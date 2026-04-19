"""
Technical Indicators for SBRS 1.1

Core indicators used by the Sovereign Breakout Retest Strategy:
- ATR (Average True Range)
- WMA (Weighted Moving Average)
- SMMA (Smoothed Moving Average)
- Swing High / Low detection (configurable left + right bars)
- EMA / SMA (general purpose)
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


# ============================================================
# Core Indicators
# ============================================================

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range -- measures volatility."""
    high = df['High']
    low = df['Low']
    close = df['Close']

    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def ema(series: pd.Series, period: int = 200) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int = 20) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0-100)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ============================================================
# SBRS Indicators — WMA, SMMA, Swing Detection
# ============================================================

def wma(series: pd.Series, period: int = 9) -> pd.Series:
    """
    Weighted Moving Average.

    Most recent bar gets weight = period, second most recent = period-1, etc.
    WMA = sum(weight_i * price_i) / sum(weights)

    Args:
        series: Price series (typically close)
        period: WMA period (default 9 — DO NOT OPTIMIZE)

    Returns:
        pd.Series of WMA values (NaN for first period-1 bars)
    """
    weights = np.arange(1, period + 1, dtype=float)  # [1, 2, ..., period]
    weight_sum = weights.sum()

    def _wma_calc(window):
        return np.dot(window, weights) / weight_sum

    return series.rolling(window=period).apply(_wma_calc, raw=True)


def smma(series: pd.Series, period: int = 7) -> pd.Series:
    """
    Smoothed Moving Average (true SMMA, NOT an EMA approximation).

    Also known as Modified Moving Average (MMA) or Running Moving Average.
    This is the exact calculation used in MetaTrader and TradingView.

    Formula:
        SMMA[0] = SMA(first N bars)
        SMMA[i] = (SMMA[i-1] * (period - 1) + close[i]) / period

    Args:
        series: Price series (typically close)
        period: SMMA period (default 7 — DO NOT OPTIMIZE)

    Returns:
        pd.Series of SMMA values (NaN until enough data)
    """
    values = series.values.astype(float)
    result = np.full(len(values), np.nan)

    # Find first valid window of `period` non-NaN values
    valid_count = 0
    start_idx = -1
    for i in range(len(values)):
        if not np.isnan(values[i]):
            valid_count += 1
            if valid_count == period:
                start_idx = i
                break
        else:
            valid_count = 0

    if start_idx < 0:
        return pd.Series(result, index=series.index)

    # Seed: SMA of first `period` valid values
    first_window_start = start_idx - period + 1
    result[start_idx] = np.mean(values[first_window_start:start_idx + 1])

    # Recursive: SMMA[i] = (SMMA[i-1] * (period-1) + close[i]) / period
    for i in range(start_idx + 1, len(values)):
        if np.isnan(values[i]):
            result[i] = result[i - 1]  # Carry forward on NaN
        else:
            result[i] = (result[i - 1] * (period - 1) + values[i]) / period

    return pd.Series(result, index=series.index)


def detect_swing_high(highs: pd.Series, left: int = 3, right: int = 3) -> pd.Series:
    """
    Detect swing highs with left/right bar confirmation.

    A swing high at bar i requires ALL of:
      - highs[i-left], ..., highs[i-1] < highs[i]  (left bars lower)
      - highs[i+1], ..., highs[i+right] < highs[i]  (right bars lower)

    A swing at bar i is only detectable at bar i+right (confirmation lag).

    Returns:
        pd.Series[bool] — True where swing high is confirmed
    """
    n = len(highs)
    h = highs.values.astype(float)
    result = np.zeros(n, dtype=bool)

    for i in range(left, n - right):
        candidate = h[i]
        if np.isnan(candidate):
            continue

        is_swing = True
        for j in range(i - left, i):
            if np.isnan(h[j]) or h[j] >= candidate:
                is_swing = False
                break

        if not is_swing:
            continue

        for j in range(i + 1, i + right + 1):
            if np.isnan(h[j]) or h[j] >= candidate:
                is_swing = False
                break

        result[i] = is_swing

    return pd.Series(result, index=highs.index)


def detect_swing_low(lows: pd.Series, left: int = 3, right: int = 3) -> pd.Series:
    """
    Detect swing lows with left/right bar confirmation.

    A swing low at bar i requires ALL of:
      - lows[i-left], ..., lows[i-1] > lows[i]  (left bars higher)
      - lows[i+1], ..., lows[i+right] > lows[i]  (right bars higher)

    Returns:
        pd.Series[bool] — True where swing low is confirmed
    """
    n = len(lows)
    lo = lows.values.astype(float)
    result = np.zeros(n, dtype=bool)

    for i in range(left, n - right):
        candidate = lo[i]
        if np.isnan(candidate):
            continue

        is_swing = True
        for j in range(i - left, i):
            if np.isnan(lo[j]) or lo[j] <= candidate:
                is_swing = False
                break

        if not is_swing:
            continue

        for j in range(i + 1, i + right + 1):
            if np.isnan(lo[j]) or lo[j] <= candidate:
                is_swing = False
                break

        result[i] = is_swing

    return pd.Series(result, index=lows.index)


def get_recent_swing_high(
    highs: pd.Series,
    swing_mask: pd.Series,
    current_idx: int,
    lookback: int = 20
) -> Optional[Tuple[int, float]]:
    """
    Get most recent confirmed swing high within lookback window.

    Only returns swings detectable at current_idx (3-bar confirmation lag).

    Returns:
        (bar_iloc_index, high_value) or None if no swing found
    """
    search_end = current_idx - 3  # inclusive
    search_start = max(0, current_idx - lookback)

    if search_end < search_start:
        return None

    for i in range(search_end, search_start - 1, -1):
        if swing_mask.iloc[i]:
            return (i, highs.iloc[i])

    return None


def get_recent_swing_low(
    lows: pd.Series,
    swing_mask: pd.Series,
    current_idx: int,
    lookback: int = 20
) -> Optional[Tuple[int, float]]:
    """
    Get most recent confirmed swing low within lookback window.

    Only returns swings detectable at current_idx (3-bar confirmation lag).

    Returns:
        (bar_iloc_index, low_value) or None if no swing found
    """
    search_end = current_idx - 3  # inclusive
    search_start = max(0, current_idx - lookback)

    if search_end < search_start:
        return None

    for i in range(search_end, search_start - 1, -1):
        if swing_mask.iloc[i]:
            return (i, lows.iloc[i])

    return None


# ============================================================
# Bollinger Bands
# ============================================================

def bollinger_bands(
    series: pd.Series, period: int = 20, std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands: middle +/- std_dev * rolling_std.

    Returns (upper, middle, lower).
    """
    middle = series.rolling(window=period).mean()
    rolling_std = series.rolling(window=period).std()
    upper = middle + std_dev * rolling_std
    lower = middle - std_dev * rolling_std
    return upper, middle, lower
