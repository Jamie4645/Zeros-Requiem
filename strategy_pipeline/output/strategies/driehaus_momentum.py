"""
Driehaus Growth Momentum Strategy (Simplified)
================================================
Source: "The New Market Wizards" - Richard Driehaus interview

Core idea: Driehaus was the pioneer of momentum investing. He believed
in buying stocks making new highs with strong relative strength, not
waiting for pullbacks. "I would much rather buy a stock at $60 that is
on its way to $100 than buy a stock at $40 that was once at $60."

Entry criteria (simplified without fundamental data):
1. Price making new 52-week (252-day) high
2. Relative strength in top 20% (price performance vs lookback)
3. Price above all key moving averages (20, 50, 200 day)

Exit criteria:
1. Relative strength drops below 50th percentile
2. Price closes below 50-day MA

This version uses price-only momentum as a proxy since we don't
have earnings/revenue data in the backtester.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Driehaus Growth Momentum",
    "category": "momentum",
    "source_book": "The New Market Wizards",
    "source_traders": ["Richard Driehaus"],
    "timeframe": "daily",
    "markets": ["equities", "indices", "etfs"],
    "confidence": 0.70,
}

DEFAULT_PARAMS = {
    "high_lookback": 252,   # 52-week (252 trading days) high
    "rs_lookback": 126,     # 6-month relative strength period
    "rs_entry_pct": 0.80,   # Top 20% = 80th percentile threshold
    "rs_exit_pct": 0.50,    # Below 50th percentile = exit
    "ma_short": 20,         # Short-term MA
    "ma_mid": 50,           # Medium-term MA (also exit trigger)
    "ma_long": 200,         # Long-term MA
    "atr_period": 14,
    "atr_stop_mult": 2.5,
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add momentum, relative strength, and MA indicators."""
    high_lb = _p(params, "high_lookback")
    rs_lb = _p(params, "rs_lookback")
    ma_short = _p(params, "ma_short")
    ma_mid = _p(params, "ma_mid")
    ma_long = _p(params, "ma_long")
    atr_period = _p(params, "atr_period")

    # Moving averages
    df["ma_20"] = df["close"].rolling(ma_short).mean()
    df["ma_50"] = df["close"].rolling(ma_mid).mean()
    df["ma_200"] = df["close"].rolling(ma_long).mean()

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # 52-week high detection
    df["high_252"] = df["high"].rolling(high_lb).max()
    df["new_high"] = df["high"] >= df["high_252"]

    # Relative strength: rate of change over rs_lookback period
    # Normalized to a 0-1 scale using rolling rank
    df["roc"] = df["close"].pct_change(rs_lb)
    df["rs_rank"] = df["roc"].rolling(high_lb, min_periods=rs_lb).rank(pct=True)

    # Price above all MAs
    df["above_all_mas"] = (
        (df["close"] > df["ma_20"]) &
        (df["close"] > df["ma_50"]) &
        (df["close"] > df["ma_200"])
    )

    return df


def entry_signal(df, params=None):
    """
    Entry: New 52-week high + relative strength in top 20% + above all MAs.
    This captures Driehaus's "buy high, sell higher" philosophy.
    """
    if "new_high" not in df.columns:
        df = compute_indicators(df, params)

    rs_entry = _p(params, "rs_entry_pct")
    valid = df["atr"].notna() & df["rs_rank"].notna()

    signal = (
        df["new_high"] &
        (df["rs_rank"] >= rs_entry) &
        df["above_all_mas"] &
        valid
    )

    return signal


def exit_signal(df, params=None):
    """
    Exit when momentum deteriorates:
    1. Relative strength drops below 50th percentile, OR
    2. Price closes below 50-day MA
    """
    if "rs_rank" not in df.columns:
        df = compute_indicators(df, params)

    rs_exit = _p(params, "rs_exit_pct")

    rs_weak = df["rs_rank"] < rs_exit
    below_50ma = df["close"] < df["ma_50"]

    return rs_weak | below_50ma


def get_stop_loss(df, i, params=None):
    """Stop at entry price minus 2.5*ATR, or below 50-day MA."""
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns and pd.notna(df["atr"].iloc[i]) else 0
    entry_price = df["close"].iloc[i]
    ma_50 = df["ma_50"].iloc[i] if "ma_50" in df.columns and pd.notna(df["ma_50"].iloc[i]) else 0

    atr_stop = entry_price - atr_mult * atr_val
    ma_stop = ma_50 - 0.5 * atr_val  # Small buffer below the 50 MA

    # Use the higher (tighter) stop
    return max(atr_stop, ma_stop)


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Driehaus rode momentum, he did not use fixed targets.
    Exit is handled by exit_signal (RS deterioration or MA break).
    """
    return None
