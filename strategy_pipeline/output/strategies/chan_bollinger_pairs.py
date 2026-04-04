"""
Bollinger Band Mean Reversion on Pairs (Chan)
===============================================
Source: "Algorithmic Trading" - Ernest Chan, Chapter 2 (Strategy #3)

Core idea: Form a price spread between two cointegrated assets using a
dynamic hedge ratio (rolling OLS). Enter when the spread breaches the
Bollinger Band (1 standard deviation) and exit when it reverts to the
mean. Position is binary (full size), not linear-scaled.

Applied to GLD-USO pair in Chan's book: APR 17.8%, Sharpe 0.96 (2007-2012).
Better APR than the linear Z-score version on the same pair because
Bollinger bands capture larger dislocations with higher conviction.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Bollinger Band Pairs Mean Reversion",
    "category": "mean_reversion",
    "source_book": "Algorithmic Trading",
    "source_traders": ["Ernest Chan"],
    "timeframe": "daily",
    "markets": ["etfs", "commodities", "equities"],
    "confidence": 0.70,
}

DEFAULT_PARAMS = {
    "lookback": 20,          # Rolling window for mean/std (or half-life)
    "entry_std": 1.0,        # Enter when spread exceeds 1.0 std from mean
    "exit_std": 0.0,         # Exit when spread crosses the mean
    "hedge_lookback": 60,    # Rolling OLS hedge ratio lookback
    "atr_period": 14,        # ATR for stop placement
    "atr_stop_mult": 3.0,    # Stop distance in ATR multiples
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """
    Compute the spread, Bollinger Bands, and Z-score.

    If 'close_x' column exists, compute a two-asset spread.
    Otherwise, apply Bollinger Bands directly to 'close' as a
    single-asset mean reversion signal.
    """
    lookback = _p(params, "lookback")
    entry_std = _p(params, "entry_std")
    hedge_lb = _p(params, "hedge_lookback")
    atr_period = _p(params, "atr_period")

    if "close_x" in df.columns:
        # Two-asset mode: compute rolling hedge ratio and spread
        y = df["close"]
        x = df["close_x"]

        # Simple rolling hedge ratio via ratio (simplified OLS)
        df["hedge_ratio"] = y.rolling(hedge_lb).corr(x) * (
            y.rolling(hedge_lb).std() / x.rolling(hedge_lb).std()
        )
        df["hedge_ratio"] = df["hedge_ratio"].ffill()

        df["spread"] = y - df["hedge_ratio"] * x
    else:
        # Single-asset mode: spread is just the price
        df["spread"] = df["close"]

    # Bollinger Bands on the spread
    df["spread_mean"] = df["spread"].rolling(lookback).mean()
    df["spread_std"] = df["spread"].rolling(lookback).std()

    df["bb_upper"] = df["spread_mean"] + entry_std * df["spread_std"]
    df["bb_lower"] = df["spread_mean"] - entry_std * df["spread_std"]

    df["z_score"] = (df["spread"] - df["spread_mean"]) / df["spread_std"].replace(0, np.nan)

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    return df


def entry_signal(df, params=None):
    """
    Long spread: enter when spread drops below lower Bollinger Band
    (Z-score < -entry_std). Binary position — full size.
    """
    if "z_score" not in df.columns:
        df = compute_indicators(df, params)

    entry_std = _p(params, "entry_std")
    valid = df["atr"].notna() & df["z_score"].notna()

    long_signal = (df["z_score"] < -entry_std) & valid

    return long_signal


def exit_signal(df, params=None):
    """
    Exit: spread crosses above the mean (Z-score > exit_std, default 0).
    """
    if "z_score" not in df.columns:
        df = compute_indicators(df, params)

    exit_std = _p(params, "exit_std")

    exit_on_reversion = df["z_score"] > exit_std

    return exit_on_reversion


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
    Mean reversion: exit when spread reverts to mean (handled by exit_signal).
    No fixed take-profit target.
    """
    return None
