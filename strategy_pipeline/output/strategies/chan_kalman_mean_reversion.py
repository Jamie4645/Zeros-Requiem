"""
Kalman Filter Mean Reversion on Cointegrated Pairs (Chan)
=========================================================
Source: "Algorithmic Trading" - Ernest Chan, Chapter 2 (Strategy #4)

Core idea: Use a Kalman Filter to dynamically estimate the hedge ratio
between two cointegrated assets (EWA/EWC). The forecast error from the
filter serves as the trading signal — go long the spread when error is
negative (spread too low), short when positive (spread too high).

Best-in-class mean reversion approach: Sharpe 2.4, APR 26.2% (2007-2012).
The Kalman Filter eliminates the lookback window selection problem that
plagues rolling-regression approaches.
"""

import numpy as np
import pandas as pd


STRATEGY_META = {
    "name": "Kalman Filter Mean Reversion (EWA-EWC)",
    "category": "mean_reversion",
    "source_book": "Algorithmic Trading",
    "source_traders": ["Ernest Chan"],
    "timeframe": "daily",
    "markets": ["etfs", "equities"],
    "confidence": 0.80,
}

DEFAULT_PARAMS = {
    "delta": 0.0001,        # State transition variance (controls hedge ratio adaptability)
    "ve": 0.001,            # Observation noise variance
    "entry_threshold": 1.0,  # Entry when |forecast_error / sqrt(Q)| > threshold
    "exit_threshold": 0.0,   # Exit when forecast error crosses zero
    "atr_period": 14,        # ATR for stop placement
    "atr_stop_mult": 3.0,    # Stop distance in ATR multiples
}


def _p(params, key):
    if params and key in params:
        return params[key]
    return DEFAULT_PARAMS[key]


def compute_indicators(df, params=None):
    """
    Run the Kalman Filter to estimate the dynamic hedge ratio between
    two assets. Expects df to have columns 'close' (asset Y) and 'close_x'
    (asset X, the hedge instrument).

    If 'close_x' is missing, fall back to single-asset Bollinger-band
    mean reversion on 'close'.
    """
    delta = _p(params, "delta")
    ve = _p(params, "ve")
    atr_period = _p(params, "atr_period")

    n = len(df)

    if "close_x" in df.columns:
        y = df["close"].values.astype(float)
        x = df["close_x"].values.astype(float)
    else:
        y = df["close"].values.astype(float)
        x = np.arange(1, n + 1, dtype=float)

    hedge_ratio = np.zeros(n)
    intercept = np.zeros(n)
    forecast_error = np.zeros(n)
    sqrt_q = np.zeros(n)

    # Kalman filter state: [hedge_ratio, intercept]
    theta = np.zeros(2)
    P = np.eye(2)  # State covariance
    R = np.eye(2) * delta  # State transition noise

    for t in range(n):
        if t == 0:
            theta = np.array([0.0, 0.0])
            P = np.eye(2)

        F = np.array([x[t], 1.0])  # Observation vector

        y_hat = F @ theta
        e = y[t] - y_hat  # Forecast error

        Q = F @ P @ F.T + ve  # Forecast error variance

        K = P @ F / Q  # Kalman gain

        theta = theta + K * e
        P = P - np.outer(K, F) @ P + R

        hedge_ratio[t] = theta[0]
        intercept[t] = theta[1]
        forecast_error[t] = e
        sqrt_q[t] = np.sqrt(max(Q, 1e-10))

    df["hedge_ratio"] = hedge_ratio
    df["intercept"] = intercept
    df["forecast_error"] = forecast_error
    df["sqrt_q"] = sqrt_q
    df["z_score"] = forecast_error / np.where(sqrt_q > 0, sqrt_q, 1.0)

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
    Enter long spread when z_score < -entry_threshold (spread is too low).
    For single-asset mode, this means price is below Kalman-estimated fair value.
    """
    if "z_score" not in df.columns:
        df = compute_indicators(df, params)

    threshold = _p(params, "entry_threshold")
    valid = df["atr"].notna() & (df["sqrt_q"] > 0)

    long_signal = (df["z_score"] < -threshold) & valid

    return long_signal


def exit_signal(df, params=None):
    """Exit when forecast error crosses zero (spread reverts to fair value)."""
    if "z_score" not in df.columns:
        df = compute_indicators(df, params)

    exit_threshold = _p(params, "exit_threshold")

    exit_on_reversion = df["z_score"] > exit_threshold

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
    Mean reversion: take profit when spread reverts to mean (z_score = 0).
    The exit_signal handles this. Return None for no fixed TP.
    """
    return None
