"""VTC — primitive + invariant tests (mirror of tests/test_ztt_primitives.py).

Pins the FROZEN pre-registered params (KB-93, 2026-07-04) and validates each
primitive on SYNTHETIC data (no data files needed). The integration test runs
the generator on the real 10Y M10 Gold cache slice and asserts STRUCTURAL
INVARIANTS only — NO profitability/PF computation here; validation is the
separate pre-registered N1-N8 gauntlet.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.regimes.vtc import VTCParams, VTCSetup, compute_indicators, generate_setups

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'cache' / 'oanda_gold_10y_10m.csv'

P = VTCParams()


# ── params frozen (pre-registered KB-93) ──────────────────────────────────
def test_sacred_params_frozen():
    assert P.ATR_PERIOD == 14


def test_frozen_mechanization_defaults():
    assert (P.THRUST_ATR, P.CLV_BAND) == (1.5, 0.80)
    assert (P.HTF_SMA, P.HTF_SLOPE_WIN) == (20, 5)
    assert (P.SL_SWING_WIN, P.SL_MAX_PCT, P.SL_MIN_PCT) == (3, 0.0045, 0.0015)
    assert (P.RR_TARGET, P.TP_CAP_PCT, P.RR_FLOOR) == (1.8, 0.020, 1.7)
    assert (P.COOLDOWN_BARS, P.MAX_HOLD) == (6, 72)


def test_params_are_immutable():
    with pytest.raises(Exception):
        VTCParams().THRUST_ATR = 99.0  # frozen dataclass


# ── synthetic frame builders ──────────────────────────────────────────────
def make_trend(n=200, start=3000.0, drift=0.3, tz='UTC'):
    """Continuous 10m trend: open = previous close, close on the trendline,
    +-1.0 wick each side. Range ~= |drift|+2, ATR ~= |drift|+2. Positive drift
    -> clean 1H long bias after ~150 bars (25 completed 1H bars); negative
    drift -> short bias. No bar ever passes the thrust range gate on its own.
    """
    idx = pd.date_range('2025-01-06 00:00', periods=n, freq='10min', tz=tz)
    c = start + drift * np.arange(n, dtype=float)
    o = np.empty(n)
    o[0] = start
    o[1:] = c[:-1]
    hi = np.maximum(o, c) + 1.0
    lo = np.minimum(o, c) - 1.0
    return pd.DataFrame({'Open': o, 'High': hi, 'Low': lo, 'Close': c}, index=idx)


def inject_thrust(df, t, size=9.0, clv=1.0, up=True):
    """Overwrite bar t with a range-expansion bar of `size` and close-location
    `clv`. up=True anchors the bar just below/above the previous close the way
    an up-thrust would print (low = prev_close - 1); up=False mirrors it.
    Only bar t is modified — neighbours keep their trendline OHLC.
    """
    cp = df['Close'].iloc[t - 1]
    if up:
        lo = cp - 1.0
        hi = lo + size
    else:
        hi = cp + 1.0
        lo = hi - size
    df.iloc[t, df.columns.get_loc('Open')] = cp
    df.iloc[t, df.columns.get_loc('High')] = hi
    df.iloc[t, df.columns.get_loc('Low')] = lo
    df.iloc[t, df.columns.get_loc('Close')] = lo + clv * (hi - lo)
    return df


def _expected_long(df, t, p=P):
    """Recompute the exact SL/TP arithmetic for a long thrust at bar t."""
    entry = df['Close'].iloc[t]
    sl = df['Low'].iloc[t - p.SL_SWING_WIN + 1:t + 1].min()
    dist = entry - sl
    tp_dist = min(p.RR_TARGET * dist, p.TP_CAP_PCT * entry)
    return entry, sl, entry + tp_dist, tp_dist / dist


# ── (1) uptrend + giant thrust closing at its high -> exactly one long ────
def test_one_long_setup_exact_arithmetic():
    df = inject_thrust(make_trend(), 190, size=9.0, clv=1.0, up=True)
    setups = generate_setups(df)
    assert len(setups) == 1
    s = setups[0]
    assert isinstance(s, VTCSetup)
    assert (s.entry_index, s.direction, s.mode) == (190, 'long', 'continuation')
    assert s.entry_time == df.index[190]
    entry, sl, tp, rr = _expected_long(df, 190)
    assert s.entry_price == pytest.approx(entry, abs=1e-3)
    assert s.stop_loss == pytest.approx(sl, abs=1e-3)
    assert s.take_profit == pytest.approx(tp, abs=1e-3)
    assert s.rr == pytest.approx(rr, abs=0.01)
    assert s.rr == pytest.approx(P.RR_TARGET, abs=0.01)   # cap not binding here
    # ztt_sim contract fillers
    assert s.level_price == s.entry_price
    assert s.level_touches == 0
    assert s.break_index == 190
    # eligibility bounds actually hold
    assert P.SL_MIN_PCT * entry <= s.sl_distance <= P.SL_MAX_PCT * entry


# ── (2) same thrust, close mid-range (CLV 0.5) -> zero setups ─────────────
def test_midrange_close_rejected():
    df = inject_thrust(make_trend(), 190, size=9.0, clv=0.5, up=True)
    assert generate_setups(df) == []


# ── (3) thrust against the 1H bias -> zero setups ─────────────────────────
def test_thrust_against_bias_rejected():
    # uptrend (long bias only) + a DOWN thrust closing at its low
    df = inject_thrust(make_trend(), 190, size=9.0, clv=0.0, up=False)
    d = compute_indicators(df)
    assert bool(d['HTF_LONG'].iloc[190]) and not bool(d['HTF_SHORT'].iloc[190])
    assert generate_setups(df) == []


# ── (4) cooldown suppresses a second thrust 3 bars later ──────────────────
def test_cooldown_suppresses_second_thrust():
    df = inject_thrust(make_trend(), 190, size=9.0, clv=1.0, up=True)
    df = inject_thrust(df, 193, size=9.0, clv=1.0, up=True)
    setups = generate_setups(df)
    assert [s.entry_index for s in setups] == [190]


def test_cooldown_expires_after_window():
    # 7 bars apart (> COOLDOWN_BARS=6): the second, otherwise-identical thrust
    # IS emitted — proving test above suppressed a valid setup via cooldown.
    df = inject_thrust(make_trend(), 185, size=9.0, clv=1.0, up=True)
    df = inject_thrust(df, 192, size=9.0, clv=1.0, up=True)
    setups = generate_setups(df)
    assert [s.entry_index for s in setups] == [185, 192]


# ── (5) SL bounds: 3-bar swing too wide -> rejected ───────────────────────
def test_sl_wider_than_hard_cap_rejected():
    # size 30 -> SL distance ~1% of entry >> SL_MAX_PCT 0.45%; the hard cap is
    # an eligibility bound: REJECT, never tighten artificially.
    df = inject_thrust(make_trend(), 190, size=30.0, clv=1.0, up=True)
    d = compute_indicators(df)
    # the bar DOES pass the thrust + CLV + bias gates...
    rng = d['High'].iloc[190] - d['Low'].iloc[190]
    assert rng >= P.THRUST_ATR * d['ATR'].iloc[190]
    assert bool(d['HTF_LONG'].iloc[190])
    # ...and is rejected purely on the SL band
    assert generate_setups(df) == []


# ── (6) look-ahead guards ─────────────────────────────────────────────────
def _key(s):
    return (s.entry_index, s.direction, s.entry_price, s.stop_loss,
            s.take_profit, s.rr)


def test_prefix_stability_no_lookahead():
    """generate_setups(df[:k]) must match the full run for entry_index < k-1."""
    df = inject_thrust(make_trend(), 185, size=9.0, clv=1.0, up=True)
    df = inject_thrust(df, 194, size=9.0, clv=1.0, up=True)
    full = generate_setups(df)
    assert [s.entry_index for s in full] == [185, 194]
    for k in (188, 190, 196, len(df)):
        prefix = generate_setups(df.iloc[:k])
        assert ([_key(s) for s in prefix if s.entry_index < k - 1]
                == [_key(s) for s in full if s.entry_index < k - 1]), f"k={k}"


def test_1h_resample_partial_bar_leak():
    """Mutating the LAST partial-hour 10m bars must not change earlier setups.

    Bar 194 (stamp 32:20) sits inside the 1H bin labeled 33:00 (bars 193-198).
    A leaky resample (in-progress bin visible, left-labeling, or bfill) would
    let a crash in bars 196-199 flip bar 194's 1H bias. Correct impl: bar 194
    sees only completed bins <= label 32:00.
    """
    df = inject_thrust(make_trend(), 185, size=9.0, clv=1.0, up=True)
    df = inject_thrust(df, 194, size=9.0, clv=1.0, up=True)
    before = [_key(s) for s in generate_setups(df) if s.entry_index < 196]
    assert len(before) == 2

    crashed = df.copy()
    for t in range(196, 200):                      # stamps 32:40 .. 33:10
        lvl = df['Close'].iloc[t] - 80.0           # violent crash
        crashed.iloc[t, crashed.columns.get_loc('Open')] = lvl + 0.5
        crashed.iloc[t, crashed.columns.get_loc('High')] = lvl + 1.0
        crashed.iloc[t, crashed.columns.get_loc('Low')] = lvl - 1.0
        crashed.iloc[t, crashed.columns.get_loc('Close')] = lvl
    after = [_key(s) for s in generate_setups(crashed) if s.entry_index < 196]
    assert after == before


# ── (7) short-side mirror of test 1 ───────────────────────────────────────
def test_one_short_setup_exact_arithmetic():
    df = inject_thrust(make_trend(drift=-0.3), 190, size=9.0, clv=0.0, up=False)
    setups = generate_setups(df)
    assert len(setups) == 1
    s = setups[0]
    assert (s.entry_index, s.direction, s.mode) == (190, 'short', 'continuation')
    entry = df['Close'].iloc[190]
    sl = df['High'].iloc[190 - P.SL_SWING_WIN + 1:191].max()
    dist = sl - entry
    tp_dist = min(P.RR_TARGET * dist, P.TP_CAP_PCT * entry)
    assert s.entry_price == pytest.approx(entry, abs=1e-3)
    assert s.stop_loss == pytest.approx(sl, abs=1e-3)
    assert s.take_profit == pytest.approx(entry - tp_dist, abs=1e-3)
    assert s.rr == pytest.approx(P.RR_TARGET, abs=0.01)
    assert s.take_profit < s.entry_price < s.stop_loss
    assert P.SL_MIN_PCT * entry <= s.sl_distance <= P.SL_MAX_PCT * entry


# ── grid overrides go through the Params object only ──────────────────────
def test_grid_overrides_via_params():
    df = inject_thrust(make_trend(), 190, size=9.0, clv=0.78, up=True)
    assert generate_setups(df) == []                      # 0.78 < default 0.80
    relaxed = VTCParams(CLV_BAND=0.75)                    # pre-registered grid cell
    assert [s.entry_index for s in generate_setups(df, relaxed)] == [190]
    strict = VTCParams(THRUST_ATR=2.0)                    # pre-registered grid cell
    df2 = inject_thrust(make_trend(), 190, size=4.5, clv=1.0, up=True)
    assert len(generate_setups(df2)) == 1                 # passes at 1.5x
    assert generate_setups(df2, strict) == []             # fails at 2.0x


# ── integration on real data: structural invariants only ──────────────────
@pytest.fixture(scope='module')
def gold_10m_slice():
    if not DATA.exists():
        pytest.skip("10Y M10 gold cache missing")
    return pd.read_csv(DATA, index_col=0, parse_dates=True, nrows=20000)


def test_integration_structural_invariants(gold_10m_slice):
    df = gold_10m_slice
    d = compute_indicators(df)
    setups = generate_setups(df)
    assert len(setups) > 0, "expected some setups on the 20k-bar gold slice"
    prev_idx = -10 ** 9
    for s in setups:
        assert s.direction in ('long', 'short')
        assert s.mode == 'continuation'
        assert s.level_touches == 0 and s.break_index == s.entry_index
        bar = df.iloc[s.entry_index]
        # phantom-fill guard: entry reference inside the entry bar
        assert bar['Low'] - 1e-6 <= s.entry_price <= bar['High'] + 1e-6
        # thrust + bias actually held at the entry bar
        assert (bar['High'] - bar['Low']) >= P.THRUST_ATR * d['ATR'].iloc[s.entry_index] - 1e-9
        if s.direction == 'long':
            assert bool(d['HTF_LONG'].iloc[s.entry_index])
            assert s.stop_loss < s.entry_price < s.take_profit
        else:
            assert bool(d['HTF_SHORT'].iloc[s.entry_index])
            assert s.take_profit < s.entry_price < s.stop_loss
        # SL eligibility band (allow 1e-3 rounding on stored prices)
        assert P.SL_MIN_PCT * s.entry_price - 1e-2 <= s.sl_distance <= P.SL_MAX_PCT * s.entry_price + 1e-2
        # R:R floor/target and % TP cap
        assert s.rr >= P.RR_FLOOR - 0.01
        assert s.rr <= P.RR_TARGET + 0.01
        assert abs(s.take_profit - s.entry_price) <= P.TP_CAP_PCT * s.entry_price + 1e-2
        # cooldown respected
        assert s.entry_index - prev_idx > P.COOLDOWN_BARS
        prev_idx = s.entry_index
