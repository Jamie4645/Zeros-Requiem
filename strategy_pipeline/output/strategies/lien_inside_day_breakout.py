"""
Inside Day Breakout Play (Lien)
================================
Source: "Day Trading and Swing Trading the Currency Market" - Kathy Lien
        (Both 1st and 2nd editions, Chapter 9)

Core idea: Identify 2+ consecutive inside days (daily range contained
within prior day's range) — a sign of volatility compression. Trade
the breakout in either direction with a stop-and-reverse mechanism
for false breakouts. Target 2x risk.

Inside days signal coiled energy. The more consecutive inside days,
the more explosive the eventual breakout. Works on all forex pairs
but best on tighter-range pairs (EUR/GBP, USD/CAD, EUR/CHF).
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Inside Day Breakout",
    "category": "volatility_breakout",
    "source_book": "Day Trading and Swing Trading the Currency Market",
    "source_traders": ["Kathy Lien"],
    "timeframe": "daily",
    "markets": ["forex", "commodities", "indices"],
    "confidence": 0.75,
}

DEFAULT_PARAMS = {
    "min_inside_days": 2,      # Minimum consecutive inside days required
    "entry_offset_pips": 10,   # Pips beyond inside day high/low for entry
    "tp_multiplier": 2.0,      # Take profit = tp_multiplier * risk
    "pip_size": 0.0001,        # 0.0001 for most FX, 0.01 for JPY, 0.1 for Gold
    "atr_period": 14,          # ATR period for fallback
    "use_atr_stops": True,     # If True, use ATR-based stops instead of fixed pip
    "atr_stop_mult": 1.5,      # ATR multiple for stop when use_atr_stops=True
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Detect inside days and compute breakout levels."""
    atr_period = _p(params, "atr_period")
    min_inside = _p(params, "min_inside_days")

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # Inside day: current high < prior high AND current low > prior low
    df["inside_day"] = (df["high"] < df["high"].shift(1)) & (df["low"] > df["low"].shift(1))

    # Count consecutive inside days
    df["inside_streak"] = 0
    streak = 0
    streaks = []
    for is_inside in df["inside_day"]:
        if is_inside:
            streak += 1
        else:
            streak = 0
        streaks.append(streak)
    df["inside_streak"] = streaks

    # Breakout levels: high and low of the most recent inside day
    df["inside_high"] = df["high"].where(df["inside_day"]).ffill()
    df["inside_low"] = df["low"].where(df["inside_day"]).ffill()

    # Signal readiness: had enough inside days to set up
    df["setup_ready"] = df["inside_streak"].shift(1) >= min_inside

    return df


def entry_signal(df, params=None):
    """
    Long entry: price closes above the inside day high after 2+
    consecutive inside days. The breakout bar itself is the entry.
    """
    if "setup_ready" not in df.columns:
        df = compute_indicators(df, params)

    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")

    # Breakout above inside day high
    long_breakout = (
        df["setup_ready"] &
        (df["close"] > df["inside_high"].shift(1) + offset * pip_size) &
        df["atr"].notna()
    )

    return long_breakout


def exit_signal(df, params=None):
    """
    Exit on stop-and-reverse: if price closes below the inside day low
    after a long entry, it's a false breakout — exit (and potentially reverse).
    """
    if "inside_low" not in df.columns:
        df = compute_indicators(df, params)

    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")

    # Price breaks below the opposite side of the inside day range
    exit_on_reversal = df["close"] < (df["inside_low"].shift(1) - offset * pip_size)

    return exit_on_reversal


def get_stop_loss(df, i, params=None):
    """
    Stop at the opposite extreme of the inside day range (+ offset).
    For longs: stop below the inside day low.
    If use_atr_stops is True, use ATR-based stop instead.
    """
    use_atr = _p(params, "use_atr_stops")

    if use_atr:
        atr_mult = _p(params, "atr_stop_mult")
        atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
        entry_price = df["close"].iloc[i]
        return entry_price - atr_mult * atr_val

    pip_size = _p(params, "pip_size")
    offset = _p(params, "entry_offset_pips")
    inside_low = df["inside_low"].iloc[i] if "inside_low" in df.columns else df["low"].iloc[i]
    return inside_low - offset * pip_size


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing: risk% of equity / dollar risk per unit."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """Take profit at 2x risk (Lien's standard 1:2 R:R)."""
    risk = abs(entry_price - stop_loss)
    if direction == "long":
        return entry_price + 2.0 * risk
    return entry_price - 2.0 * risk
