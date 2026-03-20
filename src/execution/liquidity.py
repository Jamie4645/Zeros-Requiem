"""
Liquidity Sweep Detection for SCAF 2.0

Detects when price sweeps significant liquidity pools:
- Previous Day High/Low (PDH/PDL)
- Session High/Low
- Weekly High/Low
- Asian Range boundaries (Forex)

A "sweep" = price pokes beyond the level then reverses, clearing retail stops.

Priority 1.2 Enhancement: Multi-bar sweep detection allows the poke and
close-back to occur across 1-3 bars instead of requiring same-bar reversal.
Many institutional sweeps take 2-3 candles to complete.

Priority 1.3 Enhancement: Sweep tolerance widened from 0.3 to 0.5 ATR to
capture more aggressive sweep moves (especially on Gold).
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from ..indicators.technical import atr


class SweepDirection(Enum):
    BULLISH = "bullish"    # Swept lows (bearish trap), expect upward reversal
    BEARISH = "bearish"    # Swept highs (bullish trap), expect downward reversal


@dataclass
class LiquiditySweep:
    """A detected liquidity sweep event."""
    direction: SweepDirection
    sweep_level: float          # The level that was swept (e.g., PDL at $2580)
    sweep_extreme: float        # How far price went beyond (e.g., low of $2575)
    close_price: float          # Where the candle closed (back above/below the level)
    index: int                  # Bar index
    level_type: str             # "pdh", "pdl", "session_high", "session_low", "asian_high", "asian_low", "weekly_high", "weekly_low"


def get_previous_day_levels(df: pd.DataFrame, current_index: int) -> Tuple[float, float]:
    """
    Get Previous Day High (PDH) and Previous Day Low (PDL).
    
    Looks backward from current_index to find the most recent complete day's high/low.
    Works on any timeframe (1H, 4H, daily).
    """
    if current_index < 2:
        return (0.0, 0.0)
    
    current_date = None
    prev_day_high = 0.0
    prev_day_low = float('inf')
    found_prev_day = False
    
    try:
        current_date = df.index[current_index].date()
    except AttributeError:
        # Daily data without proper datetime index -- use previous bar
        if current_index >= 1:
            return (df['High'].iloc[current_index - 1], df['Low'].iloc[current_index - 1])
        return (0.0, 0.0)
    
    # Walk backward to find previous day's bars
    for i in range(current_index - 1, max(0, current_index - 100), -1):
        try:
            bar_date = df.index[i].date()
        except AttributeError:
            continue
        
        if bar_date == current_date:
            continue  # Still on the same day
        
        if not found_prev_day:
            found_prev_day = True
            prev_date = bar_date
        
        if bar_date == prev_date:
            prev_day_high = max(prev_day_high, df['High'].iloc[i])
            prev_day_low = min(prev_day_low, df['Low'].iloc[i])
        elif bar_date < prev_date:
            break  # Moved to the day before previous
    
    if not found_prev_day or prev_day_low == float('inf'):
        return (0.0, 0.0)
    
    return (prev_day_high, prev_day_low)


def detect_liquidity_sweep(
    df: pd.DataFrame,
    index: int,
    level: float,
    level_type: str,
    sweep_tolerance_atr_mult: float = 0.5,
    sweep_lookback: int = 3,
    precomputed_atr: Optional[pd.Series] = None
) -> Optional[LiquiditySweep]:
    """
    Detect if price sweeps a liquidity level at or near the current bar.
    
    A sweep occurs when:
    - Price pokes beyond the level (clearing stops)
    - Price closes back on the original side (rejection)
    
    Priority 1.2: Multi-bar sweep. The poke can happen on any of the last
    `sweep_lookback` bars, and the current bar's close confirms the reversal.
    This captures sweeps that take 2-3 candles to complete.
    
    Priority 1.3: Default tolerance widened from 0.3 to 0.5 ATR.
    
    Args:
        df: OHLCV DataFrame
        index: Current bar index (the "confirmation" bar)
        level: The liquidity level to check
        level_type: Description of the level (e.g., "pdh", "pdl")
        sweep_tolerance_atr_mult: Max distance beyond level (in ATR units)
        sweep_lookback: How many bars back to look for the poke (1 = same-bar only)
        precomputed_atr: Optional pre-calculated ATR(14) series
    """
    if index < 15 or level <= 0:
        return None
    
    # Calculate ATR for adaptive sweep distance
    if precomputed_atr is not None:
        if pd.isna(precomputed_atr.iloc[index]):
            return None
        atr_val = precomputed_atr.iloc[index]
    else:
        atr_series = atr(df, 14)
        if pd.isna(atr_series.iloc[index]):
            return None
        atr_val = atr_series.iloc[index]
    
    sweep_distance = atr_val * sweep_tolerance_atr_mult
    
    current_close = df['Close'].iloc[index]
    
    # Look back over the sweep window for a poke beyond the level
    lookback_start = max(0, index - sweep_lookback + 1)
    
    # ------------------------------------------------------------------
    # Check for HIGH sweep (price poked above level, now closes below)
    # This is a BEARISH sweep -- longs got trapped
    # ------------------------------------------------------------------
    best_high = 0.0
    best_high_index = index
    for j in range(lookback_start, index + 1):
        bar_high = df['High'].iloc[j]
        if bar_high > best_high:
            best_high = bar_high
            best_high_index = j
    
    if best_high > level and best_high <= level + sweep_distance:
        if current_close < level:
            return LiquiditySweep(
                direction=SweepDirection.BEARISH,
                sweep_level=level,
                sweep_extreme=best_high,
                close_price=current_close,
                index=index,  # Use confirmation bar as the sweep index
                level_type=level_type
            )
    
    # ------------------------------------------------------------------
    # Check for LOW sweep (price poked below level, now closes above)
    # This is a BULLISH sweep -- shorts got trapped
    # ------------------------------------------------------------------
    best_low = float('inf')
    best_low_index = index
    for j in range(lookback_start, index + 1):
        bar_low = df['Low'].iloc[j]
        if bar_low < best_low:
            best_low = bar_low
            best_low_index = j
    
    if best_low < level and best_low >= level - sweep_distance:
        if current_close > level:
            return LiquiditySweep(
                direction=SweepDirection.BULLISH,
                sweep_level=level,
                sweep_extreme=best_low,
                close_price=current_close,
                index=index,
                level_type=level_type
            )
    
    return None


def get_weekly_levels(df: pd.DataFrame, current_index: int, lookback_bars: int = 40) -> Tuple[float, float]:
    """
    Get the Weekly High and Weekly Low looking back over recent bars.
    
    Priority 2.1: Provides weekly liquidity levels for daily data where
    session-based levels don't exist. On daily data, a 5-7 bar lookback
    covers one trading week. On 4H, ~40 bars covers a week.
    
    Returns (weekly_high, weekly_low). Returns (0, 0) if not enough data.
    """
    lookback = min(lookback_bars, current_index)
    if lookback < 5:
        return (0.0, 0.0)
    
    window = df.iloc[current_index - lookback:current_index]
    return (window['High'].max(), window['Low'].min())


def get_swing_levels(
    df: pd.DataFrame,
    current_index: int,
    lookback: int = 20,
    swing_window: int = 3
) -> Tuple[float, float]:
    """
    Detect the most recent swing high and swing low.
    
    Priority 2.2: A swing high is a bar whose high is higher than the
    `swing_window` bars on either side. A swing low is a bar whose low
    is lower than the `swing_window` bars on either side.
    
    These are natural stop-loss cluster points where retail traders place
    orders, making them prime liquidity targets.
    
    Args:
        df: OHLCV DataFrame
        current_index: Current bar (look backward from here)
        lookback: How many bars back to search
        swing_window: Bars on each side to confirm a swing point
    
    Returns (swing_high, swing_low). Returns (0, 0) if not found.
    """
    swing_high = 0.0
    swing_low = 0.0
    
    # Need at least swing_window bars ahead of the candidate to confirm
    # So the most recent candidate is at current_index - swing_window
    search_end = current_index - swing_window
    search_start = max(swing_window, current_index - lookback)
    
    # Find most recent swing high (search backward)
    for i in range(search_end, search_start - 1, -1):
        bar_high = df['High'].iloc[i]
        is_swing = True
        
        for j in range(1, swing_window + 1):
            left = i - j
            right = i + j
            if left < 0 or right >= len(df):
                is_swing = False
                break
            if df['High'].iloc[left] >= bar_high or df['High'].iloc[right] >= bar_high:
                is_swing = False
                break
        
        if is_swing:
            swing_high = bar_high
            break
    
    # Find most recent swing low (search backward)
    for i in range(search_end, search_start - 1, -1):
        bar_low = df['Low'].iloc[i]
        is_swing = True
        
        for j in range(1, swing_window + 1):
            left = i - j
            right = i + j
            if left < 0 or right >= len(df):
                is_swing = False
                break
            if df['Low'].iloc[left] <= bar_low or df['Low'].iloc[right] <= bar_low:
                is_swing = False
                break
        
        if is_swing:
            swing_low = bar_low
            break
    
    return (swing_high, swing_low)


def scan_for_sweeps(
    df: pd.DataFrame,
    index: int,
    session_high: float = 0,
    session_low: float = 0,
    asian_high: float = 0,
    asian_low: float = 0,
    weekly_high: float = 0,
    weekly_low: float = 0,
    swing_high: float = 0,
    swing_low: float = 0
) -> list:
    """
    Scan all available liquidity levels for sweeps at the current bar.
    
    Priority 2.1/2.2: Now accepts weekly and swing levels as parameters,
    giving regimes (especially Gold Daily) more liquidity sources.
    
    Returns a list of LiquiditySweep objects.
    """
    sweeps = []
    
    # Previous Day High/Low
    pdh, pdl = get_previous_day_levels(df, index)
    if pdh > 0:
        s = detect_liquidity_sweep(df, index, pdh, "pdh")
        if s:
            sweeps.append(s)
    if pdl > 0:
        s = detect_liquidity_sweep(df, index, pdl, "pdl")
        if s:
            sweeps.append(s)
    
    # Weekly levels (Priority 2.1)
    if weekly_high > 0:
        s = detect_liquidity_sweep(df, index, weekly_high, "weekly_high")
        if s:
            sweeps.append(s)
    if weekly_low > 0:
        s = detect_liquidity_sweep(df, index, weekly_low, "weekly_low")
        if s:
            sweeps.append(s)
    
    # Swing levels (Priority 2.2)
    if swing_high > 0:
        s = detect_liquidity_sweep(df, index, swing_high, "swing_high")
        if s:
            sweeps.append(s)
    if swing_low > 0:
        s = detect_liquidity_sweep(df, index, swing_low, "swing_low")
        if s:
            sweeps.append(s)
    
    # Session levels (passed in from regime)
    if session_high > 0:
        s = detect_liquidity_sweep(df, index, session_high, "session_high")
        if s:
            sweeps.append(s)
    if session_low > 0:
        s = detect_liquidity_sweep(df, index, session_low, "session_low")
        if s:
            sweeps.append(s)
    
    # Asian range (Forex regime)
    if asian_high > 0:
        s = detect_liquidity_sweep(df, index, asian_high, "asian_high")
        if s:
            sweeps.append(s)
    if asian_low > 0:
        s = detect_liquidity_sweep(df, index, asian_low, "asian_low")
        if s:
            sweeps.append(s)
    
    return sweeps
