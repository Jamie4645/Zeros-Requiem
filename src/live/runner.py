"""
SBRS 2.0 — Live Runner (Multi-Symbol: Gold, DAX, NASDAQ, GBP/USD)

Called every hour by Task Scheduler (or manually).
Each run processes ALL configured symbols sequentially:
  1. Load per-symbol state from disk
  2. Sync with broker (check if SL/TP hit between runs)
  3. Fetch latest 1H data
  4. Run SBRS 2.0 entry logic (confluence scoring, ATR filter, adaptive R:R)
  5. Manage open trades (breakeven, MA cross exit, structure exit, trailing, timeout)
  6. Execute orders via OANDA API
  7. Save per-symbol state to disk
  8. Send daily summary at 16:30 GMT

Run: py -m src.live.runner
"""

import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.fetcher import fetch, detect_asset_class
from src.live.data_cache import fetch_live
from src.regimes.sbrs_v2 import (
    analyze_sbrs_v2, get_sbrs_v2_indicators,
    WMA_PERIOD, SMMA_PERIOD, ATR_PERIOD, SWING_WINDOW,
    BE_TRIGGER_R, BE_BUFFER_R, MAX_HOLD_BARS,
    causal_4h_trend_series,
)
from src.indicators.technical import (
    atr, wma, smma,
    detect_swing_high, detect_swing_low,
)
from src.live.state import (
    load_state, save_state, reset_daily_if_needed,
    LiveTrade, AlgoState,
    add_open_trade, close_trade, generate_trade_id
)
from src.live.oanda_executor import (
    get_current_price, place_market_order, modify_stop_loss,
    close_trade as broker_close_trade, get_open_trades,
    sync_positions, is_connected, get_account_balance,
    get_last_fill_price,
)
from src.live.slip_logger import log_fill as log_slip_fill
from src.live import alerts
from src.live.portfolio_risk import can_open_position, get_portfolio_summary
from src.live.process_lock import acquire_live_lock
from src.live.deploy_gate import require_live_authorization

HISTORY_BARS = 300

# ── Symbol Configuration ─────────────────────────────────────
# Per-symbol sizes mirror the Round 8 evidence-weighted canon
# (`knowledge-base/76-Round-8-Evidence-Weighted-Sizing.md`).
# SYMBOL_RISK_CAP in src/core/risk_manager.py is the authoritative clamp —
# these values are the caller-intended target. Total live: 1.10%.
# ── PAUSED 2026-06-09 — Gold-only while ZTT is built ─────────
# Per user directive (ZTT rebuild), ALL non-Gold instruments are paused
# until the new intraday-Gold "Zero's True Trade" strategy is built,
# validated, demo-tested and live. The non-Gold configs are preserved in
# _PAUSED_SYMBOLS below (and SYMBOL_RISK_CAP zeroes them as defense-in-depth)
# so multi-asset can be restored later. NOTE: the Gold entry below still
# references the legacy SBRS path/cadence — Phase 7 replaces it with ZTT 10m.
SYMBOLS_CONFIG = [
    {
        'symbol': 'GC=F',
        'instrument': 'XAU_USD',
        'asset_class': 'gold',
        'state_key': 'GCF',
        'risk_pct': 0.0100,          # 2026-06-09: 1.00% — only live instrument (ZTT freeze); reverts when others return
        'source': 'oanda',
    },
]

# Restore an entry into SYMBOLS_CONFIG (and un-zero its SYMBOL_RISK_CAP)
# to bring an instrument back online after ZTT ships.
_PAUSED_SYMBOLS = [
    {
        'symbol': '^GDAXI',
        'instrument': 'DE30_EUR',    # OANDA DAX CFD
        'asset_class': 'indices',
        'state_key': 'GDAXI',
        'risk_pct': 0.0025,
        'source': 'oanda',
    },
    {
        'symbol': '^IXIC',
        'instrument': 'NAS100_USD',  # OANDA NASDAQ CFD
        'asset_class': 'indices',
        'state_key': 'IXIC',
        'risk_pct': 0.0015,
        'source': 'oanda',
    },
    {
        'symbol': 'GBPUSD=X',
        'instrument': 'GBP_USD',
        'asset_class': 'forex',
        'state_key': 'GBPUSD',
        'risk_pct': 0.0020,
        'source': 'oanda',
    },
]


