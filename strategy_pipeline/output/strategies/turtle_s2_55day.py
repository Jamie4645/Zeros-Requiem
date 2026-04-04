"""
Turtle System 2 — 55-Day Breakout (Dennis/Eckhardt)
=====================================================
Source: "The Complete Turtle Trader" - Michael Covel, Chapter 5
        Original Turtle Trading rules (publicly released 2003)

Core idea: Buy when price makes a new 55-day high (11-week breakout).
Exit on 20-day opposing channel. Stop at 2*ATR. NO FILTER RULE — every
breakout signal is taken regardless of the previous outcome.

S2 is simpler and more robust than S1 (which has a filter rule that
can cause missed entries). Jerry Parker's Chesapeake Capital ($1B+ AUM)
evolved primarily from S2 logic with a 52-week moving average overlay.

This is the "catch every big trend" system. It trades less frequently
than S1 but catches moves that S1's filter would skip.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Turtle System 2 (55-Day Breakout)",
    "category": "trend_following",
    "source_book": "The Complete Turtle Trader",
    "source_traders": ["Richard Dennis", "William Eckhardt", "Jerry Parker"],
    "timeframe": "daily",
    "markets": ["futures", "commodities", "forex", "indices"],
    "confidence": 0.85,
}

DEFAULT_PARAMS = {
    "entry_lookback": 55,    # 55-day Donchian channel for entries
    "exit_lookback": 20,     # 20-day Donchian channel for exits
    "atr_period": 20,        # ATR period (Turtles used 20-day)
    "atr_stop_mult": 2.0,    # Stop distance: 2 * ATR
    "pyramid_atr_mult": 1.0, # Add unit every 1N (ATR) move in favor
    "max_units": 5,          # Maximum pyramid units per market
    "risk_per_unit": 0.02,   # Risk 2% of equity per unit
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add 55-day and 20-day Donchian channels plus ATR."""
    entry_lb = _p(params, "entry_lookback")
    exit_lb = _p(params, "exit_lookback")
    atr_period = _p(params, "atr_period")

    # Entry channel (55-day)
    df["dc_upper_55"] = df["high"].rolling(entry_lb).max()
    df["dc_lower_55"] = df["low"].rolling(entry_lb).min()

    # Exit channel (20-day)
    df["dc_exit_lower_20"] = df["low"].rolling(exit_lb).min()
    df["dc_exit_upper_20"] = df["high"].rolling(exit_lb).max()

    # ATR (N in Turtle terminology)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    return df


def entry_signal(df, params=None):
    """
    Long entry: close exceeds the 55-day high channel.
    NO FILTER — every S2 breakout is taken unconditionally.
    """
    if "dc_upper_55" not in df.columns:
        df = compute_indicators(df, params)

    long_signal = df["close"] > df["dc_upper_55"].shift(1)
    valid = df["atr"].notna()

    return long_signal & valid


def exit_signal(df, params=None):
    """
    Exit long: close drops below the 20-day low channel.
    The 2N stop is handled separately via get_stop_loss.
    """
    if "dc_exit_lower_20" not in df.columns:
        df = compute_indicators(df, params)

    exit_on_channel = df["close"] < df["dc_exit_lower_20"].shift(1)

    return exit_on_channel


def get_stop_loss(df, i, params=None):
    """
    Stop loss at entry price minus 2N (2 * ATR).
    When pyramiding, all stops move to the new unit's 2N level.
    """
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns else 0
    entry_price = df["close"].iloc[i]
    return entry_price - atr_mult * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """
    Turtle N-based position sizing:
    Units = (Equity * Risk%) / (2N * Dollar_Per_Point)
    Simplified: Units = (Equity * Risk%) / Dollar_Risk
    """
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Turtles do not use fixed take-profit targets.
    They ride trends and exit on the 20-day channel breakout.
    """
    return None
