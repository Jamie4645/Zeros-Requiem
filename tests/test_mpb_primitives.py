"""MPB — primitive + invariant tests (pre-registered candidate, KB-93).

Pins the SACRED/FROZEN params and validates every primitive on SYNTHETIC data
(always collectible — no data files needed): touch/rejection geometry, ER gate,
SL %-band rejection, TP cap + rr recompute, look-ahead guard, short mirror.
The single integration test runs the generator on the first 20,000 rows of the
real 10Y M10 Gold cache and asserts STRUCTURAL INVARIANTS only — profitability
is the separate pre-registered N1-N8 gauntlet (KB-93), NOT tested here.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.indicators.technical import smma
from src.regimes.mpb import MPBParams, MPBSetup, compute_indicators, generate_setups

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'cache' / 'oanda_gold_10y_10m.csv'


# ── SACRED / FROZEN params pinned (KB-93, pre-registered 2026-07-04) ───────
def test_sacred_params_frozen():
    p = MPBParams()
    assert p.WMA_PERIOD == 144
    assert p.SMMA_PERIOD == 5
    assert p.ATR_PERIOD == 14


def test_frozen_mechanization_defaults():
    p = MPBParams()
    assert (p.SLOPE_WIN, p.ER_WIN, p.ER_MIN) == (20, 10, 0.30)
    assert (p.SL_BUFFER_ATR, p.SL_MAX_PCT, p.SL_MIN_PCT) == (0.10, 0.0045, 0.0015)
    assert (p.RR_TARGET, p.TP_CAP_PCT, p.RR_FLOOR) == (1.8, 0.020, 1.7)
    assert (p.MAX_HOLD, p.SWING_WIN) == (72, 5)


def test_params_are_immutable():
    p = MPBParams()
    with pytest.raises(Exception):
        p.WMA_PERIOD = 9  # frozen dataclass


# ── synthetic OHLC builders ───────────────────────────────────────────────
def _mk_df(closes: np.ndarray, body: float, wick: float, bull: bool) -> pd.DataFrame:
    """Deterministic candles around a close path. bull=True -> every bar close>open."""
    closes = np.asarray(closes, dtype=float)
    if bull:
        opens = closes - body
    else:
        opens = closes + body
    highs = np.maximum(opens, closes) + wick
    lows = np.minimum(opens, closes) - wick
    idx = pd.date_range('2025-01-01', periods=len(closes), freq='10min', tz='UTC')
    return pd.DataFrame({'Open': opens, 'High': highs, 'Low': lows, 'Close': closes},
                        index=idx)


def _uptrend(n=240, base=3000.0, slope=2.0, body=1.0, wick=0.5) -> pd.DataFrame:
    return _mk_df(base + slope * np.arange(n), body, wick, bull=True)


def _downtrend(n=240, base=3600.0, slope=2.0, body=1.0, wick=0.5) -> pd.DataFrame:
    return _mk_df(base - slope * np.arange(n), body, wick, bull=False)


def _touch_long(df: pd.DataFrame, t: int, depth: float = 0.5) -> None:
    """Dip bar t's Low to `depth` below the causal SMMA(5) (touch/pierce)."""
    sm = smma(df['Close'], MPBParams().SMMA_PERIOD)
    df.iloc[t, df.columns.get_loc('Low')] = sm.iloc[t] - depth


def _touch_short(df: pd.DataFrame, t: int, depth: float = 0.5) -> None:
    sm = smma(df['Close'], MPBParams().SMMA_PERIOD)
    df.iloc[t, df.columns.get_loc('High')] = sm.iloc[t] + depth


# ── (1) clean long pullback+rejection -> exactly one setup, exact SL/TP ────
def test_long_pullback_bounce_single_setup():
    p = MPBParams()
    df = _uptrend()
    _touch_long(df, 200)
    setups = generate_setups(df, p)
    assert len(setups) == 1
    s = setups[0]
    assert isinstance(s, MPBSetup)
    assert s.direction == 'long'
    assert s.mode == 'continuation'
    assert s.level_touches == 0
    assert s.break_index == 200                    # touch bar
    assert s.entry_index == 201                    # rejection bar
    assert s.entry_time == df.index[201]
    assert s.entry_price == pytest.approx(df['Close'].iloc[201], abs=1e-3)

    # exact SL/TP arithmetic against independently recomputed indicators
    d = compute_indicators(df, p)
    exp_sl = min(df['Low'].iloc[200], df['Low'].iloc[201]) - p.SL_BUFFER_ATR * d['ATR'].iloc[201]
    exp_dist = df['Close'].iloc[201] - exp_sl
    exp_tp = df['Close'].iloc[201] + p.RR_TARGET * exp_dist   # cap does not bind here
    assert s.stop_loss == pytest.approx(exp_sl, abs=1e-3)
    assert s.take_profit == pytest.approx(exp_tp, abs=2e-3)
    assert s.rr == pytest.approx(p.RR_TARGET, abs=1e-3)
    assert s.level_price == pytest.approx(d['SMMA'].iloc[200], abs=1e-3)
    # SL band respected by construction
    pct = exp_dist / df['Close'].iloc[201]
    assert p.SL_MIN_PCT <= pct <= p.SL_MAX_PCT


