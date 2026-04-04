"""
Sperandeo Market Age Reversal Strategy
========================================
Source: "The New Market Wizards" - Victor Sperandeo interview
        "Trader Vic - Methods of a Wall Street Master"

Core idea: Sperandeo observed that market trends go through "stages of life."
Young trends are strong and should be followed. Old trends (extended moves)
are fragile and prone to reversal. By measuring cumulative move since the
last significant reversal, we can estimate the "age" of the current trend.

When a move exceeds the historical median (roughly 20% for major indices),
the system increases sensitivity to reversal signals. Entry occurs when a
reversal pattern is detected in an "old age" market.

Sperandeo's "1-2-3 Reversal":
1. Trendline break
2. Failure to make new high/low
3. Break of the prior reaction point

This implementation uses a simplified version tracking trend age via
cumulative returns and detecting exhaustion.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Sperandeo Market Age Reversal",
    "category": "counter_trend",
    "source_book": "The New Market Wizards",
    "source_traders": ["Victor Sperandeo"],
    "timeframe": "daily",
    "markets": ["indices", "forex", "commodities"],
    "confidence": 0.65,
}

DEFAULT_PARAMS = {
    "atr_period": 14,
    "trend_lookback": 60,       # Bars to measure cumulative move
    "age_threshold_pct": 0.20,  # 20% move = "old age" (Sperandeo's median)
    "reversal_lookback": 5,     # Bars to confirm reversal pattern
    "swing_window": 10,         # Window for swing high/low detection
    "atr_stop_mult": 2.5,      # Stop in ATR multiples
    "rr_target": 2.0,          # Risk-reward ratio for TP
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """Add trend age, reversal detection, and ATR."""
    atr_period = _p(params, "atr_period")
    trend_lb = _p(params, "trend_lookback")
    age_thresh = _p(params, "age_threshold_pct")
    swing_win = _p(params, "swing_window")
    rev_lb = _p(params, "reversal_lookback")

    # ATR
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # Cumulative return over the trend lookback period
    df["cum_return"] = df["close"].pct_change(trend_lb)

    # Market is "old" when cumulative move exceeds threshold
    df["old_uptrend"] = df["cum_return"] > age_thresh
    df["old_downtrend"] = df["cum_return"] < -age_thresh

    # Swing highs and lows for 1-2-3 reversal detection
    df["swing_high"] = df["high"].rolling(swing_win, center=True).max()
    df["swing_low"] = df["low"].rolling(swing_win, center=True).min()

    # Recent highest high and lowest low (non-centered for real-time)
    df["recent_high"] = df["high"].rolling(swing_win).max()
    df["recent_low"] = df["low"].rolling(swing_win).min()

    # Simplified reversal signals:
    # Bearish reversal (short entry): old uptrend + failure to make new high
    # + close below prior support
    df["failing_high"] = df["high"] < df["high"].shift(1).rolling(rev_lb).max()
    df["break_support"] = df["close"] < df["recent_low"].shift(1)

    # Bullish reversal (long entry): old downtrend + failure to make new low
    # + close above prior resistance
    df["failing_low"] = df["low"] > df["low"].shift(1).rolling(rev_lb).min()
    df["break_resistance"] = df["close"] > df["recent_high"].shift(1)

    return df


def entry_signal(df, params=None):
    """
    Entry: Detect reversals in 'old age' markets.

    Long: Old downtrend exhausted + bullish reversal pattern
    Short: Old uptrend exhausted + bearish reversal pattern

    For the long-only runner, we focus on long entries from old downtrends.
    We also include short-to-long transitions in old uptrends that reverse.
    """
    if "old_uptrend" not in df.columns:
        df = compute_indicators(df, params)

    valid = df["atr"].notna() & df["cum_return"].notna()

    # Long entry: old downtrend showing bullish reversal
    long_reversal = df["old_downtrend"] & df["failing_low"] & df["break_resistance"]

    return long_reversal & valid


def exit_signal(df, params=None):
    """
    Exit when:
    1. Market shows renewed trend strength against the reversal position
       (new swing high/low in the original trend direction)
    2. Or the reversal move reaches the target (approximated by the
       cumulative return flipping back toward zero)
    """
    if "old_uptrend" not in df.columns:
        df = compute_indicators(df, params)

    # Exit long if the downtrend reasserts (new low below recent low)
    new_low = df["close"] < df["recent_low"].shift(1)

    # Exit if cumulative return flips positive (reversal succeeded, take profit)
    trend_flipped = df["cum_return"] > 0

    return new_low | trend_flipped


def get_stop_loss(df, i, params=None):
    """Stop loss below recent swing low minus ATR buffer."""
    atr_mult = _p(params, "atr_stop_mult")
    swing_win = _p(params, "swing_window")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns and pd.notna(df["atr"].iloc[i]) else 0

    start = max(0, i - swing_win)
    swing_low = df["low"].iloc[start:i + 1].min()

    return swing_low - atr_mult * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """Conservative sizing for counter-trend: 1% risk default."""
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * risk_pct) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Take profit at 2:1 risk-reward from entry.
    Counter-trend trades use tighter targets than trend-following.
    """
    risk = abs(entry_price - stop_loss)
    if direction == "long":
        return entry_price + 2.0 * risk
    else:
        return entry_price - 2.0 * risk
