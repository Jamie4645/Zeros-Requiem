"""
Round 5 Y1 — index slippage under-cost fix.

Pre-fix, NASDAQ (~$16k) and DAX (~$21k) hit the `entry_price > 1000` bracket
with slip = 1.5 * 0.1 = $0.15, under-costing by 3-13x versus real spread+impact
(0.5-2.0 points/side). Council inserted a new `entry_price > 5000` bracket
with slip = 1.5 * 1.0 = 1.5 index points.

These tests:
  1. lock in the NEW behaviour for index-priced instruments (>5000)
  2. regression-guard Gold behaviour (>1000 but <=5000)
  3. regression-guard forex behaviour (>0.01, ~1.0)
"""
import pytest

from src.core.risk_manager import RiskConfig, RiskManager


@pytest.fixture
def rm():
    return RiskManager(RiskConfig(slippage_pips=1.5), initial_capital=10_000)


def test_index_slip_applied_at_5000_plus(rm):
    """NASDAQ at $15,500 → long entry should have 1.5-point adverse slip."""
    entry = 15_500.0
    filled = rm.apply_slippage(entry, 'long')
    assert filled == pytest.approx(entry + 1.5, rel=1e-9), (
        f"NDX-like entry at {entry} must slip by 1.5 points (1.5 * 1.0), "
        f"got slip={filled - entry}"
    )


def test_index_slip_short_side(rm):
    entry = 21_000.0  # DAX-like
    filled = rm.apply_slippage(entry, 'short')
    assert filled == pytest.approx(entry - 1.5, rel=1e-9)


def test_gold_slip_unchanged_regression(rm):
    """Gold at $2,050 must STILL slip by $0.15 (1.5 * 0.1) — no regression."""
    entry = 2_050.0
    filled = rm.apply_slippage(entry, 'long')
    assert filled == pytest.approx(entry + 0.15, rel=1e-9), (
        f"Gold regression: expected $0.15 slip at entry {entry}, got {filled - entry}"
    )


def test_forex_slip_unchanged_regression(rm):
    """EURUSD at 1.265 must STILL slip by 0.00015 (1.5 * 0.0001)."""
    entry = 1.265
    filled = rm.apply_slippage(entry, 'long')
    assert filled == pytest.approx(entry + 0.00015, rel=1e-6)


def test_boundary_5000_uses_lower_bracket(rm):
    """Exactly $5,000 should still hit the Gold bracket (strict >5000 threshold)."""
    filled = rm.apply_slippage(5_000.0, 'long')
    assert filled == pytest.approx(5_000.0 + 0.15, rel=1e-9)


def test_boundary_5001_uses_index_bracket(rm):
    """Just above $5,000 triggers the new index bracket."""
    filled = rm.apply_slippage(5_001.0, 'long')
    assert filled == pytest.approx(5_001.0 + 1.5, rel=1e-9)
