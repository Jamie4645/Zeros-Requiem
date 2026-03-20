"""
Forex (Majors) Regime for SCAF 2.0

The Killzone Strategy:
1. Trading restricted to London (08:00-11:00 GMT) and NY (13:00-16:00 GMT) opens
2. Identify the Asian Session Range (High/Low from 00:00-08:00 GMT)
3. Wait for Liquidity Sweep: price pokes beyond Asian range (ATR-relative distance)
4. MSS is inherently confirmed by the sweep close-back (no lookahead needed)
5. Confirm Displacement Factor (Df > 1.0)
6. Enter at Fair Value Gap (FVG) midpoint

For daily data: uses simplified breakout logic with PDH/PDL sweeps.

JPY pairs (O1 optimisation): USD/JPY is driven by the Asian session — when
it breaks the Asian range, it's often a real breakout (not a trap). For JPY
pairs, we trade WITH the Asian breakout direction instead of fading it.

Priority 1.4: Df thresholds lowered (FVG: 1.5→1.0, fallback: 1.5→0.75)
Priority 1.6: EMA trend filter widened (1%→2%)
Priority 1.7: MSS lookahead removed — sweep detection already confirms close-back
P3: JPY on slow TFs (4H+): skip Asian range fades, only PDH/PDL sweeps
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from dataclasses import dataclass

from ..indicators.technical import (
    atr, ema, sma, displacement_factor,
    detect_session, get_session_range
)
from ..execution.liquidity import (
    scan_for_sweeps, detect_liquidity_sweep,
    LiquiditySweep, SweepDirection,
    get_previous_day_levels
)
from ..execution.displacement import detect_fvg, FairValueGap, FVGDirection
from ..execution.entries import validate_entry, TradeSetup


def _is_killzone(timestamp) -> bool:
    """Check if current time is within a forex killzone."""
    try:
        hour = timestamp.hour
    except AttributeError:
        return True  # Daily data -- always active
    
    # London Killzone: 08:00-11:00 GMT
    # NY Killzone: 13:00-16:00 GMT
    return (8 <= hour < 11) or (13 <= hour < 16)


def _get_asian_range(df: pd.DataFrame, current_index: int) -> tuple:
    """
    Get today's Asian session range (00:00-08:00 GMT).
    
    Returns (asian_high, asian_low). Returns (0, 0) if not found.
    """
    asian_high = 0.0
    asian_low = float('inf')
    found = False
    
    # Look backward to find Asian session bars (same day, hours 0-7)
    try:
        current_date = df.index[current_index].date()
    except AttributeError:
        # Daily data -- use previous bar as proxy for "range to break"
        if current_index >= 1:
            return (df['High'].iloc[current_index - 1], df['Low'].iloc[current_index - 1])
        return (0.0, 0.0)
    
    for i in range(current_index - 1, max(0, current_index - 30), -1):
        try:
            bar_date = df.index[i].date()
            bar_hour = df.index[i].hour
        except AttributeError:
            continue
        
        # Same day, Asia hours (0-7)
        if bar_date == current_date and 0 <= bar_hour < 8:
            asian_high = max(asian_high, df['High'].iloc[i])
            asian_low = min(asian_low, df['Low'].iloc[i])
            found = True
        
        # Previous day Asia (for early London when today's Asia just ended)
        elif bar_date < current_date and not found:
            if 0 <= bar_hour < 8:
                asian_high = max(asian_high, df['High'].iloc[i])
                asian_low = min(asian_low, df['Low'].iloc[i])
                found = True
            elif found:
                break
    
    if not found or asian_low == float('inf'):
        # Fallback: use last 8 bars as proxy for "recent range"
        lookback = min(8, current_index)
        if lookback > 0:
            window = df.iloc[current_index - lookback:current_index]
            return (window['High'].max(), window['Low'].min())
        return (0.0, 0.0)
    
    return (asian_high, asian_low)


def _detect_mss(df: pd.DataFrame, index: int, sweep: LiquiditySweep) -> bool:
    """
    Detect Market Structure Shift (MSS) after a liquidity sweep.
    
    Priority 1.7: Removed the next-bar lookahead that caused future peeking
    in backtests. MSS is now confirmed by the sweep itself -- the sweep
    detection already verifies that the candle's close is back inside the
    level, which IS the market structure shift. No lookahead needed.
    
    For a bullish sweep (swept lows): MSS confirmed when price closes above sweep level
    For a bearish sweep (swept highs): MSS confirmed when price closes below sweep level
    """
    # The sweep detection already requires the close to be back on the original
    # side of the level. That close-back IS the MSS. No additional confirmation needed.
    if sweep.direction == SweepDirection.BULLISH:
        return sweep.close_price > sweep.sweep_level
    else:
        return sweep.close_price < sweep.sweep_level


def _is_jpy_pair(symbol: str) -> bool:
    """Check if this is a JPY-denominated pair."""
    if not symbol:
        return False
    s = symbol.upper()
    return 'JPY' in s


def _detect_asian_breakout(
    df: pd.DataFrame,
    index: int,
    asian_high: float,
    asian_low: float,
    atr_val: float,
    ema_val: float,
    current_close: float
) -> Optional[TradeSetup]:
    """
    O1: For JPY pairs, detect Asian range breakouts to trade WITH the break.
    
    Unlike EUR/GBP where Asian breaks are traps, USD/JPY's Asian session
    is the primary move. When price breaks and closes beyond the Asian range,
    trade in the breakout direction.
    
    Returns a TradeSetup if breakout detected, None otherwise.
    """
    if atr_val <= 0 or asian_high <= 0 or asian_low <= 0:
        return None
    
    asian_range = asian_high - asian_low
    if asian_range <= 0:
        return None
    
    # Breakout above Asian high: LONG
    if current_close > asian_high:
        # Confirm: close must be beyond the range (not just a wick)
        break_distance = current_close - asian_high
        if break_distance > 0 and break_distance <= atr_val * 0.8:  # Not too far already
            entry = current_close
            sl = asian_low - atr_val * 0.3  # Stop below the Asian range
            tp = entry + abs(entry - sl) * 2.0  # 2R target
            
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr = reward / risk if risk > 0 else 0
            
            # EMA trend confirmation: only long if above EMA
            if rr >= 1.5 and current_close > ema_val:
                return TradeSetup(
                    direction='long',
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp,
                    position_size=0,  # Will be calculated by caller
                    risk_reward=rr,
                    regime="forex_jpy_breakout",
                    sweep=LiquiditySweep(SweepDirection.BULLISH, asian_high, asian_high, current_close, index, "asian_high_breakout"),
                    fvg=FairValueGap(FVGDirection.BULLISH, entry, entry, entry, 0, index, 0),
                    displacement_df=0,
                    index=index
                )
    
    # Breakout below Asian low: SHORT
    elif current_close < asian_low:
        break_distance = asian_low - current_close
        if break_distance > 0 and break_distance <= atr_val * 0.8:
            entry = current_close
            sl = asian_high + atr_val * 0.3  # Stop above the Asian range
            tp = entry - abs(sl - entry) * 2.0  # 2R target
            
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            rr = reward / risk if risk > 0 else 0
            
            # EMA trend confirmation: only short if below EMA
            if rr >= 1.5 and current_close < ema_val:
                return TradeSetup(
                    direction='short',
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp,
                    position_size=0,
                    risk_reward=rr,
                    regime="forex_jpy_breakout",
                    sweep=LiquiditySweep(SweepDirection.BEARISH, asian_low, asian_low, current_close, index, "asian_low_breakout"),
                    fvg=FairValueGap(FVGDirection.BEARISH, entry, entry, entry, 0, index, 0),
                    displacement_df=0,
                    index=index
                )
    
    return None


def analyze_forex(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01,
    symbol: str = ""
) -> List[TradeSetup]:
    """
    Run Forex regime analysis across all bars.
    
    The Killzone Strategy:
    1. Only trade during London (08-11) and NY (13-16) killzones
    2. Identify Asian session range
    3. Detect liquidity sweep of Asian range (EUR/GBP: fade, JPY: breakout)
    4. Confirm MSS (sweep close-back confirms structure shift)
    5. Check for Displacement Factor > 1.0 (Priority 1.4)
    6. Enter at FVG midpoint (with near-FVG tolerance)
    
    O1: JPY pairs trade WITH Asian breakouts, not against them.
    """
    setups = []
    is_jpy = _is_jpy_pair(symbol)
    
    # Pre-calculate indicators
    atr_14 = atr(df, 14)
    ema_50 = ema(df['Close'], 50)
    df_series = displacement_factor(df, 50)
    
    # Detect if daily data
    is_daily = False
    try:
        hours = [df.index[i].hour for i in range(min(20, len(df)))]
        if len(set(hours)) <= 2:
            is_daily = True
    except AttributeError:
        is_daily = True
    
    # N1: Estimate timeframe — JPY breakout only works on 1H and faster
    # where the Asian session spans 8+ bars (well-defined range).
    # On 4H the Asian range is only 2 bars — too coarse for breakouts.
    # 4H has ~6 unique hours in 30 bars, 1H has ~24. Threshold at 12.
    is_fast_tf = False
    if not is_daily:
        try:
            sample_hours = [df.index[j].hour for j in range(min(30, len(df)))]
            unique_hours = len(set(sample_hours))
            is_fast_tf = unique_hours >= 12  # Only 1H and faster
        except (AttributeError, IndexError):
            pass
    
    # JPY breakout only on fast timeframes (1H and below)
    use_jpy_breakout = is_jpy and is_fast_tf
    
    # Track pending FVGs waiting for fill
    pending_fvg_setups: List[dict] = []
    pending_sweeps: List[dict] = []  # Sweeps waiting for FVG formation (up to 3 bars)
    
    for i in range(52, len(df)):
        
        # ============================================================
        # Check pending FVG fills
        # ============================================================
        for pending in pending_fvg_setups[:]:
            fvg = pending['fvg']
            sweep = pending['sweep']
            bars_since = i - fvg.index
            
            if bars_since > 20:  # Forex FVGs expire faster than Gold
                pending_fvg_setups.remove(pending)
                continue
            
            if fvg.direction == FVGDirection.BULLISH and df['Low'].iloc[i] <= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "forex_killzone", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
            elif fvg.direction == FVGDirection.BEARISH and df['High'].iloc[i] >= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "forex_killzone", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
        
        # ============================================================
        # Check pending sweeps for FVG formation (adjacent-bar window)
        # Sweeps persist for up to 3 bars waiting for FVG to form
        # ============================================================
        for ps in pending_sweeps[:]:
            bars_since_sweep = i - ps['index']
            if bars_since_sweep > 3:
                pending_sweeps.remove(ps)
                continue
            
            fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                             overlap_tolerance_atr=0.1, precomputed_atr=atr_14)
            if fvg:
                sweep = ps['sweep']
                if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
                   (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                    pending_fvg_setups.append({
                        'fvg': fvg,
                        'sweep': sweep,
                    })
                    pending_sweeps.remove(ps)
                    break  # Only match one pending sweep per FVG
        
        # ============================================================
        # Killzone check (skip if outside trading hours on intraday data)
        # ============================================================
        if not is_daily and not _is_killzone(df.index[i]):
            continue
        
        # ============================================================
        # Step 1: Get the Asian session range
        # ============================================================
        asian_high, asian_low = _get_asian_range(df, i)
        if asian_high <= 0 or asian_low <= 0:
            continue
        
        # ============================================================
        # O1+N1: JPY pairs — trade WITH Asian breakout (1H only)
        # On 4H+, JPY uses standard killzone logic (breakout too noisy)
        # ============================================================
        if use_jpy_breakout:
            current_close = df['Close'].iloc[i]
            atr_val = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
            ema_val = ema_50.iloc[i] if not pd.isna(ema_50.iloc[i]) else current_close
            
            breakout = _detect_asian_breakout(df, i, asian_high, asian_low, atr_val, ema_val, current_close)
            if breakout:
                # Set position size
                if atr_val > 0:
                    breakout.position_size = (equity * risk_pct) / (atr_val * 2)
                setups.append(breakout)
            
            # JPY also checks PDH/PDL sweeps (standard fade logic still applies to PDH/PDL)
            sweep = None
            pdh, pdl = get_previous_day_levels(df, i)
            if pdh > 0:
                sweep = detect_liquidity_sweep(df, i, pdh, "pdh")
            if not sweep and pdl > 0:
                sweep = detect_liquidity_sweep(df, i, pdl, "pdl")
            
            if not sweep:
                continue
        else:
            # ============================================================
            # Step 2: Detect liquidity sweep
            # P3: JPY on slow TFs (4H+) — skip Asian range fades entirely.
            # JPY's Asian session is the primary move, not a trap. Fading it
            # on 4H produced -$183 (30% WR on 33 trades). Only PDH/PDL fades
            # work for JPY on slow TFs, where the levels are more universal.
            # ============================================================
            sweep = None
            
            if not (is_jpy and not is_fast_tf):
                # Standard pairs (EUR, GBP, etc.) — fade the Asian range trap
                sweep = detect_liquidity_sweep(df, i, asian_high, "asian_high")
                if not sweep:
                    sweep = detect_liquidity_sweep(df, i, asian_low, "asian_low")
        
            if not sweep:
                # PDH/PDL sweeps — universal, works for all pairs and timeframes
                pdh, pdl = get_previous_day_levels(df, i)
                if pdh > 0:
                    sweep = detect_liquidity_sweep(df, i, pdh, "pdh")
                if not sweep and pdl > 0:
                    sweep = detect_liquidity_sweep(df, i, pdl, "pdl")
            
            if not sweep:
                continue
        
        # ============================================================
        # Step 3: Confirm Market Structure Shift
        # ============================================================
        if not is_daily and not _detect_mss(df, i, sweep):
            continue  # No MSS confirmation, skip
        
        # ============================================================
        # Step 4: Check for displacement + FVG (Priority 1.4: min_df 1.5→1.0)
        # ============================================================
        fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                         overlap_tolerance_atr=0.1, precomputed_atr=atr_14)
        
        if fvg:
            # Immediate match: queue FVG for fill entry
            if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
               (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                pending_fvg_setups.append({
                    'fvg': fvg,
                    'sweep': sweep,
                })
        else:
            # No FVG on same bar -- try displacement fallback first
            # Priority 1.4: fallback threshold lowered 1.5→0.75
            entered_fallback = False
            if not pd.isna(df_series.iloc[i]) and df_series.iloc[i] >= 0.75:
                atr_val = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
                if atr_val > 0:
                    current_close = df['Close'].iloc[i]
                    
                    if sweep.direction == SweepDirection.BULLISH:
                        entry = current_close
                        sl = sweep.sweep_extreme - atr_val * 0.5
                        tp = entry + abs(entry - sl) * 2.5  # 2.5R target
                    else:
                        entry = current_close
                        sl = sweep.sweep_extreme + atr_val * 0.5
                        tp = entry - abs(sl - entry) * 2.5
                    
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    rr = reward / risk if risk > 0 else 0
                    
                    if rr >= 1.5:
                        direction = 'long' if sweep.direction == SweepDirection.BULLISH else 'short'
                        
                        # EMA trend check (Priority 1.6: widened 1%→2%)
                        skip_trade = False
                        if not pd.isna(ema_50.iloc[i]):
                            ema_dist = (current_close - ema_50.iloc[i]) / ema_50.iloc[i]
                            if direction == 'long' and ema_dist < -0.02:
                                skip_trade = True  # Don't long below EMA in downtrend
                            if direction == 'short' and ema_dist > 0.02:
                                skip_trade = True  # Don't short above EMA in uptrend
                        
                        if not skip_trade:
                            setup = TradeSetup(
                                direction=direction,
                                entry_price=entry,
                                stop_loss=sl,
                                take_profit=tp,
                                position_size=(equity * risk_pct) / (atr_val * 2) if atr_val > 0 else 0,
                                risk_reward=rr,
                                regime="forex_killzone",
                                sweep=sweep,
                                fvg=FairValueGap(
                                    FVGDirection.BULLISH if direction == 'long' else FVGDirection.BEARISH,
                                    entry, entry, entry, 0, i, df_series.iloc[i]
                                ),
                                displacement_df=df_series.iloc[i],
                                index=i
                            )
                            setups.append(setup)
                            entered_fallback = True
            
            # If no displacement fallback, buffer sweep for adjacent-bar FVG window
            if not entered_fallback:
                pending_sweeps.append({
                    'sweep': sweep,
                    'index': i,
                })
    
    return setups
