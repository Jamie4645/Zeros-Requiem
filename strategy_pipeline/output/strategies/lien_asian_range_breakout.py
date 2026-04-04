"""
Asian Session Range Breakout (Lien)
====================================
Source: "Day Trading and Swing Trading the Currency Market" - Kathy Lien
        Channel Breakout Strategy, Chapter 9 (both editions)

Core idea: The Asian session (Tokyo close ~04:00 GMT to London open ~07:00 GMT)
forms tight consolidation ranges in major forex pairs. When London opens,
the influx of volume breaks the Asian range — trade the first decisive
breakout in either direction with stops inside the range.

This is one of the most reliable intraday patterns in forex: Asian
consolidation → London expansion. 70% of the European session range
and 80% of the US range occurs during the US/Europe overlap, making
the London breakout the highest-probability session trade.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Asian Session Range Breakout",
    "category": "session_breakout",
    "source_book": "Day Trading and Swing Trading the Currency Market",
    "source_traders": ["Kathy Lien"],
    "timeframe": "15min",
    "markets": ["forex"],
    "confidence": 0.70,
}

DEFAULT_PARAMS = {
    "asian_start_hour": 0,    # Asian range start (GMT)
    "asian_end_hour": 6,      # Asian range end (GMT) — before London
    "entry_offset_pips": 10,  # Pips beyond range for entry
    "stop_inside_pips": 10,   # Stop placed this many pips inside the range
    "tp_multiplier": 2.0,     # Take profit = tp_multiplier * channel range
    "pip_size": 0.0001,       # 0.0001 for most FX, 0.01 for JPY
    "min_range_pips": 20,     # Minimum range size to avoid noise (pips)
    "max_range_pips": 80,     # Maximum range — too wide means no breakout edge
    "atr_period": 14,         # ATR period
    "session_end_hour": 16,   # Close any remaining position by this GMT hour
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Compute the Asian session range for each trading day."""
    atr_period = _p(params, "atr_period")
    asian_start = _p(params, "asian_start_hour")
    asian_end = _p(params, "asian_end_hour")
    pip_size = _p(params, "pip_size")
    min_range = _p(params, "min_range_pips")
    max_range = _p(params, "max_range_pips")

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    idx = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
    hours = idx.hour

    # Identify Asian session bars
    df["in_asian"] = (hours >= asian_start) & (hours < asian_end)

    # Compute daily Asian range
    asian_high = df["high"].where(df["in_asian"]).groupby(idx.date).transform("max")
    asian_low = df["low"].where(df["in_asian"]).groupby(idx.date).transform("min")

    df["asian_high"] = asian_high.ffill()
    df["asian_low"] = asian_low.ffill()
    df["asian_range_pips"] = (df["asian_high"] - df["asian_low"]) / pip_size

    # Range quality filter
    df["range_valid"] = (
        (df["asian_range_pips"] >= min_range) &
        (df["asian_range_pips"] <= max_range)
    )

    return df


def entry_signal(df, params=None):
    """
    Long entry: price breaks above the Asian session high after the
    Asian session ends (London open). Range must be valid width.
    """
    if "asian_high" not in df.columns:
        df = compute_indicators(df, params)

    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")
    asian_end = _p(params, "asian_end_hour")

    idx = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
    after_asian = idx.hour >= asian_end

    long_breakout = (
        (df["close"] > df["asian_high"] + offset * pip_size) &
        after_asian &
        df["range_valid"] &
        df["atr"].notna()
    )

    return long_breakout


def exit_signal(df, params=None):
    """Exit at end of session or if price reverses to opposite side of range."""
    if "asian_low" not in df.columns:
        df = compute_indicators(df, params)

    session_end = _p(params, "session_end_hour")

    idx = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)

    end_of_session = idx.hour >= session_end

    # Reversal: price breaks back below Asian low (false breakout)
    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")
    reversal = df["close"] < (df["asian_low"] - offset * pip_size)

    return end_of_session | reversal


def get_stop_loss(df, i, params=None):
    """Stop placed inside the Asian range (below upper boundary for longs)."""
    pip_size = _p(params, "pip_size")
    stop_inside = _p(params, "stop_inside_pips")

    if "asian_high" in df.columns:
        range_high = df["asian_high"].iloc[i]
        return range_high - stop_inside * pip_size

    entry_price = df["close"].iloc[i]
    atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
    return entry_price - 2.0 * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing: risk% of equity / dollar risk per unit."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """Take profit at 2x the Asian range width from entry."""
    risk = abs(entry_price - stop_loss)
    if direction == "long":
        return entry_price + 2.0 * risk
    return entry_price - 2.0 * risk
