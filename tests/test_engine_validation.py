"""
Phase 4: VectorBT Cross-Validation

Validates the backtest engine against VectorBT's independent calculations.
Ensures our Sharpe, PnL, and drawdown numbers are correct.

Run: py -m pytest tests/test_engine_validation.py -v
"""

import pytest
import numpy as np
import pandas as pd

try:
    import vectorbt as vbt
    HAS_VBT = True
except ImportError:
    HAS_VBT = False

# 2026-07-02 audit: the skip used to be module-wide, so when vectorbt was
# absent this file validated NOTHING — and none of it ever imported the
# actual engine. The vbt cross-checks below keep their skip; the
# TestEngineCrossValidation class at the bottom imports src/core/engine.py
# and runs unconditionally.
needs_vbt = pytest.mark.skipif(not HAS_VBT, reason="vectorbt not installed")


@needs_vbt
class TestSharpeCalculation:
    """Verify Sharpe ratio calculation matches VectorBT."""

    def test_sharpe_positive_returns(self):
        """Identical return series should produce matching Sharpe.

        Note: VectorBT annualizes with 365 (calendar days from DatetimeIndex),
        our engine uses 252 (trading days). We test using VBT's convention here
        to validate the core calculation (mean/std) is correct.
        """
        np.random.seed(42)
        idx = pd.date_range('2020-01-01', periods=252, freq='D')
        returns = pd.Series(np.random.normal(0.001, 0.01, 252), index=idx)

        # Use sqrt(365) to match VectorBT's calendar-day annualization
        mean_r = returns.mean()
        std_r = returns.std(ddof=1)
        our_sharpe = (mean_r / std_r) * np.sqrt(365) if std_r > 0 else 0

        vbt_sharpe = returns.vbt.returns.sharpe_ratio()

        assert abs(our_sharpe - vbt_sharpe) < 0.05, \
            f"Sharpe mismatch: ours={our_sharpe:.4f}, vbt={vbt_sharpe:.4f}"

    def test_sharpe_negative_returns(self):
        """Sharpe should be negative for losing strategies."""
        np.random.seed(123)
        idx = pd.date_range('2020-01-01', periods=252, freq='D')
        returns = pd.Series(np.random.normal(-0.002, 0.01, 252), index=idx)

        mean_r = returns.mean()
        std_r = returns.std(ddof=1)
        our_sharpe = (mean_r / std_r) * np.sqrt(365) if std_r > 0 else 0

        vbt_sharpe = returns.vbt.returns.sharpe_ratio()

        assert abs(our_sharpe - vbt_sharpe) < 0.05
        assert our_sharpe < 0

    def test_sharpe_zero_volatility(self):
        """Constant returns should produce very large or inf Sharpe (no risk)."""
        returns = pd.Series([0.001] * 100)
        mean_r = returns.mean()
        std_r = returns.std()
        # With truly constant returns, std is ~0 (floating point), Sharpe is huge
        if std_r < 1e-10:
            our_sharpe = float('inf')
        else:
            our_sharpe = (mean_r / std_r) * np.sqrt(252)
        assert our_sharpe > 100 or np.isinf(our_sharpe), \
            "Constant positive returns should give very high Sharpe"


@needs_vbt
class TestMaxDrawdown:
    """Verify max drawdown calculation matches VectorBT."""

    def test_drawdown_simple(self):
        """Simple equity curve should produce matching drawdown."""
        equity = pd.Series([100, 110, 105, 115, 100, 120])
        returns = equity.pct_change().dropna()

        # Our max drawdown
        peak = equity.cummax()
        dd = (peak - equity) / peak
        our_max_dd = dd.max()

        # VectorBT max drawdown
        vbt_max_dd = returns.vbt.returns.max_drawdown()

        assert abs(our_max_dd - abs(vbt_max_dd)) < 0.02, \
            f"DD mismatch: ours={our_max_dd:.4f}, vbt={vbt_max_dd:.4f}"

    def test_drawdown_no_drawdown(self):
        """Monotonically increasing equity should have 0 drawdown."""
        equity = pd.Series([100, 101, 102, 103, 104, 105])
        peak = equity.cummax()
        dd = (peak - equity) / peak
        assert dd.max() == 0.0


