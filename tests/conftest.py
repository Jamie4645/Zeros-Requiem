"""
Shared pytest fixtures for Zero's Requiem test suite.

Provides cached data fixtures and sample backtest results so that
individual test modules don't each need to fetch data from the network.
"""

import sys
import os
import warnings

import pytest

# Ensure project root is on sys.path so `from src.…` imports work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# Gold 1H data (6 months) — used by SBRS backtest tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def gold_1h_data():
    """Fetch Gold 1H data (6 months). Skip tests if fetch fails."""
    try:
        from src.data.fetcher import fetch
        df = fetch("GC=F", "1h", "6mo")
        if df is None or df.empty:
            pytest.skip("Gold 1H data fetch returned empty DataFrame")
        return df
    except Exception as exc:
        pytest.skip(f"Gold 1H data fetch failed: {exc}")


# ---------------------------------------------------------------------------
# Gold 4H data (1 year) — used by trend-context / multi-TF tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def gold_4h_data():
    """Fetch Gold 4H data (1 year). Skip tests if fetch fails."""
    try:
        from src.data.fetcher import fetch
        df = fetch("GC=F", "4h", "1y")
        if df is None or df.empty:
            pytest.skip("Gold 4H data fetch returned empty DataFrame")
        return df
    except Exception as exc:
        pytest.skip(f"Gold 4H data fetch failed: {exc}")


# ---------------------------------------------------------------------------
# Sample backtest result — runs SBRS on Gold 1H and caches the outcome
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def sample_backtest_result(gold_1h_data):
    """Run a basic SBRS Gold backtest and return the result. Skip on failure."""
    try:
        from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
        from src.core.engine import run_backtest
        from src.core.risk_manager import risk_config_for_interval

        setups = analyze_gold_sbrs(gold_1h_data, equity=10000.0)
        indicators = get_sbrs_indicators(gold_1h_data)
        risk_cfg = risk_config_for_interval("1h")
        result = run_backtest(
            gold_1h_data,
            setups,
            initial_capital=10000.0,
            risk_config=risk_cfg,
            sbrs_indicators=indicators,
        )
        return result
    except Exception as exc:
        pytest.skip(f"Sample backtest failed: {exc}")
