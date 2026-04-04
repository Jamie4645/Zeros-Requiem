"""
Seykota EMA Trend Following Strategy
======================================
Source: "Market Wizards" - Ed Seykota interview
        Seykota's Trading Tribe principles

Core idea: Follow the trend using exponential moving average crossovers.
Short EMA crossing above long EMA in the direction of price confirms trend.
Trail a 3*ATR stop to let winners run.

Seykota is one of the most successful systematic traders ever, reportedly
compounding at 60%+ annually over decades. His approach emphasizes
simplicity: "The trend is your friend until the end when it bends."
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Seykota EMA Trend Following",
    "category": "trend_following",
    "source_book": "Market Wizards",
    "source_traders": ["Ed Seykota"],
    "timeframe": "daily",
    "markets": ["futures", "commodities", "forex", "indices"],
    "confidence": 0.80,
}

DEFAULT_PARAMS = {
    "short_ema": 10,        # Fast EMA period
    "long_ema": 30,         # Slow EMA period
    "atr_period": 14,       # ATR calculation period
    "atr_trail_mult": 3.0,  # Trailing stop in ATR multiples
    "atr_stop_mult": 3.0,   # Initial stop in ATR multiples
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add EMAs and ATR to the dataframe."""
    short_p = _p(params, "short_ema")
    long_p = _p(params, "long_ema")
    atr_period = _p(params, "atr_period")

    df["ema_short"] = df["close"].ewm(span=short_p, adjust=False).mean()
    df["ema_long"] = df["close"].ewm(span=long_p, adjust=False).mean()

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # EMA cross detection
    df["ema_cross_up"] = (
        (df["ema_short"] > df["ema_long"]) &
        (df["ema_short"].shift(1) <= df["ema_long"].shift(1))
    )

    # Trailing stop reference: highest close since last entry signal
    # (approximation for the series-based runner)
    df["trail_stop"] = df["close"] - _p(params, "atr_trail_mult") * df["atr"]

    return df


def entry_signal(df, params=None):
    """
    Entry: Short EMA crosses above long EMA AND price is above both EMAs.
    This confirms trend momentum is established.
    """
    if "ema_short" not in df.columns:
        df = compute_indicators(df, params)

    cross_up = df["ema_cross_up"]
    price_above = (df["close"] > df["ema_short"]) & (df["close"] > df["ema_long"])
    valid = df["atr"].notna()

    return cross_up & price_above & valid


def exit_signal(df, params=None):
    """
    Exit on either:
    1. EMA cross reversal (short EMA crosses below long EMA)
    2. Price closes below the trailing stop (close - 3*ATR from recent high)
    """
    if "ema_short" not in df.columns:
        df = compute_indicators(df, params)

    # EMA cross reversal
    ema_cross_down = (
        (df["ema_short"] < df["ema_long"]) &
        (df["ema_short"].shift(1) >= df["ema_long"].shift(1))
    )

    # Price below trailing stop approximation (close below longer EMA - ATR buffer)
    atr_mult = _p(params, "atr_trail_mult")
    below_trail = df["close"] < (df["ema_long"] - atr_mult * df["atr"])

    return ema_cross_down | below_trail


def get_stop_loss(df, i, params=None):
    """Initial stop at entry price minus 3*ATR, or below the long EMA."""
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
    entry_price = df["close"].iloc[i]
    ema_long_val = df["ema_long"].iloc[i] if "ema_long" in df.columns else entry_price

    # More conservative of the two
    atr_stop = entry_price - atr_mult * atr_val
    ema_stop = ema_long_val - 0.5 * atr_val

    return max(atr_stop, ema_stop)


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based position sizing: risk% of equity divided by dollar risk per unit."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Seykota did not use fixed take-profit. He let trends run and exited
    on trailing stops or EMA reversals. Returns None.
    """
    return None