# ── (2) chop: ER below gate -> zero setups (ER is the binding gate) ────────
def test_chop_er_gate_rejects():
    p = MPBParams()
    # zigzag superimposed on the ramp: net +20 / path 120 over ER_WIN -> ER = 0.1667
    n = 240
    closes = 3000.0 + 2.0 * np.arange(n) + 6.0 * ((-1.0) ** np.arange(n))
    df = _mk_df(closes, body=1.0, wick=0.5, bull=True)
    _touch_long(df, 200, depth=3.0)
    assert generate_setups(df, p) == []            # ER 0.1667 <= 0.30 -> rejected
    # sharpener: identical df, only ER_MIN relaxed -> the touch emits
    relaxed = generate_setups(df, MPBParams(ER_MIN=0.10))
    assert len(relaxed) == 1 and relaxed[0].direction == 'long'


# ── (3) SL %-of-entry band: too tight and too wide both rejected ──────────
def test_sl_too_tight_rejected():
    # tiny slope -> SMMA hugs price -> SL distance ~0.04% of entry (< 0.15% floor)
    df = _uptrend(slope=0.2, body=0.2, wick=0.1)
    _touch_long(df, 200, depth=0.1)
    assert generate_setups(df, MPBParams()) == []
    # sharpener: only the floor relaxed -> setup emits (floor was the rejector)
    relaxed = generate_setups(df, MPBParams(SL_MIN_PCT=0.0))
    assert len(relaxed) == 1


def test_sl_too_wide_rejected():
    p = MPBParams()
    df = _uptrend()
    # deep dip: SL distance ~0.60% of entry (> 0.45% cap)
    df.iloc[200, df.columns.get_loc('Low')] = df['Close'].iloc[201] - 20.0
    assert generate_setups(df, p) == []
    # sharpener: only the cap relaxed -> setup emits (cap was the rejector)
    relaxed = generate_setups(df, MPBParams(SL_MAX_PCT=0.01))
    assert len(relaxed) == 1
    assert relaxed[0].rr == pytest.approx(p.RR_TARGET, abs=1e-3)  # TP cap untouched


# ── (4) TP cap binds -> rr recomputed; floor rejects when cap crushes rr ──
def test_tp_cap_forces_rr_below_floor_rejected():
    # SL dist ~1.31% of entry (needs SL_MAX_PCT override to reach the TP logic);
    # uncapped TP = 2.36% > 2.0% cap -> capped rr = 1.53 < 1.7 floor -> REJECT
    df = _uptrend()
    df.iloc[200, df.columns.get_loc('Low')] = df['Close'].iloc[201] - 44.0
    assert generate_setups(df, MPBParams(SL_MAX_PCT=0.02)) == []
    # control: same df, cap lifted -> emits at full RR_TARGET (floor wasn't binding)
    ctl = generate_setups(df, MPBParams(SL_MAX_PCT=0.02, TP_CAP_PCT=0.05))
    assert len(ctl) == 1 and ctl[0].rr == pytest.approx(1.8, abs=1e-3)


def test_tp_cap_binds_and_rr_recomputed():
    # SL dist ~1.13% of entry -> uncapped TP 2.04% > cap -> TP pinned at 2.0% of
    # entry, rr recomputed to ~1.77 (>= 1.7 floor) -> setup emitted WITH capped TP
    p = MPBParams(SL_MAX_PCT=0.02)
    df = _uptrend()
    df.iloc[200, df.columns.get_loc('Low')] = df['Close'].iloc[201] - 38.0
    setups = generate_setups(df, p)
    assert len(setups) == 1
    s = setups[0]
    entry = df['Close'].iloc[201]
    assert s.take_profit == pytest.approx(entry * (1 + p.TP_CAP_PCT), abs=2e-3)
    exp_rr = (p.TP_CAP_PCT * entry) / (entry - s.stop_loss)
    assert s.rr == pytest.approx(exp_rr, abs=1e-2)
    assert p.RR_FLOOR <= s.rr < p.RR_TARGET        # cap bound, floor cleared


