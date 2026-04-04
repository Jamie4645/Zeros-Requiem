"""
Schwartz Moving Average Pullback Strategy
==========================================
Source: "Market Wizards" / "The New Market Wizards" - Marty Schwartz interview

Core idea: In a confirmed uptrend (10 EMA > 20 EMA), wait for price to
pull back to the 10 EMA, then enter when it bounces (closes back above).
Exit when price closes below the 10 EMA.

Schwartz famously said "I always use the 10-day exponential moving average
as my line in the sand." He used this across S&P futures and other markets.

This is a mean-reversion-within-trend strategy: the trend provides
direction, the pullback provides entry timing.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Schwartz MA Pullback (10/20 EMA)",
    "category": "mean_reversion_trend",
    "source_book": "Market Wizards / The New Market Wizards",
    "source_traders": ["Marty Schwartz"],
    "timeframe": "daily",
    "markets": ["indices", "futures", "forex"],
    "confidence": 0.75,
}

DEFAULT_PARAMS = {
    "fast_ema": 10,         # Schwartz's "line in the sand"
    "slow_ema": 20,         # Trend confirmation EMA
    "atr_period": 14,       # ATR for stop placement
    "swing_lookback": 10,   # Bars to look back for swing low (stop)
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add EMAs, ATR, and pullback detection columns."""
    fast = _p(params, "fast_ema")
    slow = _p(params, "slow_ema")
    atr_period = _p(params, "atr_period")
    swing_lb = _p(params, "swing_lookback")

    df["ema_fast"] = df["close"].ewm(span=fast, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=slow, adjust=False).mean()

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # Uptrend: fast EMA above slow EMA
    df["uptrend"] = df["ema_fast"] > df["ema_slow"]

    # Pullback: low touched or went below fast EMA
    df["touched_ema"] = df["low"] <= df["ema_fast"]

    # Bounce: after touching EMA, close is back above it
    df["bounce"] = df["touched_ema"].shift(1) & (df["close"] > df["ema_fast"])

    # Swing low for stop placement
    df["swing_low"] = df["low"].rolling(swing_lb).min()

    return df


def entry_signal(df, params=None):
    """
    Entry: Uptrend confirmed (10 EMA > 20 EMA), price pulled back to
    touch the 10 EMA on the previous bar, and now closes back above it.
    """
    if "ema_fast" not in df.columns:
        df = compute_indicators(df, params)

    valid = df["atr"].notna()
    return df["uptrend"] & df["bounce"] & valid


def exit_signal(df, params=None):
    """
    Exit: Close below the 10 EMA (Schwartz's primary exit rule).
    """
    if "ema_fast" not in df.columns:
        df = compute_indicators(df, params)

    return df["close"] < df["ema_fast"]


def get_stop_loss(df, i, params=None):
    """
    Stop below the recent swing low. Schwartz placed stops
    at logical support — the lowest low of the pullback.
    """
    swing_lb = _p(params, "swing_lookback")
    start = max(0, i - swing_lb)
    swing_low = df["low"].iloc[start:i + 1].min()

    # Add a small ATR buffer below the swing low
    atr_val = df["atr"].iloc[i] if "atr" in df.columns and pd.notna(df["atr"].iloc[i]) else 0
    return swing_low - 0.2 * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing: risk% of capital / distance to stop."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Schwartz exited on the EMA, not on fixed targets.
    Returns None — exit_signal handles all exits.
    """
    return None
