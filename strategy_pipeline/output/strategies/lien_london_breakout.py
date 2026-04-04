"""
London Session Breakout — "Waiting for the Real Deal" (Lien)
=============================================================
Source: "Day Trading and Swing Trading the Currency Market" - Kathy Lien
        (Both 1st and 2nd editions, Chapter 9)

Core idea: UK/European dealers hunt stops during the Frankfurt-London
power hour (1:00-2:00 AM NY / 06:00-07:00 GMT). The initial move at
London open is often a fake-out. Wait for the fake move (≥25 pips past
range), then trade the reversal through the opposite side of the range.

GBP/USD specific. The strategy exploits institutional stop-hunting
behavior at the London open — one of the most reliable intraday patterns.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "London Session Breakout (Real Deal)",
    "category": "session_breakout",
    "source_book": "Day Trading and Swing Trading the Currency Market",
    "source_traders": ["Kathy Lien"],
    "timeframe": "15min",
    "markets": ["forex"],
    "confidence": 0.70,
}

DEFAULT_PARAMS = {
    "range_start_hour": 6,     # Range start hour (GMT) — Frankfurt open
    "range_end_hour": 7,       # Range end hour (GMT) — London open
    "min_fake_pips": 25,       # Minimum fake-out move beyond range (pips)
    "entry_offset_pips": 10,   # Entry offset beyond range high/low (pips)
    "stop_pips": 20,           # Fixed stop loss in pips
    "tp_multiplier": 2.0,      # Take profit = tp_multiplier * stop
    "pip_size": 0.0001,        # Pip size (0.0001 for most pairs, 0.01 for JPY)
    "atr_period": 14,          # ATR period for fallback sizing
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """
    Compute the Frankfurt-London power hour range and detect fake-outs.
    Expects df to have a DatetimeIndex or 'datetime' column with timezone info.
    """
    atr_period = _p(params, "atr_period")
    range_start = _p(params, "range_start_hour")
    range_end = _p(params, "range_end_hour")
    pip_size = _p(params, "pip_size")
    min_fake = _p(params, "min_fake_pips")

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # Detect the power-hour range for each day
    idx = pd.DatetimeIndex(df.index) if not isinstance(df.index, pd.DatetimeIndex) else df.index
    hours = idx.hour
    dates = idx.date

    df["in_range"] = (hours >= range_start) & (hours < range_end)
    df["_date"] = dates

    range_high = df["high"].where(df["in_range"]).groupby(df["_date"]).transform("max")
    range_low = df["low"].where(df["in_range"]).groupby(df["_date"]).transform("min")
    open_price = df["open"].where(hours == range_start).groupby(df["_date"]).transform("first")

    df["range_high"] = range_high.ffill()
    df["range_low"] = range_low.ffill()
    df["range_open"] = open_price.ffill()

    df["fake_low"] = df["low"] < (df["range_low"] - min_fake * pip_size)
    df["fake_high"] = df["high"] > (df["range_high"] + min_fake * pip_size)

    df["had_fake_low"] = df["fake_low"].groupby(df["_date"]).cummax()
    df["had_fake_high"] = df["fake_high"].groupby(df["_date"]).cummax()
    df.drop(columns=["_date"], inplace=True)

    return df


def entry_signal(df, params=None):
    """
    Long entry: After a fake-out LOW (stop hunt down), price reverses
    and breaks above range_high + entry_offset. This is the "real deal."
    """
    if "range_high" not in df.columns:
        df = compute_indicators(df, params)

    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")
    range_end = _p(params, "range_end_hour")

    idx = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
    after_range = idx.hour >= range_end

    long_signal = (
        df["had_fake_low"] &
        (df["close"] > df["range_high"] + offset * pip_size) &
        after_range &
        df["atr"].notna()
    )

    return long_signal


def exit_signal(df, params=None):
    """Exit at end of session (approximated as 16:00 GMT)."""
    if "range_high" not in df.columns:
        df = compute_indicators(df, params)

    idx = pd.DatetimeIndex(df.index) if not isinstance(df.index, pd.DatetimeIndex) else df.index

    end_of_session = pd.Series(idx.hour >= 16, index=df.index)

    return end_of_session


def get_stop_loss(df, i, params=None):
    """Fixed pip-based stop loss below entry."""
    stop_pips = _p(params, "stop_pips")
    pip_size = _p(params, "pip_size")
    entry_price = df["close"].iloc[i]
    return entry_price - stop_pips * pip_size


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing: risk% of equity / dollar risk per unit."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """Take profit at 2x risk (1:2 R:R). Close half at TP, trail remainder."""
    risk = abs(entry_price - stop_loss)
    if direction == "long":
        return entry_price + 2.0 * risk
    return entry_price - 2.0 * risk
