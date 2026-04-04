"""
Time-Series Momentum on Copper (Chan)
======================================
Source: "Algorithmic Trading" - Ernest Chan, Chapter 5 (Strategy #17)

Core idea: If copper's trailing return over a lookback period is positive,
go long. If negative, go short. Rebalance at the end of each holding period.

Chan found shorter lookbacks work better for commodities (40 days vs 250
for bonds) because commodity supply-demand cycles are faster. Copper showed
APR 18%, Sharpe 1.05 with symmetric 40/40 lookback/hold parameters.

Applicable to any trending commodity: Gold, Silver, Oil, Copper, etc.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Time-Series Momentum (Copper/Commodity)",
    "category": "momentum",
    "source_book": "Algorithmic Trading",
    "source_traders": ["Ernest Chan"],
    "timeframe": "daily",
    "markets": ["commodities", "futures"],
    "confidence": 0.70,
}

DEFAULT_PARAMS = {
    "lookback": 40,         # Return lookback period (days)
    "hold_period": 40,      # Holding period before reassessment (days)
    "atr_period": 14,       # ATR for stop and sizing
    "atr_stop_mult": 2.5,   # Stop distance in ATR multiples
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Compute trailing return and ATR."""
    lookback = _p(params, "lookback")
    atr_period = _p(params, "atr_period")

    df["trailing_return"] = df["close"].pct_change(lookback)

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # Rebalance signal: true every hold_period bars
    hold = _p(params, "hold_period")
    df["bar_index"] = range(len(df))
    df["rebalance"] = (df["bar_index"] % hold) == 0

    return df


def entry_signal(df, params=None):
    """
    Entry: trailing return over lookback period is positive AND
    it's a rebalance bar. Binary signal — fully long or no position.
    """
    if "trailing_return" not in df.columns:
        df = compute_indicators(df, params)

    positive_momentum = df["trailing_return"] > 0
    valid = df["atr"].notna() & df["trailing_return"].notna()
    rebalance = df["rebalance"]

    return positive_momentum & valid & rebalance


def exit_signal(df, params=None):
    """
    Exit: trailing return turns negative on a rebalance bar,
    or held for the full holding period and momentum has reversed.
    """
    if "trailing_return" not in df.columns:
        df = compute_indicators(df, params)

    negative_momentum = df["trailing_return"] <= 0
    rebalance = df["rebalance"]

    return negative_momentum & rebalance


def get_stop_loss(df, i, params=None):
    """Stop loss at entry price minus atr_stop_mult * ATR."""
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
    entry_price = df["close"].iloc[i]
    return entry_price - atr_mult * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing: risk% of equity / dollar risk per unit."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Time-series momentum rides trends — no fixed take-profit.
    Exit handled by the exit_signal on rebalance dates.
    """
    return None
