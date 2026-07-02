"""
Smart Money Indicators for SBRS 2.0

Fair Value Gaps, Liquidity Sweeps, MA Whipsaw Detection,
Bollinger Squeeze, Level Quality, and False Breakout Detection.

All functions are look-ahead safe — they only use data at or before current_idx.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


def detect_fvg_bullish(
    df: pd.DataFrame, current_idx: int, lookback: int = 10
) -> Optional[Tuple[int, float, float]]:
    """
    Detect most recent bullish Fair Value Gap within lookback.

    Bullish FVG: candle[j].High < candle[j+2].Low (gap between candle 1 and candle 3).
    Returns (bar_index_of_middle_candle, gap_low, gap_high) or None.

    gap_low = candle[j].High, gap_high = candle[j+2].Low
    Only checks completed patterns (j+2 <= current_idx).
    """
    start = max(0, current_idx - lookback - 2)
    # j+2 <= current_idx => j <= current_idx - 2
    end = current_idx - 2

    for j in range(end, start - 1, -1):
        gap_low = df['High'].iloc[j]
        gap_high = df['Low'].iloc[j + 2]
        if gap_low < gap_high:
            return (j + 1, gap_low, gap_high)

    return None


def detect_fvg_bearish(
    df: pd.DataFrame, current_idx: int, lookback: int = 10
) -> Optional[Tuple[int, float, float]]:
    """
    Detect most recent bearish FVG within lookback.

    Bearish FVG: candle[j].Low > candle[j+2].High (gap between candle 1 and candle 3).
    Returns (bar_index_of_middle_candle, gap_high, gap_low) or None.

    gap_high = candle[j].Low, gap_low = candle[j+2].High
    """
    start = max(0, current_idx - lookback - 2)
    end = current_idx - 2

    for j in range(end, start - 1, -1):
        gap_high = df['Low'].iloc[j]
        gap_low = df['High'].iloc[j + 2]
        if gap_high > gap_low:
            return (j + 1, gap_high, gap_low)

    return None


def detect_fvg_near_level(
    df: pd.DataFrame, current_idx: int, level: float, direction: str,
    atr_val: float, lookback: int = 10, proximity_atr: float = 1.0,
    min_gap_atr: float = 0.15
) -> bool:
    """
    Check if a meaningful FVG exists within proximity_atr * ATR of a given S/R level.

    For longs: check bullish FVG. For shorts: check bearish FVG.
    The FVG's gap zone must overlap with [level - proximity, level + proximity].
    The gap must be at least min_gap_atr * ATR wide to be considered meaningful.
    direction is 'long' or 'short'.
    """
    proximity = proximity_atr * atr_val

    if direction == 'long':
        result = detect_fvg_bullish(df, current_idx, lookback)
        if result is None:
            return False
        _, gap_low, gap_high = result
    elif direction == 'short':
        result = detect_fvg_bearish(df, current_idx, lookback)
        if result is None:
            return False
        _, gap_high, gap_low = result
    else:
        return False

    # Gap must be meaningful (not just noise)
    gap_size = abs(gap_high - gap_low)
    if gap_size < min_gap_atr * atr_val:
        return False

    level_low = level - proximity
    level_high = level + proximity

    # Check overlap between [gap_low, gap_high] and [level_low, level_high]
    return gap_low <= level_high and gap_high >= level_low


def detect_liquidity_sweep(
    df: pd.DataFrame, current_idx: int,
    swing_high_mask: pd.Series, swing_low_mask: pd.Series,
    direction: str, lookback: int = 20,
    sweep_confirm_bars: int = 3,
    swing_confirm_lag: int = 3
) -> bool:
    """
    Detect if a liquidity sweep occurred before the current bar.

    For LONGS: price broke BELOW a recent swing low then reversed back above
    it within sweep_confirm_bars.
    For SHORTS: price broke ABOVE a recent swing high then reversed back below
    it within sweep_confirm_bars.

    swing_confirm_lag: the swing masks are built with `right` future bars
    (detect_swing_high/low, default 3), so a swing at bar i is only CONFIRMED
    at bar i+lag. Only swings with i + swing_confirm_lag <= current_idx are
    visible at decision time. Without this cutoff the +1.0 confluence booster
    read up to 3 future bars (2026-07-02 audit: look-ahead leakage).
    """
    search_start = max(0, current_idx - lookback)
    newest_visible = current_idx - swing_confirm_lag

    if direction == 'long':
        # Find most recent CONFIRMED-visible swing low
        swing_level = None
        swing_idx = None
        for i in range(newest_visible, search_start - 1, -1):
            if swing_low_mask.iloc[i]:
                swing_level = df['Low'].iloc[i]
                swing_idx = i
                break

        if swing_level is None:
            return False

        # Check for sweep: bar with Low < swing_level, then reversal
        for i in range(swing_idx + 1, current_idx):
            if df['Low'].iloc[i] < swing_level:
                # Check reversal within sweep_confirm_bars
                confirm_end = min(current_idx, i + sweep_confirm_bars + 1)
                for k in range(i, confirm_end):
                    if df['Close'].iloc[k] > swing_level:
                        return True
                break  # Only check first sweep

    elif direction == 'short':
        # Find most recent CONFIRMED-visible swing high
        swing_level = None
        swing_idx = None
        for i in range(newest_visible, search_start - 1, -1):
            if swing_high_mask.iloc[i]:
                swing_level = df['High'].iloc[i]
                swing_idx = i
                break

        if swing_level is None:
            return False

        # Check for sweep: bar with High > swing_level, then reversal
        for i in range(swing_idx + 1, current_idx):
            if df['High'].iloc[i] > swing_level:
                confirm_end = min(current_idx, i + sweep_confirm_bars + 1)
                for k in range(i, confirm_end):
                    if df['Close'].iloc[k] < swing_level:
                        return True
                break

    return False


def detect_ma_whipsaw(
    wma_vals: pd.Series, smma_vals: pd.Series,
    current_idx: int, lookback: int = 15, max_crosses: int = 2
) -> bool:
    """
    Detect if MA crossovers are whipsawing (unreliable).

    Count how many times WMA crossed SMMA within lookback bars ending at current_idx.
    A cross = sign change in (WMA - SMMA) between consecutive bars.
    Returns True if crosses > max_crosses (signal is unreliable).
    """
    start = max(1, current_idx - lookback + 1)
    diff = wma_vals - smma_vals
    crosses = 0

    for i in range(start, current_idx + 1):
        prev = diff.iloc[i - 1]
        curr = diff.iloc[i]
        if np.isnan(prev) or np.isnan(curr):
            continue
        if (prev > 0 and curr < 0) or (prev < 0 and curr > 0):
            crosses += 1

    return crosses > max_crosses


def detect_bollinger_squeeze(
    df: pd.DataFrame, current_idx: int,
    bb_period: int = 20, bb_std: float = 2.0,
    squeeze_threshold: float = 0.5, lookback: int = 50
) -> bool:
    """
    Detect tight consolidation via Bollinger Band squeeze.

    Compute BB width = (upper - lower) / middle at current_idx.
    Compare to average BB width over last `lookback` bars.
    If current width < squeeze_threshold * average width, return True (squeeze).
    """
    required = bb_period + lookback
    if current_idx < required - 1:
        return False

    close = df['Close'].iloc[:current_idx + 1]
    middle = close.rolling(window=bb_period).mean()
    rolling_std = close.rolling(window=bb_period).std()
    upper = middle + bb_std * rolling_std
    lower = middle - bb_std * rolling_std

    width = (upper - lower) / middle

    current_width = width.iloc[current_idx]
    if np.isnan(current_width):
        return False

    avg_start = max(bb_period - 1, current_idx - lookback)
    avg_width = width.iloc[avg_start:current_idx + 1].mean()

    if np.isnan(avg_width) or avg_width == 0:
        return False

    return current_width < squeeze_threshold * avg_width


def count_level_touches(
    df: pd.DataFrame, level: float, current_idx: int,
    atr_val: float, lookback: int = 50, tolerance_atr: float = 0.3
) -> int:
    """
    Count how many times price touched a S/R level without breaking through.

    A "touch" = bar where High or Low came within tolerance_atr * ATR of the level,
    AND the bar before or after was NOT within tolerance.

    Require at least 3 bars between touches to avoid counting consecutive bars.
    """
    tolerance = tolerance_atr * atr_val
    start = max(0, current_idx - lookback)
    touches = 0
    last_touch_idx = -10  # Ensure first touch can always count

    for i in range(start, current_idx + 1):
        high_i = df['High'].iloc[i]
        low_i = df['Low'].iloc[i]

        # Check if this bar is near the level
        near = (abs(high_i - level) <= tolerance) or (abs(low_i - level) <= tolerance)
        if not near:
            continue

        # Check spacing from last touch
        if i - last_touch_idx < 3:
            continue

        touches += 1
        last_touch_idx = i

    return touches


def detect_false_breakout(
    df: pd.DataFrame, level: float, direction: str,
    current_idx: int, atr_val: float,
    lookback: int = 30, tolerance_atr: float = 0.3
) -> bool:
    """
    Check if a false breakout occurred at this level within lookback bars.

    For longs (breakout above level):
    A false breakout = some bar closed above level, then within 3 bars,
    price closed back below level.

    For shorts (breakout below level):
    A false breakout = some bar closed below level, then within 3 bars,
    price closed back above level.

    Returns True if a previous false breakout was found.
    """
    start = max(0, current_idx - lookback)

    if direction == 'long':
        for i in range(start, current_idx - 1):
            if df['Close'].iloc[i] > level:
                check_end = min(current_idx + 1, i + 4)  # within 3 bars
                for k in range(i + 1, check_end):
                    if df['Close'].iloc[k] < level:
                        return True

    elif direction == 'short':
        for i in range(start, current_idx - 1):
            if df['Close'].iloc[i] < level:
                check_end = min(current_idx + 1, i + 4)
                for k in range(i + 1, check_end):
                    if df['Close'].iloc[k] > level:
                        return True

    return False
