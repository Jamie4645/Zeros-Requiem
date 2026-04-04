"""
CAN SLIM Cup-with-Handle Breakout (O'Neil)
============================================
Source: "How to Make Money in Stocks" - William O'Neil (4th Edition)
        "Market Wizards" - O'Neil & David Ryan interviews

Core idea: Buy leading growth stocks breaking out of cup-with-handle
base patterns on heavy volume during confirmed market uptrends. Cut
ALL losses at 7-8%. Take profits at 20-25%.

O'Neil's system combines fundamental screening (C, A, N, S, L, I, M)
with technical breakout entries. This implementation focuses on the
codifiable technical components: base pattern detection, volume
confirmation, relative strength filtering, and risk management.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "CAN SLIM Cup-with-Handle Breakout",
    "category": "momentum_growth",
    "source_book": "How to Make Money in Stocks",
    "source_traders": ["William O'Neil", "David Ryan"],
    "timeframe": "daily",
    "markets": ["equities"],
    "confidence": 0.80,
}

DEFAULT_PARAMS = {
    "base_min_weeks": 7,         # Minimum base duration (weeks)
    "base_max_correction": 0.33, # Maximum correction depth (33%)
    "handle_max_correction": 0.12,  # Handle max correction (12%)
    "volume_breakout_mult": 1.5, # Breakout volume must be 1.5x avg (50% above)
    "volume_avg_period": 50,     # Average volume lookback (days)
    "rs_min": 80,                # Minimum relative strength rating
    "max_chase_pct": 0.05,       # Don't chase more than 5% above pivot
    "stop_loss_pct": 0.08,       # 7-8% hard stop loss
    "profit_target_pct": 0.25,   # 20-25% profit target
    "atr_period": 14,            # ATR for supplementary analysis
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """
    Detect cup-with-handle pattern components and breakout conditions.
    """
    vol_period = _p(params, "volume_avg_period")
    atr_period = _p(params, "atr_period")
    base_min = _p(params, "base_min_weeks")
    base_max_corr = _p(params, "base_max_correction")
    handle_max = _p(params, "handle_max_correction")

    # Volume analysis
    df["vol_avg"] = df["volume"].rolling(vol_period).mean() if "volume" in df.columns else 0

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # 50-day and 200-day moving averages (O'Neil's key MAs)
    df["ma_50"] = df["close"].rolling(50).mean()
    df["ma_200"] = df["close"].rolling(200).mean()

    # Relative Strength proxy: % gain over 12 months vs start
    df["rs_proxy"] = df["close"].pct_change(252) * 100 if len(df) > 252 else 0

    # Rolling high for base detection
    base_bars = base_min * 5  # Convert weeks to trading days
    df["rolling_high"] = df["high"].rolling(base_bars, min_periods=base_bars).max()

    # Correction from rolling high
    df["correction_pct"] = (df["rolling_high"] - df["low"]) / df["rolling_high"]

    # Base formation: price has corrected between 12-33% and is now recovering
    df["in_base"] = (
        (df["correction_pct"] >= 0.12) &
        (df["correction_pct"] <= base_max_corr)
    )

    # Handle: small pullback within last 5-20 bars (1-4 weeks)
    recent_high = df["high"].rolling(20).max()
    recent_low = df["low"].rolling(10).min()
    handle_depth = (recent_high - recent_low) / recent_high
    df["handle_valid"] = handle_depth <= handle_max

    # Pivot point: recent high (breakout level)
    df["pivot"] = df["high"].rolling(20).max()

    return df


def entry_signal(df, params=None):
    """
    Entry: price breaks above the pivot (recent high) on volume 50%+
    above the 50-day average. Price must be above 50-day and 200-day MAs.
    """
    if "pivot" not in df.columns:
        df = compute_indicators(df, params)

    vol_mult = _p(params, "volume_breakout_mult")
    max_chase = _p(params, "max_chase_pct")

    breakout = df["close"] > df["pivot"].shift(1)

    volume_confirm = True
    if "volume" in df.columns and "vol_avg" in df.columns:
        volume_confirm = df["volume"] > (df["vol_avg"] * vol_mult)

    above_mas = (df["close"] > df["ma_50"]) & (df["close"] > df["ma_200"])

    not_chasing = df["close"] <= df["pivot"].shift(1) * (1 + max_chase)

    valid = df["atr"].notna() & df["ma_200"].notna()

    return breakout & volume_confirm & above_mas & not_chasing & valid


def exit_signal(df, params=None):
    """
    Exit: price drops 7-8% below entry (loss cut), or reaches 20-25%
    profit target. Also exit if price closes below 50-day MA on volume.
    """
    if "ma_50" not in df.columns:
        df = compute_indicators(df, params)

    # Close below 50-day MA as a trend breakdown signal
    below_ma50 = df["close"] < df["ma_50"]

    return below_ma50


def get_stop_loss(df, i, params=None):
    """Hard stop at 7-8% below entry price — O'Neil's cardinal rule."""
    stop_pct = _p(params, "stop_loss_pct")
    entry_price = df["close"].iloc[i]
    return entry_price * (1 - stop_pct)


def position_size(capital, entry_price, stop, risk_pct):
    """Risk-based sizing. O'Neil recommends 4-7 positions max."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    O'Neil's standard: take profit at 20-25% above entry.
    Exception: if stock gains 20%+ in under 3 weeks, hold 8 weeks.
    """
    if direction == "long":
        return entry_price * 1.25
    return entry_price * 0.75
