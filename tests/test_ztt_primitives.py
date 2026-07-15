"""ZTT Phase 2 — primitive + invariant tests.

Pins the FROZEN SACRED params and validates each primitive. The integration test
runs the generator on real 1Y M10 Gold and asserts STRUCTURAL INVARIANTS
(phantom-fill guard, correct SL/TP geometry) rather than exact trade counts —
those are Phase 3/4 questions.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.regimes.ztt import (
    ZTTParams, ZTTSetup, compute_indicators, generate_setups,
    ma_momentum, _trend_state, _score_touch, _Level,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'cache' / 'oanda_gold_1y_10m.csv'


# ── SACRED params frozen (signed off 2026-06-09) ──────────────────────────
def test_sacred_params_frozen():
    p = ZTTParams()
    assert p.WMA_PERIOD == 144
    assert p.SMMA_PERIOD == 5
    assert p.ATR_PERIOD == 14
    assert p.MIN_RR == 3.0


def test_frozen_mechanization_defaults():
    p = ZTTParams()
    assert (p.SWING_W, p.MIN_TOUCHES) == (3, 2)
    assert (p.LEVEL_TOL, p.DISRESPECT_TOL, p.BREAK_BUFFER) == (0.25, 0.10, 0.10)
    assert (p.REVERSAL_LOOKBACK, p.RETEST_TOL, p.MAX_RETEST_WAIT) == (30, 0.50, 10)
    assert (p.SL_BUFFER, p.MIN_SL_DOLLARS, p.STRUCT_CAP_BUFFER) == (0.30, 10.0, 0.25)


def test_params_are_immutable():
    p = ZTTParams()
    with pytest.raises(Exception):
        p.WMA_PERIOD = 9  # frozen dataclass


# ── pure helpers ──────────────────────────────────────────────────────────
def test_ma_momentum():
    assert ma_momentum(10.0, 9.0) == 1
    assert ma_momentum(9.0, 10.0) == -1
    assert ma_momentum(np.nan, 9.0) == 0


def test_trend_state():
    assert _trend_state([10, 12], [8, 9]) == 'up'      # HH + HL
    assert _trend_state([12, 10], [9, 8]) == 'down'    # LH + LL
    assert _trend_state([10, 12], [9, 8]) == 'range'   # HH + LL (mixed)
    assert _trend_state([10], [8]) == 'range'          # insufficient


def test_score_touch_clean_vs_disrespect():
    p = ZTTParams()
    # resistance at 100, ATR 10, DISRESPECT_TOL*ATR = 1.0
    lv = _Level(price=100.0, kind='resistance')
    _score_touch(lv, close_k=100.5, atr_k=10.0, p=p)   # close within tol -> clean
    assert (lv.clean, lv.disrespect) == (1, 0)
    _score_touch(lv, close_k=102.0, atr_k=10.0, p=p)   # close beyond tol -> disrespect
    assert (lv.clean, lv.disrespect) == (1, 1)
    sup = _Level(price=100.0, kind='support')
    _score_touch(sup, close_k=99.5, atr_k=10.0, p=p)   # within -> clean
    _score_touch(sup, close_k=98.0, atr_k=10.0, p=p)   # below tol -> disrespect
    assert (sup.clean, sup.disrespect) == (1, 1)


def test_level_qualifies():
    p = ZTTParams()
    lv = _Level(price=100.0, kind='support', clean=2, disrespect=0)
    assert lv.qualifies(p.MIN_TOUCHES)
    lv2 = _Level(price=100.0, kind='support', clean=2, disrespect=3)
    assert not lv2.qualifies(p.MIN_TOUCHES)   # mostly disrespected
    lv3 = _Level(price=100.0, kind='support', clean=1, disrespect=0)
    assert not lv3.qualifies(p.MIN_TOUCHES)   # too few touches


# ── integration on real data: structural invariants ───────────────────────
@pytest.fixture(scope='module')
def gold_1y():
    if not DATA.exists():
        pytest.skip("1Y M10 gold cache missing")
    df = pd.read_csv(DATA, index_col=0, parse_dates=True)
    return df


def test_indicators_compute(gold_1y):
    d = compute_indicators(gold_1y)
    assert {'WMA', 'SMMA', 'ATR', 'swing_high', 'swing_low'} <= set(d.columns)
    # WMA(144) warmup: first 143 are NaN, then populated
    assert d['WMA'].iloc[:143].isna().all()
    assert d['WMA'].iloc[200:].notna().all()


def test_generator_runs_and_is_sane(gold_1y):
    setups = generate_setups(gold_1y)
    assert isinstance(setups, list) and len(setups) > 0, "expected some setups on 1Y gold"
    for s in setups:
        assert isinstance(s, ZTTSetup)
        assert s.direction in ('long', 'short')
        assert s.mode in ('continuation', 'reversal', 'range')


def test_phantom_fill_guard(gold_1y):
    """F2: every entry price must lie within the entry bar's [low, high]."""
    d = gold_1y
    setups = generate_setups(d)
    for s in setups:
        bar = d.iloc[s.entry_index]
        assert bar['Low'] - 1e-6 <= s.entry_price <= bar['High'] + 1e-6, (
            f"setup #{s.entry_index} entry {s.entry_price} outside bar "
            f"[{bar['Low']}, {bar['High']}] — PHANTOM FILL"
        )


def test_sl_tp_geometry(gold_1y):
    """SL on the correct side; TP ~ MIN_RR; SL distance >= floor."""
    p = ZTTParams()
    setups = generate_setups(gold_1y, p)
    for s in setups:
        assert s.sl_distance >= p.MIN_SL_DOLLARS - 1e-6
        if s.direction == 'long':
            assert s.stop_loss < s.entry_price < s.take_profit
        else:
            assert s.take_profit < s.entry_price < s.stop_loss
        assert s.rr == pytest.approx(p.MIN_RR, abs=0.05)


def test_arm_a_excludes_reversals(gold_1y):
    """Continuation-only arm must produce no 'reversal'-mode setups."""
    arm_a = ZTTParams(allow_reversal=False)
    setups = generate_setups(gold_1y, arm_a)
    assert all(s.mode != 'reversal' for s in setups)
