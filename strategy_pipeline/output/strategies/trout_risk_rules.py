"""
Trout Risk Management Module
==============================
Source: "The New Market Wizards" - Monroe Trout interview

NOT a standalone strategy. This is a risk management overlay that can be
applied on top of any strategy. Trout was known for exceptional risk
discipline, never having a losing month in his career.

Trout's rules:
1. Maximum 1.5% loss on any single trade
2. Maximum 4% loss in a single day
3. Maximum 10% loss in a single month
4. Position size capped per-market per-month

Usage:
    from trout_risk_rules import TroutRiskManager

    risk_mgr = TroutRiskManager(initial_capital=100_000)
    # Before each trade:
    allowed, adjusted_size = risk_mgr.check_trade(
        market="GOLD", entry_price=2000, stop=1970, size=10
    )
    # After each trade:
    risk_mgr.record_trade(pnl=-500, date=today)

This module also provides a STRATEGY_META and the standard interface
functions so the backtester can load it. When run as a "strategy," it
uses a simple MA crossover but applies Trout's risk rules as filters.
"""

import numpy as np
import pandas as pd
from datetime import datetime


STRATEGY_META = {
    "name": "Trout Risk Rules (MA Cross + Risk Overlay)",
    "category": "risk_management",
    "source_book": "The New Market Wizards",
    "source_traders": ["Monroe Trout"],
    "timeframe": "daily",
    "markets": ["all"],
    "confidence": 0.90,
}

