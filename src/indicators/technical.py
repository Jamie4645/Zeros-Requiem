"""
Technical Indicators for SCAF 2.0 + SBRS 1.0

All indicators used across regimes:
- ATR (Average True Range)
- Bollinger Bands
- EMA / SMA
- RSI
- Volatility Ratio (ATR fast/slow)
- Displacement Factor (Df)

SBRS 1.0 additions:
- WMA (Weighted Moving Average)
- SMMA (Smoothed Moving Average)
- Swing High / Low detection (3-bar left + 3-bar right)
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
# Bollinger Bands
# ============================================================

def bollinger_bands(
    series: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.5
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.
    
    Returns: (upper_band, middle_band, lower_band)
    """
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


# ============================================================
# Volatility Ratio (for Crypto regime)
# ============================================================

def volatility_ratio(df: pd.DataFrame, fast: int = 5, slow: int = 50) -> pd.Series:
    """
    Volatility Ratio: ATR(fast) / ATR(slow)
    
    VR < 0.5 = extreme compression ("coiled spring")
    VR < 0.7 = moderate compression
    VR > 1.0 = expanding volatility
    """
    atr_fast = atr(df, fast)
    atr_slow = atr(df, slow)
    
    return atr_fast / atr_slow


# ============================================================
# Displacement Factor (Df)
# ============================================================

def candle_body(df: pd.DataFrame) -> pd.Series:
    """Absolute candle body size."""
    return abs(df['Close'] - df['Open'])


def displacement_factor(df: pd.DataFrame, lookback: int = 50) -> pd.Series:
    """
    Displacement Factor (Df) -- Z-score of current candle body vs recent average.
    
    Df = (body_current - mean(body_50)) / std(body_50)
    
    Df > 2.0 = institutional displacement (2 standard deviations above average)
    """
    body = candle_body(df)
    body_mean = body.rolling(window=lookback).mean()
    body_std = body.rolling(window=lookback).std()
    
    # Avoid division by zero
    body_std = body_std.replace(0, np.nan)
    
    return (body - body_mean) / body_std


def is_expansion_candle(df: pd.DataFrame, index: int, body_pct_threshold: float = 0.80) -> bool:
    """
    Check if candle at index is an expansion candle (body > 80% of total range).
    Used in crypto regime.
    """
    o = df['Open'].iloc[index]
    h = df['High'].iloc[index]
    l = df['Low'].iloc[index]
    c = df['Close'].iloc[index]
    
    total_range = h - l
    body = abs(c - o)
    
    if total_range == 0:
        return False
    
    return (body / total_range) >= body_pct_threshold


# ============================================================
# Session / Time Detection
# ============================================================

def detect_session(timestamp, asset_class: str = 'gold') -> str:
    """
    Detect the current trading session from a timestamp.
    
    Gold sessions (GMT):
    - Asia: 00:00-08:00
    - London: 08:00-12:00
    - NY Overlap: 12:00-16:00
    - NY Afternoon: 16:00-21:00
    - Off-hours: 21:00-00:00
    
    Forex sessions (GMT):
    - Asia: 00:00-08:00
    - London Open (Killzone): 08:00-11:00
    - London/NY Overlap: 12:00-13:00
    - NY Open (Killzone): 13:00-16:00
    - NY Close: 16:00-21:00
    
    Returns session name string.
    """
    try:
        hour = timestamp.hour
    except AttributeError:
        # If timestamp doesn't have hour (daily data), return 'daily'
        return 'daily'
    
    if asset_class == 'gold':
        if 0 <= hour < 8:
            return 'asia'
        elif 8 <= hour < 12:
            return 'london'
        elif 12 <= hour < 16:
            return 'ny_overlap'
        elif 16 <= hour < 21:
            return 'ny_afternoon'
        else:
            return 'off_hours'
    
    elif asset_class == 'forex':
        if 0 <= hour < 8:
            return 'asia'
        elif 8 <= hour < 11:
            return 'london_killzone'
        elif 11 <= hour < 13:
            return 'london_ny_transition'
        elif 13 <= hour < 16:
            return 'ny_killzone'
        elif 16 <= hour < 21:
            return 'ny_close'
        else:
            return 'off_hours'
    
    else:  # crypto -- 24/7, no session restrictions
        return 'active'


