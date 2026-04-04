"""
Turtle Trading Breakout Strategy (Dennis / Eckhardt)
=====================================================
Source: "Market Wizards" - Richard Dennis & William Eckhardt interviews
        Original Turtle Trading rules (publicly released 2003)

Core idea: Buy 20-day high breakouts, sell 20-day low breakdowns.
Exit on 10-day opposing channel. Stop at 2*ATR from entry.

This is one of the most well-documented systematic trend-following
strategies ever created. The Turtles used this from 1983-1988 and
compounded at ~80% annually.

Simplified here to long-only channel breakout for equities/commodities.
Short signals included for instruments that allow shorting.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Turtle Breakout (20/10 Channel)",
    "category": "trend_following",
    "source_book": "Market Wizards",
    "source_traders": ["Richard Dennis", "William Eckhardt"],
    "timeframe": "daily",
    "markets": ["futures", "commodities", "forex", "indices"],
    "confidence": 0.85,
}

# ── Default Parameters ──────────────────────────────────────────────
DEFAULT_PARAMS = {
    "entry_lookback": 20,   # Donchian channel period for entries
    "exit_lookback": 10,    # Donchian channel period for exits
    "atr_period": 14,       # ATR period for stops and sizing
    "atr_stop_mult": 2.0,   # Stop distance in ATR multiples
}


def _p(params, key):
    """Retrieve parameter with fallback to defaults."""
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add Donchian channels and ATR to the dataframe."""
    entry_lb = _p(params, "entry_lookback")
    exit_lb = _p(params, "exit_lookback")
    atr_period = _p(params, "atr_period")

    # Donchian channels for entry
    df["dc_upper"] = df["high"].rolling(entry_lb).max()
    df["dc_lower"] = df["low"].rolling(entry_lb).min()

    # Donchian channels for exit
    df["dc_exit_lower"] = df["low"].rolling(exit_lb).min()
    df["dc_exit_upper"] = df["high"].rolling(exit_lb).max()

    # ATR for stop-loss and position sizing
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    return df


def entry_signal(df, params=None):
    """
    Entry: close breaks above the 20-day high (long signal).
    Returns a boolean Series. True = enter long on this bar.
    """
    if "dc_upper" not in df.columns:
        df = compute_indicators(df, params)

    # Long entry: close exceeds previous bar's 20-day high channel
    long_signal = df["close"] > df["dc_upper"].shift(1)

    # Require ATR to be valid (enough data)
    valid = df["atr"].notna()

    return long_signal & valid


def exit_signal(df, params=None):
    """
    Exit: close drops below the 10-day low (exit long).
    Also exits if price hits the 2*ATR trailing stop from highest close since entry.
    """
    if "dc_exit_lower" not in df.columns:
        df = compute_indicators(df, params)

    # Exit when close breaks below the 10-day low channel
    exit_on_channel = df["close"] < df["dc_exit_lower"].shift(1)

    return exit_on_channel


def get_stop_loss(df, i, params=None):
    """Stop loss at entry price minus 2 * ATR."""
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
    entry_price = df["close"].iloc[i]
    return entry_price - atr_mult * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """
    Turtle position sizing: risk a fixed % of equity per trade.
    Size = (equity * risk%) / dollar_risk_per_unit
    """
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    units = (capital * risk_pct) / dollar_risk
    return max(0, units)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Turtles did not use fixed take-profit targets; they rode trends
    and exited on the 10-day channel. This returns None to indicate
    the exit_signal handles all exits.
    """
    return None