DEFAULT_PARAMS = {
    # Risk limits (Trout's actual rules)
    "max_risk_per_trade": 0.015,    # 1.5% max loss per trade
    "max_daily_loss": 0.04,         # 4% max daily loss
    "max_monthly_loss": 0.10,       # 10% max monthly loss
    # Simple MA cross for entry (this is just a vehicle for the risk rules)
    "fast_ma": 10,
    "slow_ma": 30,
    "atr_period": 14,
    "atr_stop_mult": 2.0,
    # Monthly position cap
    "max_monthly_positions": 20,
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


# ═══════════════════════════════════════════════════════════════════
# RISK MANAGEMENT MODULE (importable by other strategies)
# ═══════════════════════════════════════════════════════════════════

class TroutRiskManager:
    """
    Standalone risk manager implementing Monroe Trout's rules.
    Can be imported and used by any strategy.
    """

    def __init__(self, initial_capital=100_000, params=None):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = _p(params, "max_risk_per_trade")
        self.max_daily_loss = _p(params, "max_daily_loss")
        self.max_monthly_loss = _p(params, "max_monthly_loss")
        self.max_monthly_positions = _p(params, "max_monthly_positions")

        # Tracking state
        self.daily_pnl = 0.0
        self.monthly_pnl = 0.0
        self.monthly_trades = 0
        self.current_day = None
        self.current_month = None

    def _reset_daily(self, date):
        """Reset daily tracking if it is a new day."""
        day = date.date() if hasattr(date, "date") else date
        if day != self.current_day:
            self.daily_pnl = 0.0
            self.current_day = day

    def _reset_monthly(self, date):
        """Reset monthly tracking if it is a new month."""
        month = (date.year, date.month) if hasattr(date, "year") else None
        if month and month != self.current_month:
            self.monthly_pnl = 0.0
            self.monthly_trades = 0
            self.current_month = month

    def check_trade(self, entry_price, stop, size, date=None):
        """
        Check if a proposed trade passes all risk rules.

        Returns:
            (allowed: bool, adjusted_size: float)
        """
        if date:
            self._reset_daily(date)
            self._reset_monthly(date)

        dollar_risk_per_unit = abs(entry_price - stop)
        total_risk = dollar_risk_per_unit * size

        # Rule 1: Max 1.5% risk per trade
        max_trade_risk = self.current_capital * self.max_risk_per_trade
        if total_risk > max_trade_risk and dollar_risk_per_unit > 0:
            size = max_trade_risk / dollar_risk_per_unit

        # Rule 2: Check daily loss limit
        daily_limit = self.current_capital * self.max_daily_loss
        if abs(self.daily_pnl) >= daily_limit:
            return False, 0

        # Rule 3: Check monthly loss limit
        monthly_limit = self.current_capital * self.max_monthly_loss
        if abs(self.monthly_pnl) >= monthly_limit:
            return False, 0

        # Rule 4: Monthly position cap
        if self.monthly_trades >= self.max_monthly_positions:
            return False, 0

        return True, max(0, size)

    def record_trade(self, pnl, date=None):
        """Record a completed trade for risk tracking."""
        if date:
            self._reset_daily(date)
            self._reset_monthly(date)
        self.daily_pnl += pnl
        self.monthly_pnl += pnl
        self.monthly_trades += 1
        self.current_capital += pnl

    def max_position_size(self, entry_price, stop, risk_pct=None):
        """
        Calculate maximum allowed position size given Trout's rules.
        """
        if risk_pct is None:
            risk_pct = self.max_risk_per_trade
        dollar_risk = abs(entry_price - stop)
        if dollar_risk <= 0:
            return 0
        return (self.current_capital * risk_pct) / dollar_risk


# ═══════════════════════════════════════════════════════════════════
# STANDARD STRATEGY INTERFACE (for backtester compatibility)
# Uses a simple MA crossover as the trade vehicle, but the real
# value is the risk management rules.
# ═══════════════════════════════════════════════════════════════════

def compute_indicators(df, params=None):
    """Add MAs and ATR for the simple entry vehicle."""
    fast = _p(params, "fast_ma")
    slow = _p(params, "slow_ma")
    atr_period = _p(params, "atr_period")

    df["ma_fast"] = df["close"].rolling(fast).mean()
    df["ma_slow"] = df["close"].rolling(slow).mean()

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift(1)).abs(),
        (df["low"] - df["close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    df["atr"] = tr.rolling(atr_period).mean()

    # MA crossover
    df["ma_cross_up"] = (
        (df["ma_fast"] > df["ma_slow"]) &
        (df["ma_fast"].shift(1) <= df["ma_slow"].shift(1))
    )
    df["ma_cross_down"] = (
        (df["ma_fast"] < df["ma_slow"]) &
        (df["ma_fast"].shift(1) >= df["ma_slow"].shift(1))
    )

    # Monthly loss tracking (simplified for series-based backtester):
    # Compute rolling 20-bar return as proxy for monthly performance
    df["rolling_20d_return"] = df["close"].pct_change(20)

    return df


def entry_signal(df, params=None):
    """
    Entry: MA crossover with risk filter.
    Skip entries if the rolling monthly return suggests we are near
    the 10% monthly loss limit (approximation for series-based runner).
    """
    if "ma_fast" not in df.columns:
        df = compute_indicators(df, params)

    max_monthly = _p(params, "max_monthly_loss")
    valid = df["atr"].notna()

    # Basic MA cross entry
    signal = df["ma_cross_up"] & valid

    # Risk filter: suppress entries if recent performance is very bad
    # (approximation of Trout's monthly loss limit)
    monthly_ok = (df["rolling_20d_return"] > -max_monthly) | df["rolling_20d_return"].isna()

    return signal & monthly_ok


def exit_signal(df, params=None):
    """Exit on MA cross reversal."""
    if "ma_fast" not in df.columns:
        df = compute_indicators(df, params)

    return df["ma_cross_down"]


def get_stop_loss(df, i, params=None):
    """Tight stop: 2*ATR, consistent with 1.5% max risk per trade."""
    atr_mult = _p(params, "atr_stop_mult")
    atr_val = df["atr"].iloc[i] if "atr" in df.columns and pd.notna(df["atr"].iloc[i]) else 0
    return df["close"].iloc[i] - atr_mult * atr_val


def position_size(capital, entry_price, stop, risk_pct):
    """
    Trout's sizing: never risk more than 1.5% per trade.
    Cap risk_pct at 1.5% regardless of what the runner passes in.
    """
    max_risk = min(risk_pct, 0.015)  # Trout's hard cap
    dollar_risk = abs(entry_price - stop)
    if dollar_risk <= 0:
        return 0
    return max(0, (capital * max_risk) / dollar_risk)


def get_take_profit(entry_price, stop_loss, direction):
    """
    Trout focused on risk management, not fixed targets.
    Exit is handled by MA reversal signal.
    """
    return None