def get_session_range(
    df: pd.DataFrame, 
    end_index: int, 
    session_name: str = 'asia'
) -> Tuple[float, float]:
    """
    Get the high/low range of a specific session looking backward from end_index.
    
    Used for Asian range trap in Forex regime and session-based levels in Gold regime.
    
    Returns (session_high, session_low). Returns (0, 0) if not enough data.
    """
    session_high = 0.0
    session_low = float('inf')
    found_session = False
    
    # Look backward up to 50 bars to find the session
    for i in range(end_index - 1, max(0, end_index - 50), -1):
        try:
            ts = df.index[i]
            hour = ts.hour
        except (AttributeError, IndexError):
            continue
        
        if session_name == 'asia' and 0 <= hour < 8:
            session_high = max(session_high, df['High'].iloc[i])
            session_low = min(session_low, df['Low'].iloc[i])
            found_session = True
        elif session_name == 'london' and 8 <= hour < 12:
            session_high = max(session_high, df['High'].iloc[i])
            session_low = min(session_low, df['Low'].iloc[i])
            found_session = True
        elif found_session:
            # We've moved past the session, stop
            break
    
    if not found_session or session_low == float('inf'):
        return (0.0, 0.0)
    
    return (session_high, session_low)


# ============================================================
# SBRS 1.0 Indicators — WMA, SMMA, Swing Detection
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
    
    Note: SMMA(N) is mathematically equivalent to EMA(2*N - 1), but we
    implement the true SMMA formula for clarity and correctness.
    
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
      - highs[i-left], highs[i-left+1], ..., highs[i-1] < highs[i]  (left bars lower)
      - highs[i+1], highs[i+2], ..., highs[i+right] < highs[i]      (right bars lower)
    
    This means 6 total comparison bars (3 left + 3 right).
    A swing at bar i is only detectable at bar i+right (3-bar lag).
    
    Args:
        highs: Series of high prices
        left: Number of bars to check on left (default 3)
        right: Number of bars to check on right (default 3)
    
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
        # Check left side: all bars must be strictly lower
        for j in range(i - left, i):
            if np.isnan(h[j]) or h[j] >= candidate:
                is_swing = False
                break
        
        if not is_swing:
            continue
        
        # Check right side: all bars must be strictly lower
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
      - lows[i-left], lows[i-left+1], ..., lows[i-1] > lows[i]  (left bars higher)
      - lows[i+1], lows[i+2], ..., lows[i+right] > lows[i]      (right bars higher)
    
    This means 6 total comparison bars (3 left + 3 right).
    A swing at bar i is only detectable at bar i+right (3-bar lag).
    
    Args:
        lows: Series of low prices
        left: Number of bars to check on left (default 3)
        right: Number of bars to check on right (default 3)
    
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
        # Check left side: all bars must be strictly higher
        for j in range(i - left, i):
            if np.isnan(lo[j]) or lo[j] <= candidate:
                is_swing = False
                break
        
        if not is_swing:
            continue
        
        # Check right side: all bars must be strictly higher
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
    
    Only returns swings that are DETECTABLE at current_idx, meaning the
    swing must be at position <= current_idx - right (3-bar confirmation lag).
    We search backward from current_idx - 3 (the most recent detectable swing).
    
    Args:
        highs: Series of high prices
        swing_mask: Boolean Series from detect_swing_high()
        current_idx: Current bar integer position (iloc-based)
        lookback: Number of bars to look back (default 20)
    
    Returns:
        (bar_iloc_index, high_value) or None if no swing found
    """
    # Most recent detectable swing is at current_idx - 3 (needs 3 right bars)
    search_end = current_idx - 3  # inclusive
    search_start = max(0, current_idx - lookback)
    
    if search_end < search_start:
        return None
    
    # Search backward from most recent
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
    
    Only returns swings that are DETECTABLE at current_idx, meaning the
    swing must be at position <= current_idx - right (3-bar confirmation lag).
    
    Args:
        lows: Series of low prices
        swing_mask: Boolean Series from detect_swing_low()
        current_idx: Current bar integer position (iloc-based)
        lookback: Number of bars to look back (default 20)
    
    Returns:
        (bar_iloc_index, low_value) or None if no swing found
    """
    search_end = current_idx - 3  # inclusive, 3-bar confirmation lag
    search_start = max(0, current_idx - lookback)
    
    if search_end < search_start:
        return None
    
    # Search backward from most recent
    for i in range(search_end, search_start - 1, -1):
        if swing_mask.iloc[i]:
            return (i, lows.iloc[i])
    
    return None
