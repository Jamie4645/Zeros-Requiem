"""
SBRS Gold Backtest — Integration Tests (pytest edition)

Validates that the SBRS strategy produces setups and that backtesting
returns reasonable performance metrics on Gold 1H data.

Run: python -m pytest tests/test_gold_backtest.py -v
"""

import pytest


class TestGoldSBRSBacktest:
    """Integration tests for Gold SBRS strategy + backtest engine."""

    def test_gold_1h_produces_setups(self, gold_1h_data):
        """SBRS should generate at least one trade setup on 6 months of Gold 1H."""
        from src.regimes.sbrs_gold import analyze_gold_sbrs

        setups = analyze_gold_sbrs(gold_1h_data, equity=10000.0)
        assert len(setups) > 0, (
            f"Expected at least 1 setup on 6mo Gold 1H data, got {len(setups)}"
        )

    def test_gold_backtest_runs(self, sample_backtest_result):
        """Backtest should execute trades (total_trades > 0)."""
        assert sample_backtest_result.total_trades > 0, (
            f"Expected trades > 0, got {sample_backtest_result.total_trades}"
        )

    def test_gold_profit_factor_reasonable(self, sample_backtest_result):
        """PF < 10 (not absurd); if PF > 0 on this slice, expect 0.5–10. PF can be 0 if all losses."""
        pf = sample_backtest_result.profit_factor
        assert pf == pf, "profit_factor is NaN"
        assert pf < 10 or pf == float("inf")
        if pf > 0:
            assert 0.5 < pf < 10, (
                f"Profit factor {pf:.2f} is outside reasonable range (0.5, 10)"
            )

    def test_gold_max_drawdown_acceptable(self, sample_backtest_result):
        """Max drawdown should be under 50% (sanity check, not the 15% target)."""
        dd = sample_backtest_result.max_drawdown_pct
        assert dd < 50, (
            f"Max drawdown {dd:.2f}% exceeds 50% sanity threshold"
        )
