"""
SBRS 2.0 — Continuous Live Engine

Persistent process that:
1. Streams real-time prices from OANDA for all configured instruments
2. Detects hourly candle closes automatically (no cron needed)
3. Runs SBRS 2.0 analysis on each candle close
4. Manages open positions with real-time awareness
5. Enforces portfolio-level risk across all symbols
6. Uses the SAME analyze_sbrs_v2() function as backtests (strategy/live parity)

Run: py -m src.live.engine_live
Stop: Ctrl+C (graceful shutdown saves all state)

Architecture:
  - Main loop checks for candle close every 30 seconds
  - On candle close for any symbol, runs the full analysis pipeline
  - Heartbeat Telegram message every 4 hours
  - Portfolio risk checked before every entry
"""

import sys
import time
import signal
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.fetcher import fetch
from src.regimes.sbrs_v2 import (
    analyze_sbrs_v2, get_sbrs_v2_indicators,
    WMA_PERIOD, SMMA_PERIOD, ATR_PERIOD, SWING_WINDOW,
    BE_TRIGGER_R, BE_BUFFER_R, MAX_HOLD_BARS,
    causal_4h_trend_series,
)
from src.indicators.technical import atr, wma, smma, detect_swing_high, detect_swing_low
from src.live.state import (
    load_state, save_state, reset_daily_if_needed,
    LiveTrade, AlgoState, add_open_trade, close_trade, generate_trade_id
)
from src.live.oanda_executor import (
    get_current_price, place_market_order, modify_stop_loss,
    close_trade as broker_close_trade,
    sync_positions, is_connected, get_account_balance
)
from src.live.portfolio_risk import can_open_position, get_portfolio_summary
from src.live import alerts
from src.live.process_lock import acquire_live_lock

HISTORY_BARS = 300
POLL_INTERVAL_SECONDS = 30    # Check for candle close every 30s
HEARTBEAT_HOURS = 4           # Send Telegram heartbeat every N hours

SYMBOLS_CONFIG = [
    {
        'symbol': 'GC=F',
        'instrument': 'XAU_USD',
        'asset_class': 'gold',
        'state_key': 'GCF',
        'risk_pct': 0.005,
        'source': 'oanda',
    },
    {
        'symbol': '^GDAXI',
        'instrument': 'DE30_EUR',
        'asset_class': 'indices',
        'state_key': 'GDAXI',
        'risk_pct': 0.0025,
        'source': 'oanda',
    },
    {
        'symbol': '^IXIC',
        'instrument': 'NAS100_USD',
        'asset_class': 'indices',
        'state_key': 'IXIC',
        'risk_pct': 0.0025,
        'source': 'oanda',
    },
    {
        'symbol': 'GBPUSD=X',
        'instrument': 'GBP_USD',
        'asset_class': 'forex',
        'state_key': 'GBPUSD',
        'risk_pct': 0.0025,
        'source': 'oanda',
    },
]


