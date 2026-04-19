"""Regression tests for audit remediation (direction, causal 4H, helpers)."""

import numpy as np
import pandas as pd
import pytest

from src.core.risk_manager import RiskManager, RiskConfig, normalize_direction
from src.execution.entries import TradeDirection
from src.regimes.sbrs_v2 import (
    causal_4h_trend_series,
    drop_incomplete_last_4h_bar,
    resample_to_4h,
    trend_4h_at_bar_causal,
)


def test_normalize_direction_enum_and_str():
    assert normalize_direction(TradeDirection.LONG) == 'long'
    assert normalize_direction(TradeDirection.SHORT) == 'short'
    assert normalize_direction('long') == 'long'
    assert normalize_direction('SHORT') == 'short'


def test_risk_manager_can_trade_accepts_enum():
    cfg = RiskConfig()
    rm = RiskManager(cfg, 100_000.0)
    ok, _ = rm.can_trade([], TradeDirection.LONG, 100.0, pd.Timestamp('2020-01-01'))
    assert ok is True


def test_drop_incomplete_last_4h_removes_partial_bucket():
    # Hourly UTC bars 08–10 only: 4h bin starting 08:00 is incomplete (needs 11:00 bar)
    idx = pd.date_range('2024-01-02 08:00', periods=3, freq='1h', tz='UTC')
    df1h = pd.DataFrame(
        {'Open': 1.0, 'High': 1.1, 'Low': 0.9, 'Close': 1.0},
        index=idx,
    )
    df4 = resample_to_4h(df1h)
    assert len(df4) >= 1
    trimmed = drop_incomplete_last_4h_bar(df4, df1h)
    assert len(trimmed) == len(df4) - 1


def test_trend_4h_at_bar_causal_no_future_1h():
    np.random.seed(42)
    n = 400
    idx = pd.date_range('2020-01-01', periods=n, freq='1h', tz='UTC')
    close = 100 + np.cumsum(np.random.randn(n) * 0.1)
    df = pd.DataFrame(
        {
            'Open': close,
            'High': close + 0.2,
            'Low': close - 0.2,
            'Close': close,
        },
        index=idx,
    )
    i = 200
    t1 = trend_4h_at_bar_causal(df, i)
    # Truncating future must not change causal trend at i
    t2 = trend_4h_at_bar_causal(df.iloc[: i + 1], i)
    assert t1 == t2
    assert t1 in ('bullish', 'bearish', 'neutral')


def test_causal_series_matches_slice_resample_reference():
    """Incremental causal series matches per-bar resample+dropped incomplete bar."""
    np.random.seed(7)
    n = 120
    idx = pd.date_range('2022-06-01', periods=n, freq='1h', tz='UTC')
    close = 2000 + np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame(
        {
            'Open': close,
            'High': close + 3,
            'Low': close - 3,
            'Close': close,
        },
        index=idx,
    )
    fast = causal_4h_trend_series(df)
    for j in (55, 89, 110):
        slow = trend_4h_at_bar_causal(df, j)
        assert fast.iloc[j] == slow, f'mismatch at {j}: {fast.iloc[j]} vs {slow}'