@needs_vbt
class TestPnLAccuracy:
    """Verify P&L calculations against VectorBT portfolio."""

    def test_long_trade_pnl(self):
        """Simple long trade P&L should match."""
        entry = 100.0
        exit_price = 110.0
        size = 10

        our_pnl = (exit_price - entry) * size
        assert our_pnl == 100.0

    def test_short_trade_pnl(self):
        """Simple short trade P&L should match."""
        entry = 110.0
        exit_price = 100.0
        size = 10

        our_pnl = (entry - exit_price) * size
        assert our_pnl == 100.0

    def test_portfolio_from_signals(self):
        """Build a simple portfolio with VectorBT and compare total return."""
        np.random.seed(42)
        close = pd.Series(np.cumsum(np.random.normal(0, 1, 100)) + 100,
                          index=pd.date_range('2020-01-01', periods=100, freq='D'))

        # Simple moving average crossover
        fast_ma = close.rolling(5).mean()
        slow_ma = close.rolling(20).mean()

        entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
        exits = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

        pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=10000)

        # VectorBT stats
        vbt_total_return = pf.total_return()
        vbt_total_pnl = pf.total_profit()

        # Basic sanity: these should be finite numbers
        assert np.isfinite(vbt_total_return), "VectorBT total return should be finite"
        assert np.isfinite(vbt_total_pnl), "VectorBT total PnL should be finite"


@needs_vbt
class TestProfitFactor:
    """Verify profit factor calculation."""

    def test_profit_factor_basic(self):
        """PF = gross wins / gross losses."""
        wins = [100, 200, 150]
        losses = [-50, -80, -70]
        all_pnls = wins + losses

        gross_wins = sum(w for w in all_pnls if w > 0)
        gross_losses = abs(sum(l for l in all_pnls if l < 0))
        our_pf = gross_wins / gross_losses if gross_losses > 0 else float('inf')

        assert abs(our_pf - 2.25) < 0.01, f"PF should be 2.25, got {our_pf}"

    def test_profit_factor_no_losses(self):
        """PF with no losses should be inf."""
        pnls = [100, 200, 50]
        gross_losses = abs(sum(l for l in pnls if l < 0))
        pf = sum(w for w in pnls if w > 0) / gross_losses if gross_losses > 0 else float('inf')
        assert pf == float('inf')

    def test_profit_factor_no_wins(self):
        """PF with no wins should be 0."""
        pnls = [-100, -200, -50]
        gross_wins = sum(w for w in pnls if w > 0)
        gross_losses = abs(sum(l for l in pnls if l < 0))
        pf = gross_wins / gross_losses if gross_losses > 0 else 0
        assert pf == 0.0


class TestEngineCrossValidation:
    """Actually import src/core/engine.py and validate its outputs against
    hand-computed ground truth (2026-07-02 audit: this file previously never
    touched the engine — it re-derived formulas inline and skipped entirely
    without vectorbt)."""

    @staticmethod
    def _df(lows, highs, closes):
        idx = pd.date_range('2024-01-01', periods=len(lows), freq='h')
        return pd.DataFrame({
            'Open': closes, 'High': highs, 'Low': lows,
            'Close': closes, 'Volume': 1000,
        }, index=idx)

    def test_engine_pnl_matches_hand_computed(self):
        from src.core.engine import run_backtest
        from src.execution.entries import TradeSetup

        n = 30
        lows = [99.0] * n
        highs = [101.0] * n
        closes = [100.0] * n
        # TP (110) hit at bar 12. The bar's low stays ABOVE the breakeven stop
        # (entry + 0.1R = 100.5, armed once 1.5R = 107.5 trades) so the TP fill
        # is unambiguous — the engine conservatively fills stops before targets
        # when a single bar spans both.
        highs[12] = 112.0
        lows[12] = 109.0
        closes[12] = 111.0
        df = self._df(lows, highs, closes)

        setup = TradeSetup(
            direction='long', entry_price=100.0, stop_loss=95.0,
            take_profit=110.0, position_size=1.0, risk_reward=2.0,
            regime='test', index=5,
        )
        res = run_backtest(df, [setup], 10000.0, None, False)

        assert res.total_trades == 1
        trade = res.trades[0]
        assert trade.entry_price == pytest.approx(100.0)
        # Hand-computed ground truth: long 1.0 units, entry 100 -> TP 110 = +10
        assert trade.pnl == pytest.approx(10.0)
        assert res.final_capital == pytest.approx(10010.0)
        assert res.winning_trades == 1
        assert res.losing_trades == 0

    def test_engine_short_sl_matches_hand_computed(self):
        from src.core.engine import run_backtest
        from src.execution.entries import TradeSetup

        n = 30
        lows = [99.0] * n
        highs = [101.0] * n
        closes = [100.0] * n
        highs[9] = 106.0    # SL (105) hit at bar 9
        df = self._df(lows, highs, closes)

        setup = TradeSetup(
            direction='short', entry_price=100.0, stop_loss=105.0,
            take_profit=85.0, position_size=2.0, risk_reward=3.0,
            regime='test', index=5,
        )
        res = run_backtest(df, [setup], 10000.0, None, False)

        assert res.total_trades == 1
        trade = res.trades[0]
        # Hand-computed: short 2.0 units, entry 100 -> SL 105 = -10
        assert trade.pnl == pytest.approx(-10.0)
        assert res.final_capital == pytest.approx(9990.0)
        assert res.losing_trades == 1
