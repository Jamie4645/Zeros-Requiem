"""
SBRS 2.0 — Alerts & Logging (Multi-Symbol)

Sends notifications via Telegram and logs to file.
Only sends Telegram for: trade entries, trade exits, daily summary, errors.
Structure breaks and bar processing go to log file only (reduces noise).

Setup:
1. Create a Telegram bot via @BotFather
2. Get your chat ID by messaging @userinfobot
3. Add to .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""

import os
import logging
import requests
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

LOG_DIR = Path(__file__).resolve().parent.parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"sbrs_{datetime.utcnow().strftime('%Y%m')}.log"

logger = logging.getLogger('sbrs_live')
logger.setLevel(logging.INFO)

if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                       datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('  %(asctime)s %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(ch)


def send_telegram(message: str) -> bool:
    """Send a message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
        }
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def _tg_ok() -> bool:
    return bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)


def _sym_tag(symbol: str) -> str:
    """Short display tag: GC=F -> Gold, ^GDAXI -> DAX, etc."""
    tags = {
        'GC=F': 'Gold', '^GSPC': 'S&P', '^IXIC': 'NAS',
        '^GDAXI': 'DAX', 'GBPUSD=X': 'GBP/USD', 'EURUSD=X': 'EUR/USD',
        'USDJPY=X': 'USD/JPY', 'AUDUSD=X': 'AUD/USD',
        'BTC-USD': 'BTC', 'ETH-USD': 'ETH',
    }
    return tags.get(symbol, symbol)


# ── Telegram-worthy alerts (user sees these) ─────────────────

def log_trade_entry(symbol: str, direction: str, entry: float, sl: float,
                     tp: float, size: float, oanda_id: str, confluence: float = 0.0):
    """Trade entry — sent to Telegram."""
    tag = _sym_tag(symbol)
    sl_dist = abs(entry - sl)
    rr = abs(tp - entry) / sl_dist if sl_dist > 0 else 0
    emoji = "🟢" if direction == 'long' else "🔴"

    msg = (f"[{tag}] ENTRY {direction.upper()} @ {entry:.2f} | "
           f"SL: {sl:.2f} | TP: {tp:.2f} | R:R {rr:.1f} | "
           f"Score: {confluence:.1f} | OANDA #{oanda_id}")
    logger.info(msg)

    if _tg_ok():
        send_telegram(
            f"{emoji} <b>[{tag} 1H] TRADE ENTRY</b>\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry:.2f}\n"
            f"Stop Loss: {sl:.2f}\n"
            f"Take Profit: {tp:.2f}\n"
            f"R:R: {rr:.1f} | Confluence: {confluence:.1f}\n"
            f"Size: {size:.2f} units\n"
            f"OANDA: #{oanda_id}"
        )


def log_trade_exit(symbol: str, direction: str, entry: float, exit_price: float,
                    pnl: float, reason: str, oanda_id: str):
    """Trade exit — sent to Telegram."""
    tag = _sym_tag(symbol)
    emoji = "✅" if pnl > 0 else "❌"

    msg = (f"[{tag}] EXIT {direction.upper()} | Entry: {entry:.2f} | "
           f"Exit: {exit_price:.2f} | PnL: ${pnl:,.2f} | Reason: {reason}")
    logger.info(msg)

    if _tg_ok():
        send_telegram(
            f"{emoji} <b>[{tag} 1H] TRADE EXIT</b>\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry:.2f} → Exit: {exit_price:.2f}\n"
            f"PnL: ${pnl:,.2f}\n"
            f"Reason: {reason}\n"
            f"OANDA: #{oanda_id}"
        )


def log_daily_summary(symbols_data: list):
    """Daily summary across all symbols — sent to Telegram."""
    lines = []
    total_pnl = 0.0
    total_open = 0
    for sd in symbols_data:
        tag = _sym_tag(sd['symbol'])
        lines.append(f"  {tag}: ${sd['capital']:,.2f} | Day: ${sd['daily_pnl']:+,.2f} | Open: {sd['open_trades']}")
        total_pnl += sd['daily_pnl']
        total_open += sd['open_trades']

    summary = "\n".join(lines)
    logger.info(f"DAILY SUMMARY | Total PnL: ${total_pnl:+,.2f} | Open: {total_open}")

    if _tg_ok():
        send_telegram(
            f"📊 <b>SBRS 2.0 Daily Summary</b>\n"
            f"{'─' * 28}\n"
            f"{summary}\n"
            f"{'─' * 28}\n"
            f"Total Day PnL: ${total_pnl:+,.2f}\n"
            f"Open positions: {total_open}"
        )


def log_error(message: str, symbol: str = ""):
    """Error — sent to Telegram."""
    tag = f"[{_sym_tag(symbol)}] " if symbol else ""
    logger.error(f"{tag}{message}")
    if _tg_ok():
        send_telegram(f"⚠️ <b>SBRS ERROR</b>\n{tag}{message}")


# ── Log-only alerts (no Telegram noise) ──────────────────────

def log_startup(symbol: str, capital: float, open_trades: int, pending: int):
    """Log when the runner starts for a symbol."""
    tag = _sym_tag(symbol)
    logger.info(f"[{tag}] Started | Capital: ${capital:,.2f} | Open: {open_trades} | Pending: {pending}")


def log_bar_processed(symbol: str, bar_time: str, close_price: float, trend: str):
    """Log each bar processed (log only, no Telegram)."""
    tag = _sym_tag(symbol)
    logger.info(f"[{tag}] Bar {bar_time} | Close: {close_price:.2f} | Trend: {trend}")


def log_structure_break(symbol: str, direction: str, level: float, bar_time: str):
    """Log structure break (log only, no Telegram)."""
    tag = _sym_tag(symbol)
    logger.info(f"[{tag}] Structure break {direction.upper()} | Level: {level:.2f} | {bar_time}")


def log_sl_moved(symbol: str, direction: str, old_sl: float, new_sl: float,
                  reason: str, oanda_id: str):
    """SL modification — log only (too noisy for Telegram)."""
    tag = _sym_tag(symbol)
    logger.info(f"[{tag}] SL MOVED | {old_sl:.2f} → {new_sl:.2f} | Reason: {reason} | #{oanda_id}")


def log_trade_blocked(symbol: str, direction: str, reason: str):
    """Risk block — log only."""
    tag = _sym_tag(symbol)
    logger.info(f"[{tag}] BLOCKED {direction.upper()} | Reason: {reason}")
