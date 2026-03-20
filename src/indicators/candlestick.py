"""
Candlestick Pattern Detection for SCAF 2.0

Patterns:
- Engulfing (bullish/bearish)
- Pin Bar / Hammer / Shooting Star
- Expansion Candle (body > 80% of range)
"""

import pandas as pd


def is_bullish_engulfing(df: pd.DataFrame, index: int) -> bool:
    """Current bullish candle fully engulfs previous bearish candle."""
    if index < 1:
        return False
    
    prev_o, prev_c = df['Open'].iloc[index-1], df['Close'].iloc[index-1]
    curr_o, curr_c = df['Open'].iloc[index], df['Close'].iloc[index]
    
    if prev_c >= prev_o or curr_c <= curr_o:
        return False
    
    return curr_o <= prev_c and curr_c >= prev_o and abs(curr_c - curr_o) > abs(prev_c - prev_o)


def is_bearish_engulfing(df: pd.DataFrame, index: int) -> bool:
    """Current bearish candle fully engulfs previous bullish candle."""
    if index < 1:
        return False
    
    prev_o, prev_c = df['Open'].iloc[index-1], df['Close'].iloc[index-1]
    curr_o, curr_c = df['Open'].iloc[index], df['Close'].iloc[index]
    
    if prev_c <= prev_o or curr_c >= curr_o:
        return False
    
    return curr_o >= prev_c and curr_c <= prev_o and abs(curr_c - curr_o) > abs(prev_c - prev_o)


def is_bullish_pin_bar(df: pd.DataFrame, index: int) -> bool:
    """Long lower wick showing rejection of lower prices."""
    o, h, l, c = df['Open'].iloc[index], df['High'].iloc[index], df['Low'].iloc[index], df['Close'].iloc[index]
    
    body = abs(c - o)
    total_range = h - l
    lower_wick = min(o, c) - l
    upper_wick = h - max(o, c)
    
    if total_range == 0 or body == 0:
        return False
    
    return lower_wick >= body * 2 and upper_wick <= total_range * 0.3


def is_bearish_pin_bar(df: pd.DataFrame, index: int) -> bool:
    """Long upper wick showing rejection of higher prices."""
    o, h, l, c = df['Open'].iloc[index], df['High'].iloc[index], df['Low'].iloc[index], df['Close'].iloc[index]
    
    body = abs(c - o)
    total_range = h - l
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    
    if total_range == 0 or body == 0:
        return False
    
    return upper_wick >= body * 2 and lower_wick <= total_range * 0.3


def is_expansion_candle(df: pd.DataFrame, index: int, threshold: float = 0.80) -> bool:
    """Body is >= threshold % of total range (e.g., 80%). Signals strong directional conviction."""
    o, h, l, c = df['Open'].iloc[index], df['High'].iloc[index], df['Low'].iloc[index], df['Close'].iloc[index]
    
    total_range = h - l
    body = abs(c - o)
    
    if total_range == 0:
        return False
    
    return (body / total_range) >= threshold