def _is_candle_closed(df: pd.DataFrame, now: datetime) -> bool:
    """
    Verify the latest bar is a COMPLETED candle, not the current in-progress one.
    The last bar's hour should be BEFORE the current hour.
    Prevents running on incomplete candle data.
    """
    if len(df) == 0:
        return False
    last_bar_hour = df.index[-1].hour
    current_hour = now.hour
    return last_bar_hour != current_hour


def _run_symbol(config: dict, now: datetime) -> dict:
    """Process a single symbol. Returns summary dict for daily report."""
    symbol = config['symbol']
    asset_class = config['asset_class']
    state_key = config['state_key']
    risk_pct = config['risk_pct']
    tag = alerts._sym_tag(symbol)

    # ── Load state ────────────────────────────────────────────
    state = load_state(state_key)
    state.symbol = symbol
    state.instrument = config['instrument']
    state.asset_class = asset_class
    new_day = reset_daily_if_needed(state)

    broker_balance = get_account_balance()
    if broker_balance is not None:
        state.current_capital = broker_balance
        if broker_balance > state.peak_equity:
            state.peak_equity = broker_balance

    alerts.log_startup(symbol, state.current_capital, len(state.open_trades), len(state.pending_setups))

    # ── Sync with broker ──────────────────────────────────────
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
                    exit_price, pnl, f"{broker_reason} (between runs)", oanda_id
                )

    # ── Fetch data ────────────────────────────────────────────
    alerts.logger.info(f"[{tag}] Fetching latest {HISTORY_BARS} bars...")
    try:
        df = fetch_live(symbol, '1h', '1mo', min_bars=HISTORY_BARS)
        if len(df) > HISTORY_BARS:
            df = df.iloc[-HISTORY_BARS:]
        alerts.logger.info(f"[{tag}] Loaded {len(df)} candles: {df.index[-1]}")
    except Exception as e:
        alerts.log_error(f"Failed to fetch data: {e}", symbol)
        save_state(state, state_key)
        return _summary(state, symbol)

    if len(df) < 50:
        alerts.log_error(f"Not enough data: {len(df)} bars", symbol)
        save_state(state, state_key)
        return _summary(state, symbol)

    # ── Candle close guard ────────────────────────────────────
    if not _is_candle_closed(df, now):
        alerts.logger.info(f"[{tag}] Current candle not yet closed, skipping this run")
        save_state(state, state_key)
        return _summary(state, symbol)

    # ── Run SBRS 2.0 analysis ─────────────────────────────────
    bar_time = str(df.index[-1])
    current_close = df['Close'].iloc[-1]
    atr_vals = atr(df, ATR_PERIOD)
    current_atr = atr_vals.iloc[-1]
    i = len(df) - 1

    if np.isnan(current_atr) or current_atr <= 0:
        alerts.logger.info(f"[{tag}] ATR is NaN, skipping")
        save_state(state, state_key)
        return _summary(state, symbol)

    # Run the full v2 strategy on the data window to find new setups
    new_setups = analyze_sbrs_v2(
        df, state.current_capital, risk_pct,
        asset_class=asset_class, symbol=symbol
    )

    # Only consider setups triggered on the LAST bar
    latest_setups = [s for s in new_setups if s.index == i]

    state.last_bar_time = bar_time
    state.bars_processed += 1

    current_trend = causal_4h_trend_series(df).iloc[-1]

    alerts.log_bar_processed(symbol, bar_time, current_close, current_trend)

    # ── Execute new setups (max 1 per symbol per run) ────────
    # Sort by confluence score descending — take the best signal only
    latest_setups.sort(key=lambda s: getattr(s, 'confluence_score', 0), reverse=True)
    filled_this_run = False

    for setup in latest_setups:
        if filled_this_run:
            break

        direction = setup.direction.value if hasattr(setup.direction, 'value') else str(setup.direction)

        # Per-symbol daily loss check
        if state.daily_pnl < -(state.daily_start_capital * 0.05):
            alerts.log_trade_blocked(symbol, direction, "daily_loss_limit")
            continue

        # Per-symbol drawdown check
        dd = (state.peak_equity - state.current_capital) / state.peak_equity if state.peak_equity > 0 else 0
        dd_limit = 0.10 if asset_class == 'gold' else 0.20
        if dd >= dd_limit:
            alerts.log_trade_blocked(symbol, direction, "drawdown_breaker")
            continue

        # Portfolio-level risk check (aggregated across ALL symbols)
        risk_dollars = abs(setup.entry_price - setup.stop_loss) * setup.position_size
        allowed, block_reason = can_open_position(
            config['instrument'], symbol, direction, risk_dollars, state.current_capital
        )
        if not allowed:
            alerts.log_trade_blocked(symbol, direction, block_reason)
            continue

        oanda_trade_id = place_market_order(direction, setup.position_size, setup.stop_loss, setup.take_profit, instrument=config['instrument'])

        # Slip reconciliation (Falsifier #1): record expected vs actual fill.
        log_slip_fill(
            symbol=symbol,
            instrument=config['instrument'],
            direction=direction,
            expected_entry=setup.entry_price,
            actual_fill=get_last_fill_price(),
            oanda_trade_id=oanda_trade_id,
            units=setup.position_size,
            asset_class=asset_class,
            note='runner',
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
            filled_this_run = True
            alerts.log_trade_entry(
                symbol, direction, setup.entry_price, setup.stop_loss,
                setup.take_profit, setup.position_size, oanda_trade_id,
                setup.confluence_score
            )
        else:
            alerts.log_error(f"Order FAILED for {direction.upper()} @ {setup.entry_price:.2f}", symbol)

    # ── Manage open trades ────────────────────────────────────
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

        # --- Breakeven ---
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

        # --- MA Cross Exit ---
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

        # --- Timeout ---
        if trade_dict['bars_held'] >= max_hold:
            result = broker_close_trade(oanda_id)
            if result:
                pnl = result.get('pnl', profit * trade_dict['position_size'])
                close_trade(state, oanda_id, result.get('price', current_close), 'timeout', pnl)
                alerts.log_trade_exit(symbol, direction, entry_price,
                                      result.get('price', current_close), pnl, 'Timeout', oanda_id)
            continue

        # --- Trailing Stop ---
        trail_trigger = 2.0 if is_indices_trade else 3.0
        if getattr(trade_dict, 'is_counter_trend', False) or trade_dict.get('is_counter_trend', False):
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
    alerts.logger.info(f"[{tag}] Done | Open: {len(state.open_trades)} | Capital: ${state.current_capital:,.2f}")
    return _summary(state, symbol)


def _summary(state: AlgoState, symbol: str) -> dict:
    return {
        'symbol': symbol,
        'capital': state.current_capital,
        'daily_pnl': state.daily_pnl,
        'open_trades': len(state.open_trades),
        'total_trades': state.total_trades,
    }


def run():
    """Main execution — called once per hour by Task Scheduler."""
    require_live_authorization('runner')
    acquire_live_lock()
    now = datetime.now(timezone.utc)
    alerts.logger.info(f"{'=' * 60}")
    alerts.logger.info(f"SBRS 2.0 Runner triggered at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    alerts.logger.info(f"Symbols: {[c['symbol'] for c in SYMBOLS_CONFIG]}")

    if not is_connected():
        alerts.log_error("Cannot connect to OANDA API. Check internet/API status.")
        return

    summaries = []
    for config in SYMBOLS_CONFIG:
        try:
            summary = _run_symbol(config, now)
            summaries.append(summary)
        except Exception as e:
            alerts.log_error(f"FATAL for {config['symbol']}: {e}", config['symbol'])
            import traceback
            alerts.logger.error(traceback.format_exc())

    # Daily summary at 16:30 GMT
    if now.hour == 16 and now.minute >= 30 and summaries:
        alerts.log_daily_summary(summaries)

    alerts.logger.info(f"{'=' * 60}")


if __name__ == '__main__':
    run()
