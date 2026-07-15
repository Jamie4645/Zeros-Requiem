"""
Walk-forward regression guards (2026-07-02 audit).

Walk-forward consistency is the promotion gate for every strategy (75%+
windows profitable), yet walk_forward.py had NO collected tests. Guards:

  - windows are sequential, non-overlapping, and cover every bar exactly once
  - the drawdown circuit-breaker state carries across windows as a relative
    drawdown fraction (the audit found each window built a fresh RiskManager,
    resetting peak_equity and silently neutralizing the breaker — the real
    R6-5 mechanism; WF results were systematically optimistic vs continuous)
  - run_backtest honours initial_peak_equity
"""
from types import SimpleNamespace

import pandas as pd
import pytest

import src.core.walk_forward as wf_mod
from src.core.engine import run_backtest


def _df(n=300, start='2020-01-01'):
    idx = pd.date_range(start, periods=n, freq='h')
    return pd.DataFrame({
        'Open': 100.0, 'High': 101.0, 'Low': 99.0,
        'Close': 100.0, 'Volume': 1000,
    }, index=idx)


class TestWindowSplit:
    def test_sequential_non_overlapping_full_coverage(self):
        df = _df(305)
        wins = wf_mod.split_into_windows(df, n_windows=4, min_bars=50)
        seen = []
        for w in wins:
            seen.extend(list(w.index))
        assert seen == list(df.index), (
            "windows must cover every bar exactly once, in order — any gap or "
            "overlap corrupts the consistency score"
        )

    def test_window_count_adapts_to_min_bars(self):
        df = _df(120)
        wins = wf_mod.split_into_windows(df, n_windows=8, min_bars=50)
        assert len(wins) >= 2
        assert all(len(w) >= 50 for w in wins)


class TestPeakEquityCarry:
    def test_engine_seeds_peak(self):
        df = _df(50)
        res = run_backtest(df, [], 10000.0, None, False,
                           initial_peak_equity=12500.0)
        assert res.risk_stats['peak_equity'] == 12500.0

    def test_engine_ignores_peak_below_capital(self):
        df = _df(50)
        res = run_backtest(df, [], 10000.0, None, False,
                           initial_peak_equity=8000.0)
        assert res.risk_stats['peak_equity'] == 10000.0

    def test_relative_drawdown_carries_across_windows(self, monkeypatch):
        calls = []

        def fake_run_backtest(df, setups, initial_capital, risk_config,
                              apply_slippage, sbrs_indicators=None,
                              initial_peak_equity=None):
            calls.append(initial_peak_equity)
            # Every fake window peaks at 10,000 and ends at 9,000 -> 10% dd.
            return SimpleNamespace(
                final_capital=9000.0,
                risk_stats={'peak_equity': 10000.0},
                total_pnl=-1000.0, total_trades=0, win_rate=0.0,
                profit_factor=0.0, sharpe_ratio=0.0, expectancy=0.0,
            )

        monkeypatch.setattr(wf_mod, 'run_backtest', fake_run_backtest)
        wf_mod.run_walk_forward(
            _df(300), analyze_fn=lambda d, c, r: [], n_windows=3,
            initial_capital=10000.0, min_bars=50,
        )
        assert len(calls) == 3
        assert calls[0] is None, "first window has no carried drawdown"
        assert calls[1] == pytest.approx(10000.0 / 0.9), (
            "second window must resume at the 10% relative drawdown the first "
            "window ended in (peak seeded to capital/(1-dd))"
        )
        assert calls[2] == pytest.approx(10000.0 / 0.9)
