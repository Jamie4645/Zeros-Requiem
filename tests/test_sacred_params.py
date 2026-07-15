"""
SACRED parameter pins — audit blocker #5 (added 2026-06-01).

CLAUDE.md: "If I catch you optimizing WMA_PERIOD, SMMA_PERIOD, or SWING_LOOKBACK,
we have a problem." Before this file the full suite passed even after a silent
WMA 9 -> 12 edit. These equality pins make any unapproved change to a core
parameter fail CI loudly.

The values pinned here are the ACTUAL values in src/regimes/sbrs_v2.py AND
must match the CLAUDE.md SACRED block — if either side moves, this test goes
red and stays red until code and canon agree again. A pin here must never be
used to bless a divergence (2026-07-02 audit finding: the previous version of
this file pinned a code-vs-canon divergence as "NOT a test failure", which
taught the drift-detector to ratify drift).

Canon reconciliation 2026-07-02:
  - RETEST_TOLERANCE_ATR 0.7 (long) / 0.3 (short) — the v2.0 ablation-validated
    values (KB 46/59); the CLAUDE.md SACRED block was stale at 0.5 and has been
    updated to match.
  - ATR_RR_CLAMP_LOW raised 0.7 -> 1.0 so the adaptive-R:R floor can never
    undercut SACRED MIN_RR=3.0 (the old call-site gate was tautological).
"""
import pytest

from src.regimes import sbrs_v2 as s


# (name, expected) — the three truly sacred trend/structure params first.
SACRED = [
    ("WMA_PERIOD", 9),
    ("SMMA_PERIOD", 7),
    ("SWING_LOOKBACK", 20),
    ("SWING_WINDOW", 3),
    ("MIN_RR", 3.0),
    ("RETEST_TOLERANCE_ATR", 0.7),        # matches CLAUDE.md SACRED block (reconciled 2026-07-02)
    ("RETEST_TOLERANCE_ATR_SHORT", 0.3),  # matches CLAUDE.md SACRED block (reconciled 2026-07-02)
]

# Tunable params: locked to current values so changes are deliberate + reviewed.
TUNABLE = [
    ("ATR_PERIOD", 14),
    ("MAX_RETEST_WAIT", 10),
    ("SL_BUFFER_ATR", 0.3),
    ("BE_TRIGGER_R", 1.5),
    ("MAX_HOLD_BARS", 40),
    ("MA_CROSS_LOOKBACK", 10),
]

# Confluence + per-asset R:R floors that define the v2 edge.
EDGE = [
    ("MIN_RR_INDICES", 2.0),
    ("MIN_RR_FOREX", 2.5),
    ("MIN_RR_CRYPTO", 2.5),
    ("CONFLUENCE_MIN_WITH_TREND", 1.0),
    ("CONFLUENCE_MIN_COUNTER_TREND", 2.0),
    ("COUNTER_TREND_RR_MIN", 2.0),
    ("ATR_RR_CLAMP_LOW", 1.0),  # 2026-07-02 audit: floor may never undercut SACRED MIN_RR
]


@pytest.mark.parametrize("name,expected", SACRED)
def test_sacred_params_unchanged(name, expected):
    actual = getattr(s, name)
    assert actual == pytest.approx(expected), (
        f"SACRED parameter {name} changed from {expected} to {actual}. "
        f"This requires EXPLICIT user approval (see CLAUDE.md param-guard)."
    )


@pytest.mark.parametrize("name,expected", TUNABLE)
def test_tunable_params_pinned(name, expected):
    actual = getattr(s, name)
    assert actual == pytest.approx(expected), (
        f"Tunable parameter {name} changed from {expected} to {actual}; "
        f"confirm this was a deliberate, reviewed change."
    )


@pytest.mark.parametrize("name,expected", EDGE)
def test_edge_params_pinned(name, expected):
    actual = getattr(s, name)
    assert actual == pytest.approx(expected), (
        f"Edge parameter {name} changed from {expected} to {actual}."
    )
