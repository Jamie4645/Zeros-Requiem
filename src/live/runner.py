"""
SBRS 1.1 — Live Runner (Gold 1H)

Called every hour by Task Scheduler (or manually).
Each run:
  1. Load state from disk
  2. Sync with broker (check if SL/TP hit between runs)
  3. Fetch latest 1H data from OANDA
  4. Run SBRS entry logic on current bar
  5. Manage open trades (breakeven, MA cross exit, etc.)
  6. Execute any orders via OANDA API
  7. Save state to disk
  8. Send alerts

Run: py -m src.live.runner
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.oanda_fetcher import fetch_oanda, is_oanda_available
from src.indicators.technical import (
    atr, wma, smma,
    detect_swing_high, detect_swing_low,
    get_recent_swing_high, get_recent_swing_low
)
from src.regimes.sbrs_gold import (
    resample_to_4h, compute_4h_context, map_4h_to_1h,
    check_ma_cross, is_choppy, is_session_blocked, check_trend_alignment,
    WMA_PERIOD, SMMA_PERIOD, ATR_PERIOD, SWING_LOOKBACK, SWING_WINDOW,
    MIN_RR, RETEST_TOLERANCE_ATR, RETEST_TOLERANCE_ATR_SHORT,
    MAX_RETEST_WAIT, SL_BUFFER_ATR, MA_CROSS_LOOKBACK,
    TREND_CROSS_LOOKBACK, CHOP_ATR_THRESHOLD, CHOP_LOOKBACK,
    BE_TRIGGER_R, BE_BUFFER_R, MAX_HOLD_BARS
)
from src.live.state import (
    load_state, save_state, reset_daily_if_needed,
    LivePendingSetup, LiveTrade, AlgoState,
    add_pending_setup, remove_pending_setup,
    add_open_trade, close_trade, generate_trade_id
)
from src.live.oanda_executor import (
    get_current_price, place_market_order, modify_stop_loss,
    close_trade as broker_close_trade, get_open_trades,
    sync_positions, is_connected, get_account_balance
)
from src.live import alerts

# How many bars of history to fetch for indicator computation
HISTORY_BARS = 300  # ~12.5 days of 1H data, enough for all indicators
RISK_PCT = 0.01     # 1% risk per trade


def run():
    """Main execution — called once per hour."""
    
    now = datetime.now(timezone.utc)
    alerts.logger.info(f"{'='*60}")
    alerts.logger.info(f"SBRS Runner triggered at {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    # ──────────────────────────────────────────────────────────
    # Step 0: Pre-checks
    # ──────────────────────────────────────────────────────────
    if not is_oanda_available():
        alerts.log_error("OANDA credentials not configured. Check .env file.")
        return
    
    if not is_connected():
        alerts.log_error("Cannot connect to OANDA API. Check internet/API status.")
        return
    
    # ──────────────────────────────────────────────────────────
    # Step 1: Load state
    # ──────────────────────────────────────────────────────────
    state = load_state()
    new_day = reset_daily_if_needed(state)
    
    # Sync capital with broker
    broker_balance = get_account_balance()
    if broker_balance is not None:
        state.current_capital = broker_balance
        if broker_balance > state.peak_equity:
            state.peak_equity = broker_balance
    
    alerts.log_startup(state.current_capital, len(state.open_trades), len(state.pending_setups))
    
    if new_day:
        alerts.logger.info("New trading day — daily P&L reset")
    
    # ──────────────────────────────────────────────────────────
    # Step 2: Sync with broker (detect SL/TP hits between runs)
    # ──────────────────────────────────────────────────────────
    if state.open_trades:
        closed_on_broker = sync_positions(state.open_trades)
        for closed_t in closed_on_broker:
            oanda_id = closed_t['oanda_trade_id']
            # Trade was closed by broker (SL or TP hit)
            # We don't know the exact exit price/PnL — get from broker history
            # For now, mark as closed and log
            pnl = 0.0  # Broker already applied the P&L to balance
            reason = 'broker_closed'  # TP or SL hit between runs
            
            result = close_trade(state, oanda_id, closed_t.get('entry_price', 0), 
                                 reason, pnl)
            if result:
                alerts.log_trade_exit(
                    closed_t['direction'], closed_t['entry_price'],
                    0.0, pnl, 'SL/TP hit between runs', oanda_id
                )
    
    # ──────────────────────────────────────────────────────────
    # Step 3: Fetch latest data
    # ──────────────────────────────────────────────────────────
    alerts.logger.info(f"Fetching latest {HISTORY_BARS} bars of Gold 1H data...")
    
    try:
        df = fetch_oanda('GC=F', '1h', '6mo')  # Fetch 6 months, we'll use last 300 bars
        if len(df) > HISTORY_BARS:
            df = df.iloc[-HISTORY_BARS:]
        alerts.logger.info(f"Loaded {len(df)} candles: {df.index[-1]}")
    except Exception as e:
        alerts.log_error(f"Failed to fetch data: {e}")
        save_state(state)
        return
    
    if len(df) < 50:
        alerts.log_error(f"Not enough data: {len(df)} bars")
        save_state(state)
        return
    
    # ──────────────────────────────────────────────────────────
    # Step 4: Compute indicators
    # ──────────────────────────────────────────────────────────
    
    # 4H context
    df_4h = resample_to_4h(df)
    if len(df_4h) < WMA_PERIOD + SMMA_PERIOD:
        alerts.logger.info("Not enough 4H bars for indicators, skipping")
        save_state(state)
        return
    
    df_4h = compute_4h_context(df_4h)
    trend_context = map_4h_to_1h(df, df_4h)
    
    # 1H indicators
    wma_1h = wma(df['Close'], WMA_PERIOD)
    smma_1h = smma(df['Close'], SMMA_PERIOD)
    atr_vals = atr(df, ATR_PERIOD)
    swing_high_mask = detect_swing_high(df['High'], left=SWING_WINDOW, right=SWING_WINDOW)
    swing_low_mask = detect_swing_low(df['Low'], left=SWING_WINDOW, right=SWING_WINDOW)
    
    # 4H MA for cross checking
    wma_4h = wma(df_4h['Close'], WMA_PERIOD) if len(df_4h) >= WMA_PERIOD else None
    smma_4h = smma(df_4h['Close'], SMMA_PERIOD) if len(df_4h) >= SMMA_PERIOD else None
    
    # Current bar (last complete candle)
    i = len(df) - 1
    current_close = df['Close'].iloc[i]
    current_high = df['High'].iloc[i]
    current_low = df['Low'].iloc[i]
    current_atr = atr_vals.iloc[i]
    current_trend = trend_context.iloc[i]
    bar_time = str(df.index[i])
    
    if np.isnan(current_atr) or current_atr <= 0:
        alerts.logger.info(f"ATR is NaN at bar {bar_time}, skipping")
        save_state(state)
        return
    
    alerts.log_bar_processed(bar_time, current_close, current_trend)
    state.last_bar_time = bar_time
    state.bars_processed += 1
    
    # ──────────────────────────────────────────────────────────
    # Step 5: Check for structure breaks (new pending setups)
    # ──────────────────────────────────────────────────────────
    
    if current_trend == 'bullish':
        swing_result = get_recent_swing_high(df['High'], swing_high_mask, i, SWING_LOOKBACK)
        if swing_result is not None:
            sh_idx, sh_level = swing_result
            if current_close > sh_level:
                # Check not already pending
                already = any(
                    abs(p['broken_level'] - sh_level) < current_atr * 0.1
                    for p in state.pending_setups
                )
                if not already:
                    setup = LivePendingSetup(
                        direction='long',
                        broken_level=sh_level,
                        break_bar_time=bar_time,
                        bars_waiting=0,
                        created_at=bar_time
                    )
                    add_pending_setup(state, setup)
                    alerts.log_structure_break('long', sh_level, bar_time)
    
    if current_trend == 'bearish':
        swing_result = get_recent_swing_low(df['Low'], swing_low_mask, i, SWING_LOOKBACK)
        if swing_result is not None:
            sl_idx, sl_level = swing_result
            if current_close < sl_level:
                already = any(
                    abs(p['broken_level'] - sl_level) < current_atr * 0.1
                    for p in state.pending_setups
                )
                if not already:
                    setup = LivePendingSetup(
                        direction='short',
                        broken_level=sl_level,
                        break_bar_time=bar_time,
                        bars_waiting=0,
                        created_at=bar_time
                    )
                    add_pending_setup(state, setup)
                    alerts.log_structure_break('short', sl_level, bar_time)
    
    # ──────────────────────────────────────────────────────────
    # Step 6: Check pending setups for retest confirmation
    # ──────────────────────────────────────────────────────────
    
    expired_indices = []
    
    for idx, pending in enumerate(state.pending_setups):
        # Skip if just created this bar
        if pending['break_bar_time'] == bar_time:
            continue
        
        pending['bars_waiting'] += 1
        
        # Timeout
        if pending['bars_waiting'] > MAX_RETEST_WAIT:
            expired_indices.append(idx)
            continue
        
        direction = pending['direction']
        broken_level = pending['broken_level']
        
        # Determine tolerance
        if direction == 'long':
            tolerance = RETEST_TOLERANCE_ATR
        else:
            tolerance = RETEST_TOLERANCE_ATR_SHORT
        
        # Retest check
        retest_confirmed = False
        retest_extreme = 0.0
        
        if direction == 'long':
            distance = current_low - broken_level
            if distance <= tolerance * current_atr:
                if current_close > current_low:
                    retest_confirmed = True
                    retest_extreme = current_low
        else:
            distance = broken_level - current_high
            if distance <= tolerance * current_atr:
                if current_close < current_high:
                    retest_confirmed = True
                    retest_extreme = current_high
        
        if not retest_confirmed:
            continue
        
        # Re-check trend alignment
        if not check_trend_alignment(current_trend, direction):
            continue
        
        # MA cross confirmation
        ma_cross_1h = check_ma_cross(wma_1h, smma_1h, i, direction, MA_CROSS_LOOKBACK)
        
        ma_cross_4h = False
        if wma_4h is not None and smma_4h is not None:
            mask_4h = df_4h.index <= df.index[i]
            if mask_4h.any():
                idx_4h = mask_4h.sum() - 1
                if idx_4h > 0:
                    ma_cross_4h = check_ma_cross(wma_4h, smma_4h, idx_4h, direction, TREND_CROSS_LOOKBACK)
        
        # Shorts need 4H cross
        if direction == 'long':
            if not (ma_cross_1h or ma_cross_4h):
                continue
        else:
            if not ma_cross_4h:
                continue
        
        # Session filter
        try:
            if is_session_blocked(df.index[i]):
                continue
        except:
            pass
        
        # Chop filter
        if is_choppy(df, i, atr_vals, CHOP_LOOKBACK, CHOP_ATR_THRESHOLD):
            continue
        
        # Calculate SL, TP
        if direction == 'long':
            stop_loss = retest_extreme - (SL_BUFFER_ATR * current_atr)
            sl_distance = current_close - stop_loss
            take_profit = current_close + (MIN_RR * sl_distance)
        else:
            stop_loss = retest_extreme + (SL_BUFFER_ATR * current_atr)
            sl_distance = stop_loss - current_close
            take_profit = current_close - (MIN_RR * sl_distance)
        
        if sl_distance <= 0:
            continue
        
        rr = abs(take_profit - current_close) / sl_distance
        if rr < MIN_RR:
            continue
        
        # Position sizing from current capital
        position_size = (state.current_capital * RISK_PCT) / sl_distance
        if position_size <= 0:
            continue
        
        # Risk checks
        # Daily loss limit (3%)
        if state.daily_pnl < -(state.daily_start_capital * 0.03):
            alerts.log_trade_blocked(direction, "daily_loss_limit")
            continue
        
        # Drawdown breaker (10%)
        dd = (state.peak_equity - state.current_capital) / state.peak_equity if state.peak_equity > 0 else 0
        if dd >= 0.10:
            alerts.log_trade_blocked(direction, "drawdown_breaker")
            continue
        
        # Max concurrent trades (4)
        if len(state.open_trades) >= 4:
            alerts.log_trade_blocked(direction, "max_concurrent")
            continue
        
        # ──────────────────────────────────────────────────────
        # ENTRY — Place order via OANDA
        # ──────────────────────────────────────────────────────
        alerts.logger.info(f"SIGNAL: {direction.upper()} @ {current_close:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f} | Size: {position_size:.0f}")
        
        oanda_trade_id = place_market_order(direction, position_size, stop_loss, take_profit)
        
        if oanda_trade_id:
            trade = LiveTrade(
                trade_id=generate_trade_id(),
                oanda_trade_id=oanda_trade_id,
                direction=direction,
                entry_price=current_close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                original_sl=stop_loss,
                position_size=position_size,
                entry_time=bar_time,
                entry_bar_index=state.bars_processed,
                regime='sbrs_gold',
                status='open'
            )
            add_open_trade(state, trade)
            alerts.log_trade_entry(direction, current_close, stop_loss, take_profit,
                                    position_size, oanda_trade_id)
        else:
            alerts.log_error(f"Order FAILED for {direction.upper()} @ {current_close:.2f}")
        
        expired_indices.append(idx)
    
    # Clean up expired/used setups
    for idx in sorted(set(expired_indices), reverse=True):
        remove_pending_setup(state, idx)
    
    # ──────────────────────────────────────────────────────────
    # Step 7: Manage open trades
    # ──────────────────────────────────────────────────────────
    
    for trade_dict in state.open_trades[:]:
        oanda_id = trade_dict['oanda_trade_id']
        direction = trade_dict['direction']
        entry_price = trade_dict['entry_price']
        original_sl = trade_dict['original_sl']
        current_sl = trade_dict['stop_loss']
        initial_risk = abs(entry_price - original_sl)
        
        if initial_risk <= 0:
            continue
        
        trade_dict['bars_held'] = state.bars_processed - trade_dict['entry_bar_index']
        is_long = direction == 'long'
        
        # Current profit in R
        profit = (current_close - entry_price) if is_long else (entry_price - current_close)
        current_r = profit / initial_risk
        
        # --- Breakeven at 1.5R ---
        if not trade_dict['stop_moved_to_be']:
            bar_profit = (current_high - entry_price) if is_long else (entry_price - current_low)
            if bar_profit >= BE_TRIGGER_R * initial_risk:
                be_buffer = BE_BUFFER_R * initial_risk
                new_sl = (entry_price + be_buffer) if is_long else (entry_price - be_buffer)
                
                if modify_stop_loss(oanda_id, new_sl):
                    old_sl = trade_dict['stop_loss']
                    trade_dict['stop_loss'] = new_sl
                    trade_dict['stop_moved_to_be'] = True
                    alerts.log_sl_moved(direction, old_sl, new_sl, 'breakeven', oanda_id)
        
        # --- MA Cross Reversal Exit ---
        if i >= 1:
            w_c = wma_1h.iloc[i]
            s_c = smma_1h.iloc[i]
            w_p = wma_1h.iloc[i-1]
            s_p = smma_1h.iloc[i-1]
            
            if not (np.isnan(w_c) or np.isnan(s_c) or np.isnan(w_p) or np.isnan(s_p)):
                ma_exit = False
                if is_long and w_c < s_c and w_p >= s_p:
                    ma_exit = True
                elif not is_long and w_c > s_c and w_p <= s_p:
                    ma_exit = True
                
                if ma_exit:
                    result = broker_close_trade(oanda_id)
                    if result:
                        pnl = result.get('pnl', profit * trade_dict['position_size'])
                        close_trade(state, oanda_id, result.get('price', current_close),
                                    'ma_cross', pnl)
                        alerts.log_trade_exit(direction, entry_price, 
                                              result.get('price', current_close),
                                              pnl, 'MA Cross Reversal', oanda_id)
                    continue
        
        # --- Timeout (40 bars) ---
        if trade_dict['bars_held'] >= MAX_HOLD_BARS:
            result = broker_close_trade(oanda_id)
            if result:
                pnl = result.get('pnl', profit * trade_dict['position_size'])
                close_trade(state, oanda_id, result.get('price', current_close),
                            'timeout', pnl)
                alerts.log_trade_exit(direction, entry_price,
                                      result.get('price', current_close),
                                      pnl, 'Max Hold Timeout', oanda_id)
            continue
        
        # --- Trailing Stop at 3R+ ---
        if current_r >= 3.0 and trade_dict['stop_moved_to_be']:
            search_end = i - 3
            search_start = max(0, i - 20)
            
            if is_long:
                for j in range(search_end, search_start - 1, -1):
                    if j >= 0 and swing_low_mask.iloc[j]:
                        trail = df['Low'].iloc[j]
                        if trail > current_sl and trail < current_close:
                            if modify_stop_loss(oanda_id, trail):
                                alerts.log_sl_moved(direction, current_sl, trail, 'trailing', oanda_id)
                                trade_dict['stop_loss'] = trail
                        break
            else:
                for j in range(search_end, search_start - 1, -1):
                    if j >= 0 and swing_high_mask.iloc[j]:
                        trail = df['High'].iloc[j]
                        if trail < current_sl and trail > current_close:
                            if modify_stop_loss(oanda_id, trail):
                                alerts.log_sl_moved(direction, current_sl, trail, 'trailing', oanda_id)
                                trade_dict['stop_loss'] = trail
                        break
    
    # ──────────────────────────────────────────────────────────
    # Step 8: Daily summary at end of session (16:30 GMT)
    # ──────────────────────────────────────────────────────────
    if now.hour == 16 and now.minute >= 30:
        wr = state.total_wins / state.total_trades * 100 if state.total_trades > 0 else 0
        alerts.log_daily_summary(
            state.current_capital, state.daily_pnl,
            len(state.open_trades), state.total_trades, wr
        )
    
    # ──────────────────────────────────────────────────────────
    # Step 9: Save state and done
    # ──────────────────────────────────────────────────────────
    save_state(state)
    alerts.logger.info(f"Run complete. Open: {len(state.open_trades)} | Pending: {len(state.pending_setups)} | Capital: ${state.current_capital:,.2f}")
    alerts.logger.info(f"{'='*60}")


if __name__ == '__main__':
    run()
