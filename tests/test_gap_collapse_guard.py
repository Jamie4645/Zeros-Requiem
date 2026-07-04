"""Gap-collapse guard regression (2026-07-04 fresh-strategy ultrareview defect #1).

A fill that gaps toward the stop can shrink realized risk_dist far below the
signal-time SL distance, exploding position size (observed on real data:
risk_dist $0.046 vs signal ~$5 -> r = -73.9, excess kurtosis 1037).

`ztt_sim.simulate(min_risk_frac=...)` must treat such fills as UNABLE.
Default (0.0) must preserve historical behavior byte-for-byte — all canon
results were produced without the guard.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.real_trades.ztt_sim import simulate  # noqa: E402


@dataclass
class _Setup:
    entry_index: int
    entry_time: pd.Timestamp
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    rr: float
    mode: str = 'test'
    level_price: float = 0.0
    level_touches: int = 0
    break_index: int = 0


def _frame():
    """Signal bar at 100, SL 99; next bar OPENS at 98.70 (gap toward/through the
    stop). With the session cost (+0.60 at 09:00 UTC) the realized entry is
    ~99.30 -> realized risk_dist ~0.30 vs signal-time 1.0 (30% < 50% guard)."""
    idx = pd.date_range('2026-01-05 09:00', periods=10, freq='10min', tz='UTC')
    o = [100.0, 100.0, 98.70, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5]
    h = [100.5, 100.5, 99.60, 99.6, 99.6, 99.6, 99.6, 99.6, 99.6, 99.6]
    l = [99.50, 99.50, 98.50, 99.3, 99.3, 99.3, 99.3, 99.3, 99.3, 99.3]
    c = [100.0, 100.0, 99.50, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5, 99.5]
    return pd.DataFrame({'Open': o, 'High': h, 'Low': l, 'Close': c}, index=idx)


def _setup(df):
    return [_Setup(entry_index=1, entry_time=df.index[1], direction='long',
                   entry_price=100.0, stop_loss=99.0, take_profit=101.8, rr=1.8)]


def test_guard_marks_gap_collapsed_fill_unable():
    df = _frame()
    atr_v = np.full(len(df), 0.5)
    trades, unables = simulate(_setup(df), df, atr_v, one_position=True,
                               max_hold=5, min_risk_frac=0.5)
    assert trades == [] and unables == 1


def test_default_preserves_historical_behavior():
    df = _frame()
    atr_v = np.full(len(df), 0.5)
    trades, unables = simulate(_setup(df), df, atr_v, one_position=True, max_hold=5)
    assert unables == 0 and len(trades) == 1
    # the pathology the guard exists for: collapsed realized risk -> outsized |r|
    # (a clean SL loss is ~ -1R minus costs; here |r| blows out well past that)
    assert abs(trades[0]['r']) > 3


def test_normal_fill_unaffected_by_guard():
    df = _frame()
    df.loc[df.index[2], 'Open'] = 100.05   # no gap: fill near signal price
    df.loc[df.index[2], 'High'] = 100.60
    df.loc[df.index[2], 'Low'] = 99.30     # keep bar range under the outlier guard
    atr_v = np.full(len(df), 0.5)
    trades, unables = simulate(_setup(df), df, atr_v, one_position=True,
                               max_hold=5, min_risk_frac=0.5)
    assert unables == 0 and len(trades) == 1