# ── (5) look-ahead guard: truncation leaves earlier setups unchanged ──────
def test_no_lookahead_truncation_invariance():
    p = MPBParams()
    df = _uptrend(n=260)
    for t in (170, 200, 225):
        _touch_long(df, t)
    full = generate_setups(df, p)
    assert len(full) == 3
    for k in (204, 230, 260):
        part = generate_setups(df.iloc[:k], p)
        exp = [s for s in full if s.entry_index < k - 2]
        got = [s for s in part if s.entry_index < k - 2]
        assert got == exp, f"truncation at k={k} changed earlier setups"


# ── (5b) dedupe: touch within 2 bars of the previous entry is suppressed ──
def test_adjacent_touch_dedupe():
    p = MPBParams()
    df = _uptrend()
    _touch_long(df, 200)
    _touch_long(df, 202)          # 202 < prev entry (201) + 2 -> suppressed
    setups = generate_setups(df, p)
    assert len(setups) == 1 and setups[0].entry_index == 201


# ── (6) short-side mirror of test 1 ────────────────────────────────────────
def test_short_pullback_bounce_mirror():
    p = MPBParams()
    df = _downtrend()
    _touch_short(df, 200)
    setups = generate_setups(df, p)
    assert len(setups) == 1
    s = setups[0]
    assert s.direction == 'short'
    assert s.mode == 'continuation'
    assert s.break_index == 200 and s.entry_index == 201
    d = compute_indicators(df, p)
    entry = df['Close'].iloc[201]
    exp_sl = max(df['High'].iloc[200], df['High'].iloc[201]) + p.SL_BUFFER_ATR * d['ATR'].iloc[201]
    exp_tp = entry - p.RR_TARGET * (exp_sl - entry)
    assert s.entry_price == pytest.approx(entry, abs=1e-3)
    assert s.stop_loss == pytest.approx(exp_sl, abs=1e-3)
    assert s.take_profit == pytest.approx(exp_tp, abs=2e-3)
    assert s.take_profit < s.entry_price < s.stop_loss
    assert s.rr == pytest.approx(p.RR_TARGET, abs=1e-3)


# ── integration: structural invariants on the first 20k rows of real M10 ──
@pytest.mark.skipif(not DATA.exists(), reason="10Y M10 gold cache missing")
def test_integration_20k_slice_invariants():
    p = MPBParams()
    df = pd.read_csv(DATA, index_col=0, parse_dates=True).iloc[:20000]
    assert df.index.tz is not None                 # tz-aware UTC index
    setups = generate_setups(df, p)
    assert len(setups) > 0, "expected some MPB setups on 20k rows of real gold"
    for s in setups:
        assert s.direction in ('long', 'short')
        assert s.mode == 'continuation' and s.level_touches == 0
        assert s.break_index == s.entry_index - 1
        # phantom-fill guard: entry reference inside the entry bar's range
        bar = df.iloc[s.entry_index]
        assert bar['Low'] - 1e-6 <= s.entry_price <= bar['High'] + 1e-6
        # SL band invariant (2e-6 pct tolerance for 3-dp price rounding)
        pct = s.sl_distance / s.entry_price
        assert p.SL_MIN_PCT - 2e-6 <= pct <= p.SL_MAX_PCT + 2e-6
        # geometry + TP cap + rr floor invariants
        if s.direction == 'long':
            assert s.stop_loss < s.entry_price < s.take_profit
        else:
            assert s.take_profit < s.entry_price < s.stop_loss
        tp_pct = abs(s.take_profit - s.entry_price) / s.entry_price
        assert tp_pct <= p.TP_CAP_PCT + 2e-6
        assert p.RR_FLOOR - 1e-3 <= s.rr <= p.RR_TARGET + 1e-3
    # look-ahead cross-check on real data: truncation leaves earlier setups intact
    part = generate_setups(df.iloc[:15000], p)
    exp = [s for s in setups if s.entry_index < 14998]
    got = [s for s in part if s.entry_index < 14998]
    assert got == exp
