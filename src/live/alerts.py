"""
SBRS 1.1 — Alerts & Logging

Sends notifications via Telegram and logs to file.

Setup:
1. Create a Telegram bot via @BotFather → get the API token
2. Get your chat ID by messaging @userinfobot
3. Add to .env:
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
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

# Setup file logging
LOG_DIR = Path(__file__).resolve().parent.parent.parent / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"sbrs_{datetime.utcnow().strftime('%Y%m')}.log"

logger = logging.getLogger('sbrs_live')
logger.setLevel(logging.INFO)

# File handler — persistent log
fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', 
                                   datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(fh)

# Console handler — when running manually
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('  %(asctime)s %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(ch)


def send_telegram(message: str) -> bool:
    """Send a message via Telegram bot. Returns True if sent successfully."""
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


def _is_telegram_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)


# ── High-Level Alert Functions ────────────────────────────────

def log_startup(capital: float, open_trades: int, pending: int):
    """Log when the runner starts."""
    msg = f"SBRS Runner started | Capital: ${capital:,.2f} | Open: {open_trades} | Pending: {pending}"
    logger.info(msg)
    if _is_telegram_configured():
        send_telegram(f"🟢 <b>SBRS Started</b>\nCapital: ${capital:,.2f}\nOpen trades: {open_trades}\nPending setups: {pending}")


def log_bar_processed(bar_time: str, close_price: float, trend: str):
    """Log each bar processed."""
    logger.info(f"Bar {bar_time} | Close: {close_price:.2f} | 4H Trend: {trend}")


def log_structure_break(direction: str, level: float, bar_time: str):
    """Log when a structure break is detected."""
    emoji = "📈" if direction == 'long' else "📉"
    msg = f"Structure break {direction.upper()} | Level: {level:.2f} | {bar_time}"
    logger.info(msg)
    if _is_telegram_configured():
        send_telegram(f"{emoji} <b>Structure Break</b>\nDirection: {direction.upper()}\nLevel: {level:.2f}\nTime: {bar_time}")


def log_trade_entry(direction: str, entry: float, sl: float, tp: float, 
                     size: float, oanda_id: str):
    """Log when a trade is entered."""
    sl_dist = abs(entry - sl)
    rr = abs(tp - entry) / sl_dist if sl_dist > 0 else 0
    emoji = "🟢" if direction == 'long' else "🔴"
    
    msg = f"ENTRY {direction.upper()} | Price: {entry:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | R:R {rr:.1f} | Size: {size:.2f} | OANDA #{oanda_id}"
    logger.info(msg)
    
    if _is_telegram_configured():
        send_telegram(
            f"{emoji} <b>TRADE ENTRY</b>\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry:.2f}\n"
            f"Stop Loss: {sl:.2f}\n"
            f"Take Profit: {tp:.2f}\n"
            f"R:R: {rr:.1f}\n"
            f"Size: {size:.2f} units\n"
            f"OANDA: #{oanda_id}"
        )


def log_trade_exit(direction: str, entry: float, exit_price: float, 
                    pnl: float, reason: str, oanda_id: str):
    """Log when a trade is closed."""
    emoji = "✅" if pnl > 0 else "❌"
    
    msg = f"EXIT {direction.upper()} | Entry: {entry:.2f} | Exit: {exit_price:.2f} | PnL: ${pnl:,.2f} | Reason: {reason} | OANDA #{oanda_id}"
    logger.info(msg)
    
    if _is_telegram_configured():
        send_telegram(
            f"{emoji} <b>TRADE EXIT</b>\n"
            f"Direction: {direction.upper()}\n"
            f"Entry: {entry:.2f} → Exit: {exit_price:.2f}\n"
            f"PnL: ${pnl:,.2f}\n"
            f"Reason: {reason}\n"
            f"OANDA: #{oanda_id}"
        )


def log_sl_moved(direction: str, old_sl: float, new_sl: float, reason: str, oanda_id: str):
    """Log when stop loss is modified (breakeven, trailing)."""
    msg = f"SL MOVED | {old_sl:.2f} → {new_sl:.2f} | Reason: {reason} | OANDA #{oanda_id}"
    logger.info(msg)
    
    if _is_telegram_configured():
        send_telegram(
            f"🔧 <b>SL Modified</b>\n"
            f"Old SL: {old_sl:.2f}\n"
            f"New SL: {new_sl:.2f}\n"
            f"Reason: {reason}"
        )


def log_trade_blocked(direction: str, reason: str):
    """Log when risk manager blocks a trade."""
    logger.info(f"BLOCKED {direction.upper()} | Reason: {reason}")


def log_no_signal(bar_time: str):
    """Log when no signal is generated (debug level)."""
    logger.debug(f"No signal at {bar_time}")


def log_error(message: str):
    """Log an error."""
    logger.error(message)
    if _is_telegram_configured():
        send_telegram(f"⚠️ <b>SBRS ERROR</b>\n{message}")


def log_daily_summary(capital: float, daily_pnl: float, open_trades: int,
                       total_trades: int, win_rate: float):
    """Send daily summary (call at end of trading day)."""
    msg = (f"DAILY SUMMARY | Capital: ${capital:,.2f} | "
           f"Day PnL: ${daily_pnl:,.2f} | Open: {open_trades} | "
           f"Total: {total_trades} | WR: {win_rate:.1f}%")
    logger.info(msg)
    
    if _is_telegram_configured():
        emoji = "📊"
        send_telegram(
            f"{emoji} <b>SBRS Daily Summary</b>\n"
            f"Capital: ${capital:,.2f}\n"
            f"Today's PnL: ${daily_pnl:,.2f}\n"
            f"Open trades: {open_trades}\n"
            f"Total trades: {total_trades}\n"
            f"Win rate: {win_rate:.1f}%"
        )
