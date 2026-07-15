"""ZTT v3 Phase-1 tests — honest metric stack (A2) + regime tagger (B1).

Pure-function tests; no network, no data-cache dependency (synthetic OHLC).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.real_trades import metrics as M           # noqa: E402
from src.regimes.ztt import ZTTParams                   # noqa: E402
from src.regimes.ztt_regime import (                    # noqa: E402
    compute_regime, regime_tags, wilder_adx, _efficiency_ratio,
)


# ──────────────────────────── metrics (A2) ────────────────────────────
def _mk_trades(rs, start='2025-01-01', risk=100.0):
    """Build trade dicts from a list of R-multiples (1 trade/day)."""
    out = []
    t0 = pd.Timestamp(start, tz='UTC')
    for k, r in enumerate(rs):
        out.append(dict(
            pnl=r * risk, r=float(r), exit_reason=('sl' if r < 0 else 'tp'),
            entry_time=t0 + pd.Timedelta(days=k),
            exit_time=t0 + pd.Timedelta(days=k, hours=6),
            mfe_r=max(r, 0.0), regime='up',
        ))
    return out


def test_max_drawdown_known():
    eq = [100, 120, 90, 110]          # peak 120 -> trough 90 = 25%
    assert M.max_drawdown(eq) == pytest.approx(0.25)


def test_profit_factor():
    assert M.profit_factor([2, 2, -1, -1]) == pytest.approx(2.0)
    assert M.profit_factor([1, 2]) == float('inf')


def test_information_ratio_sign():
    up = np.full(30, 0.01)            # steady gains, zero vol -> 0 by guard
    assert M.information_ratio(up) == 0.0
    noisy_up = np.array([0.02, -0.01] * 15) + 0.01
    assert M.information_ratio(noisy_up) > 0
    assert M.information_ratio(-noisy_up) < 0


def test_r_percentiles_and_kurtosis():
    rp = M.r_percentiles([-1, -1, -1, 3])
    assert rp['p50'] == pytest.approx(-1.0)
    assert rp['mean'] == pytest.approx(0.0)
    assert rp['worst_decile'] == pytest.approx(-1.0)
    assert isinstance(M.excess_kurtosis([-1, -1, -1, 9, -1, -1]), float)


def test_worst_sequence():
    # cumulative dips by 5 then recovers
    assert M.worst_sequence([1, -3, -2, 4]) == pytest.approx(-5.0)
    assert M.worst_sequence([1, 2, 3]) == pytest.approx(0.0)


def test_cap_mfe_audit():
    trades = [
        dict(exit_reason='cap', r=1.5, mfe_r=2.5, regime='up'),    # left 1.0
        dict(exit_reason='cap', r=1.5, mfe_r=1.7, regime='down'),  # left 0.2
        dict(exit_reason='tp', r=3.0, mfe_r=3.0, regime='up'),     # ignored
    ]
    a = M.cap_mfe_audit(trades)
    assert a['n_capped'] == 2
    assert a['median_left_on_table_r'] == pytest.approx(0.6)
    assert set(a['by_regime']) == {'up', 'down'}


def test_summarize_shape_and_benchmark():
    trades = _mk_trades([3, -1, 3, -1, -1, 3, -1, 2])
    close = pd.Series(
        np.linspace(100, 130, 40),
        index=pd.date_range('2025-01-01', periods=40, freq='D', tz='UTC'))
    m = M.summarize(trades, 10000.0, benchmark_close=close)
    for k in ('information_ratio', 'sortino', 'calmar', 'ulcer', 'net_r',
              'r_dist', 'cap_mfe', 'buy_hold_info_ratio', 'beats_buy_hold',
              'live_expectation_ir', 'profit_factor'):
        assert k in m
    assert m['n'] == len(trades)
    assert m['live_expectation_ir'] == pytest.approx(m['information_ratio'] / 2)


def test_summarize_empty():
    assert M.summarize([], 10000.0) == {'n': 0}


# ──────────────────────────── regime (B1) ────────────────────────────
def _synthetic_ohlc(n=900):
    """Up-trend then down-trend, with intrabar range, tz-aware 10m bars."""
    half = n // 2
    trend = np.concatenate([np.linspace(100, 200, half),
                            np.linspace(200, 120, n - half)])
    osc = 3.0 * np.sin(np.arange(n) * 2 * np.pi / 12)   # zigzag -> real swings
    closes = trend + osc
    rng = np.abs(np.sin(np.arange(n))) * 0.3 + 0.2
    df = pd.DataFrame({
        'Open': closes,
        'High': closes + rng,
        'Low': closes - rng,
        'Close': closes,
        'Volume': np.full(n, 1000.0),
    }, index=pd.date_range('2024-01-01', periods=n, freq='10min', tz='UTC'))
    return df


def test_efficiency_ratio_bounds():
    close = np.linspace(0, 10, 50)             # perfectly straight -> ER == 1
    assert _efficiency_ratio(close, 49, 20) == pytest.approx(1.0)
    choppy = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1], dtype=float)
    er = _efficiency_ratio(choppy, 9, 20)
    assert 0.0 <= er < 0.5                      # net 1, path 9 -> ~0.11


def test_wilder_adx_range():
    df = _synthetic_ohlc()
    adx = wilder_adx(df, 14)
    valid = adx[~np.isnan(adx)]
    assert valid.size > 0
    assert valid.min() >= 0 and valid.max() <= 100


def test_compute_regime_columns_and_causality():
    df = _synthetic_ohlc()
    p = ZTTParams()
    rd = compute_regime(df, p)
    assert list(rd.columns) == ['trend_dir', 'er', 'adx', 'vol_ratio', 'vol_bucket']
    assert set(rd['trend_dir'].unique()) <= {'up', 'down', 'range'}
    # the synthetic series trends up then down -> both must appear
    assert {'up', 'down'} <= set(rd['trend_dir'].unique())
    er = rd['er'].dropna()
    assert (er >= 0).all() and (er <= 1.0 + 1e-9).all()
    buckets = set(rd['vol_bucket'].dropna().unique())
    assert buckets <= {'low', 'mid', 'high'}


def test_regime_tags_dict():
    df = _synthetic_ohlc()
    p = ZTTParams()
    rd = compute_regime(df, p)
    tag = regime_tags(df, len(df) - 1, p, regime_df=rd)
    assert set(tag) == {'trend_dir', 'er', 'adx', 'vol_ratio', 'vol_bucket'}
    assert tag['trend_dir'] in {'up', 'down', 'range'}


def test_regime_is_tag_only_no_lookahead():
    """Tag at bar i must not change when future bars are appended (causality)."""
    df = _synthetic_ohlc()
    p = ZTTParams()
    i = 600
    full = regime_tags(df, i, p)
    truncated = regime_tags(df.iloc[:i + 1], i, p)
    assert full['trend_dir'] == truncated['trend_dir']
    assert full['er'] == truncated['er']


# ─────────────────── regime-CV harness (B2) ───────────────────
sys.path.insert(0, str(ROOT / 'tests'))
import _ztt_regime_cv as CV   # noqa: E402


def test_auc_perfect_and_random():
    y = np.array([0, 0, 1, 1], dtype=float)
    assert CV.auc(np.array([1, 2, 3, 4.]), y) == pytest.approx(1.0)   # perfectly separable
    assert CV.auc(np.array([4, 3, 2, 1.]), y) == pytest.approx(0.0)   # perfectly anti
    assert CV.auc(np.array([1, 1, 1, 1.]), y) == pytest.approx(0.5)   # no info


def test_regime_cv_refuses_single_regime():
    """A single populated regime fold => REFUSE (every-fold rule, never 'most')."""
    n = 60
    data = pd.DataFrame({
        'feature': np.random.default_rng(0).normal(size=n),
        'label': ([1, 0] * (n // 2)),
        'regime': ['down'] * n,          # only one regime populated
    })
    res = CV.regime_cv(data, 'feature', verbose=False)
    assert res['verdict'] == 'REFUSE'


def test_regime_cv_certifies_when_all_folds_strong():
    """All three folds populated with a perfectly-discriminating feature => CERTIFY."""
    rng = np.random.default_rng(1)
    frames = []
    for reg in ('up', 'down', 'range'):
        k = 30
        label = np.array([1] * k + [0] * k)
        # feature cleanly separates classes in every fold
        feat = np.where(label == 1, rng.normal(5, 0.5, 2 * k), rng.normal(-5, 0.5, 2 * k))
        frames.append(pd.DataFrame({'feature': feat, 'label': label, 'regime': reg}))
    data = pd.concat(frames, ignore_index=True)
    res = CV.regime_cv(data, 'feature', verbose=False)
    assert res['verdict'] == 'CERTIFY'