class LiveEngine:
    """Continuous SBRS 2.0 execution engine."""

    def __init__(self):
        self.running = False
        self.last_processed_bar: Dict[str, str] = {}
        self.last_heartbeat: Optional[datetime] = None
        self.cycle_count = 0

    def _should_process(self, config: dict) -> bool:
        """Check if a new candle has closed for this symbol since last processing."""
        symbol = config['symbol']
        try:
            df = fetch(symbol, '1h', '3mo')
            if len(df) < 50:
                return False

            last_bar = str(df.index[-1])
            prev = self.last_processed_bar.get(symbol, '')

            if last_bar != prev:
                return True
            return False
        except Exception:
            return False

    def _process_symbol(self, config: dict) -> Optional[dict]:
        """Run the full SBRS 2.0 pipeline for a single symbol. Strategy/live parity."""
        symbol = config['symbol']
        asset_class = config['asset_class']
        state_key = config['state_key']
        risk_pct = config['risk_pct']
        tag = alerts._sym_tag(symbol)

        state = load_state(state_key)
        state.symbol = symbol
        state.instrument = config['instrument']
        state.asset_class = asset_class
        reset_daily_if_needed(state)

        broker_balance = get_account_balance()
        if broker_balance is not None:
            state.current_capital = broker_balance
            if broker_balance > state.peak_equity:
                state.peak_equity = broker_balance

        # Sync broker positions
        if state.open_trades:
            closed_on_broker = sync_positions(state.open_trades)
            for closed_t in closed_on_broker:
                oanda_id = closed_t['oanda_trade_id']
                exit_price = closed_t.get('_broker_exit_price', 0.0)
                pnl = closed_t.get('_broker_pnl', 0.0)
                broker_reason = closed_t.get('_broker_close_reason', 'unknown')
                reason_map = {'take_profit': 'tp', 'stop_loss': 'sl', 'trailing_stop': 'trailing_sl'}
                reason = reason_map.get(broker_reason, 'broker_closed')
                result = close_trade(state, oanda_id, exit_price, reason, pnl)
                if result:
                    alerts.log_trade_exit(
                        symbol, closed_t['direction'], closed_t['entry_price'],
                        exit_price, pnl, f"{broker_reason} (detected)", oanda_id
                    )

        # Fetch data
        try:
            df = fetch(symbol, '1h', '6mo')
            if len(df) > HISTORY_BARS:
                df = df.iloc[-HISTORY_BARS:]
        except Exception as e:
            alerts.log_error(f"Data fetch failed: {e}", symbol)
            save_state(state, state_key)
            return None

        if len(df) < 50:
            save_state(state, state_key)
            return None

        bar_time = str(df.index[-1])
        self.last_processed_bar[symbol] = bar_time
        state.last_bar_time = bar_time
        state.bars_processed += 1

        i = len(df) - 1
        current_close = df['Close'].iloc[i]
        atr_vals = atr(df, ATR_PERIOD)
        current_atr = atr_vals.iloc[i]

        if np.isnan(current_atr) or current_atr <= 0:
            save_state(state, state_key)
            return None

        current_trend = causal_4h_trend_series(df).iloc[-1]

        alerts.log_bar_processed(symbol, bar_time, current_close, current_trend)

        # STRATEGY/LIVE PARITY: Use the exact same function as backtest
        new_setups = analyze_sbrs_v2(
            df, state.current_capital, risk_pct,
            asset_class=asset_class, symbol=symbol
        )
        latest_setups = [s for s in new_setups if s.index == i]
        latest_setups.sort(key=lambda s: getattr(s, 'confluence_score', 0), reverse=True)

        # Execute best setup (1 per symbol per candle)
        filled = False
        for setup in latest_setups:
            if filled:
                break

            direction = setup.direction.value if hasattr(setup.direction, 'value') else str(setup.direction)

            if state.daily_pnl < -(state.daily_start_capital * 0.05):
                alerts.log_trade_blocked(symbol, direction, "daily_loss_limit")
                continue

            dd = (state.peak_equity - state.current_capital) / state.peak_equity if state.peak_equity > 0 else 0
            dd_limit = 0.10 if asset_class == 'gold' else 0.20
            if dd >= dd_limit:
                alerts.log_trade_blocked(symbol, direction, "drawdown_breaker")
                continue

            risk_dollars = abs(setup.entry_price - setup.stop_loss) * setup.position_size
            allowed, block_reason = can_open_position(
                config['instrument'], symbol, direction, risk_dollars, state.current_capital
            )
            if not allowed:
                alerts.log_trade_blocked(symbol, direction, block_reason)
                continue

            oanda_trade_id = place_market_order(
                direction, setup.position_size, setup.stop_loss,
                setup.take_profit, instrument=config['instrument']
            )

            if oanda_trade_id:
                trade = LiveTrade(
                    trade_id=generate_trade_id(),
                    oanda_trade_id=oanda_trade_id,
                    direction=direction,
                    entry_price=setup.entry_price,
                    stop_loss=setup.stop_loss,
                    take_profit=setup.take_profit,
                    original_sl=setup.stop_loss,
                    position_size=setup.position_size,
                    entry_time=bar_time,
                    entry_bar_index=state.bars_processed,
                    regime=setup.regime,
                    status='open',
                    symbol=symbol,
                    asset_class=asset_class,
                    confluence_score=setup.confluence_score,
                    is_counter_trend=setup.is_counter_trend,
                )
                add_open_trade(state, trade)
                filled = True
                alerts.log_trade_entry(
                    symbol, direction, setup.entry_price, setup.stop_loss,
                    setup.take_profit, setup.position_size, oanda_trade_id,
                    setup.confluence_score
                )

        # Manage open trades
        indicators = get_sbrs_v2_indicators(df)
        wma_1h = indicators['wma_1h']
        smma_1h = indicators['smma_1h']
        swing_high_mask = indicators['swing_high_mask']
        swing_low_mask = indicators['swing_low_mask']

        for trade_dict in state.open_trades[:]:
            oanda_id = trade_dict['oanda_trade_id']
            direction = trade_dict['direction']
            entry_price = trade_dict['entry_price']
            original_sl = trade_dict['original_sl']
            initial_risk = abs(entry_price - original_sl)
            if initial_risk <= 0:
                continue

            trade_dict['bars_held'] = state.bars_processed - trade_dict['entry_bar_index']
            is_long = direction == 'long'
            is_indices_trade = trade_dict.get('asset_class', '') == 'indices'

            profit = (current_close - entry_price) if is_long else (entry_price - current_close)
            current_r = profit / initial_risk

            be_trigger = 1.0 if is_indices_trade else BE_TRIGGER_R
            max_hold = 25 if is_indices_trade else MAX_HOLD_BARS

            # Breakeven
            if not trade_dict['stop_moved_to_be']:
                bar_profit = (df['High'].iloc[i] - entry_price) if is_long else (entry_price - df['Low'].iloc[i])
                if bar_profit >= be_trigger * initial_risk:
                    be_buffer = BE_BUFFER_R * initial_risk
                    price_data = get_current_price(instrument=config['instrument'])
                    spread_buffer = 0.0
                    if price_data:
                        bid, ask, mid = price_data
                        spread_buffer = (ask - bid) * 0.6
                    new_sl = (entry_price + be_buffer + spread_buffer) if is_long else (entry_price - be_buffer - spread_buffer)
                    if modify_stop_loss(oanda_id, new_sl, instrument=config['instrument']):
                        old_sl = trade_dict['stop_loss']
                        trade_dict['stop_loss'] = new_sl
                        trade_dict['stop_moved_to_be'] = True
                        alerts.log_sl_moved(symbol, direction, old_sl, new_sl, 'breakeven', oanda_id)

            # MA Cross exit
            if i >= 1:
                w_c, s_c = wma_1h.iloc[i], smma_1h.iloc[i]
                w_p, s_p = wma_1h.iloc[i-1], smma_1h.iloc[i-1]
                if not (np.isnan(w_c) or np.isnan(s_c) or np.isnan(w_p) or np.isnan(s_p)):
                    ma_exit = (is_long and w_c < s_c and w_p >= s_p) or (not is_long and w_c > s_c and w_p <= s_p)
                    if ma_exit:
                        result = broker_close_trade(oanda_id)
                        if result:
                            pnl = result.get('pnl', profit * trade_dict['position_size'])
                            close_trade(state, oanda_id, result.get('price', current_close), 'ma_cross', pnl)
                            alerts.log_trade_exit(symbol, direction, entry_price,
                                                  result.get('price', current_close), pnl, 'MA Cross', oanda_id)
                        continue

            # Timeout
            if trade_dict['bars_held'] >= max_hold:
                result = broker_close_trade(oanda_id)
                if result:
                    pnl = result.get('pnl', profit * trade_dict['position_size'])
                    close_trade(state, oanda_id, result.get('price', current_close), 'timeout', pnl)
                    alerts.log_trade_exit(symbol, direction, entry_price,
                                          result.get('price', current_close), pnl, 'Timeout', oanda_id)
                continue

            # Trailing stop
            trail_trigger = 2.0 if is_indices_trade else 3.0
            if trade_dict.get('is_counter_trend', False):
                trail_trigger = 1.5

            if current_r >= trail_trigger and trade_dict['stop_moved_to_be']:
                search_end = i - 3
                search_start = max(0, i - 20)
                current_sl = trade_dict['stop_loss']
                inst = config['instrument']

                if is_long:
                    for j in range(search_end, search_start - 1, -1):
                        if j >= 0 and swing_low_mask.iloc[j]:
                            trail = df['Low'].iloc[j]
                            if trail > current_sl and trail < current_close:
                                if modify_stop_loss(oanda_id, trail, instrument=inst):
                                    alerts.log_sl_moved(symbol, direction, current_sl, trail, 'trailing', oanda_id)
                                    trade_dict['stop_loss'] = trail
                            break
                else:
                    for j in range(search_end, search_start - 1, -1):
                        if j >= 0 and swing_high_mask.iloc[j]:
                            trail = df['High'].iloc[j]
                            if trail < current_sl and trail > current_close:
                                if modify_stop_loss(oanda_id, trail, instrument=inst):
                                    alerts.log_sl_moved(symbol, direction, current_sl, trail, 'trailing', oanda_id)
                                    trade_dict['stop_loss'] = trail
                            break

        save_state(state, state_key)
        return {
            'symbol': symbol,
            'capital': state.current_capital,
            'daily_pnl': state.daily_pnl,
            'open_trades': len(state.open_trades),
        }

    def _send_heartbeat(self):
        """Send periodic Telegram heartbeat."""
        now = datetime.now(timezone.utc)
        if self.last_heartbeat and (now - self.last_heartbeat).total_seconds() < HEARTBEAT_HOURS * 3600:
            return

        summaries = []
        for config in SYMBOLS_CONFIG:
            state = load_state(config['state_key'])
            tag = alerts._sym_tag(config['symbol'])
            open_count = len(state.open_trades)
            summaries.append(f"{tag}: {open_count} open")

        portfolio = get_portfolio_summary()
        status = " | ".join(summaries)

        if alerts._tg_ok():
            alerts.send_telegram(
                f"🔄 <b>SBRS 2.0 Heartbeat</b>\n"
                f"{status}\n"
                f"Cycle: #{self.cycle_count} | {now.strftime('%H:%M UTC')}\n"
                f"{portfolio}"
            )

        self.last_heartbeat = now

    def run(self):
        """Main continuous loop."""
        acquire_live_lock()
        self.running = True

        def _shutdown(signum, frame):
            alerts.logger.info("Shutdown signal received, saving state...")
            self.running = False

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        alerts.logger.info("=" * 60)
        alerts.logger.info("SBRS 2.0 Continuous Engine STARTED")
        alerts.logger.info(f"Symbols: {[c['symbol'] for c in SYMBOLS_CONFIG]}")
        alerts.logger.info(f"Poll interval: {POLL_INTERVAL_SECONDS}s | Heartbeat: every {HEARTBEAT_HOURS}h")
        alerts.logger.info("=" * 60)

        if not is_connected():
            alerts.log_error("Cannot connect to OANDA API at startup")
            return

        if alerts._tg_ok():
            alerts.send_telegram(
                f"⚡ <b>SBRS 2.0 Engine ONLINE</b>\n"
                f"Symbols: {', '.join(alerts._sym_tag(c['symbol']) for c in SYMBOLS_CONFIG)}\n"
                f"Mode: Continuous (polling every {POLL_INTERVAL_SECONDS}s)\n"
                f"Portfolio risk: Active"
            )

        while self.running:
            try:
                self.cycle_count += 1

                for config in SYMBOLS_CONFIG:
                    if not self.running:
                        break

                    if self._should_process(config):
                        tag = alerts._sym_tag(config['symbol'])
                        alerts.logger.info(f"[{tag}] New candle detected — processing...")
                        try:
                            self._process_symbol(config)
                        except Exception as e:
                            alerts.log_error(f"Processing failed: {e}", config['symbol'])
                            alerts.logger.error(traceback.format_exc())

                # Daily summary at 16:30 GMT
                now = datetime.now(timezone.utc)
                if now.hour == 16 and now.minute >= 30 and now.minute < 31:
                    summaries = []
                    for config in SYMBOLS_CONFIG:
                        state = load_state(config['state_key'])
                        summaries.append({
                            'symbol': config['symbol'],
                            'capital': state.current_capital,
                            'daily_pnl': state.daily_pnl,
                            'open_trades': len(state.open_trades),
                        })
                    alerts.log_daily_summary(summaries)

                self._send_heartbeat()

                time.sleep(POLL_INTERVAL_SECONDS)

            except Exception as e:
                alerts.log_error(f"Engine loop error: {e}")
                alerts.logger.error(traceback.format_exc())
                time.sleep(60)

        # Graceful shutdown
        alerts.logger.info("Engine shutting down gracefully...")
        for config in SYMBOLS_CONFIG:
            state = load_state(config['state_key'])
            save_state(state, config['state_key'])
        alerts.logger.info("All state saved. Engine stopped.")

        if alerts._tg_ok():
            alerts.send_telegram("🔴 <b>SBRS 2.0 Engine OFFLINE</b>\nGraceful shutdown complete.")


def main():
    engine = LiveEngine()
    engine.run()


if __name__ == '__main__':
    main()
