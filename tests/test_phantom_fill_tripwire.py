"""
Phantom-fill tripwire — promoted to a COLLECTED test (2026-07-02 audit).

The 2026-06-01 audit found reversal entries filling at the broken level
without price ever trading there — impossible fills that won 95-100% and
accounted for 93-149% of every instrument's profit. The engine fix rests
reversal/limit entries as real limit orders that fill only on a genuine
touch. That regression previously lived only in non-collected `_audit_*`
harnesses; a fully green pytest run said nothing about it. These tests make
reintroducing the bug loud:

  - a resting limit that price never touches must NOT fill
  - a touched limit must fill AT the limit price, on the touch bar
  - a limit that expires unfilled must cancel (no late fills)
  - EVERY filled trade's entry must lie inside its entry bar's traded range
"""
import numpy as np
import pandas as pd
import pytest

from src.core.engine import run_backtest, REVERSAL_LIMIT_MAX_WAIT
from src.execution.entries import TradeSetup


def _df(lows, highs, closes=None):
    n = len(lows)
    idx = pd.date_range('2024-01-01', periods=n, freq='h')
    if closes is None:
        closes = [(lo + hi) / 2 for lo, hi in zip(lows, highs)]
    return pd.DataFrame({
        'Open': closes, 'High': highs, 'Low': lows,
        'Close': closes, 'Volume': 1000,
    }, index=idx)


def _limit_setup(direction, entry, sl, tp, index, size=0.1):
    return TradeSetup(
        direction=direction, entry_price=entry, stop_loss=sl, take_profit=tp,
        position_size=size, risk_reward=3.0, regime='test', index=index,
        is_limit=True,
    )


class TestRestingLimitFills:
    def test_untouched_limit_never_fills(self):
        # Price stays in 99-101 forever; a long limit at 95 must never fill.
        n = 40
        df = _df([99.0] * n, [101.0] * n)
        setup = _limit_setup('long', 95.0, 92.0, 104.0, 5)
        res = run_backtest(df, [setup], 10000.0, None, False)
        assert res.total_trades == 0, (
            "PHANTOM FILL: limit order filled although price never traded "
            "to the level — the 2026-06-01 bug is back."
        )

    def test_touched_limit_fills_at_limit_price_on_touch_bar(self):
        n = 40
        lows = [99.0] * n
        lows[10] = 94.5  # genuine touch at bar 10
        df = _df(lows, [101.0] * n)
        setup = _limit_setup('long', 95.0, 90.0, 250.0, 5)
        res = run_backtest(df, [setup], 10000.0, None, False)
        assert res.total_trades == 1
        trade = res.trades[0]
        assert trade.entry_index == 10
        assert trade.entry_price == pytest.approx(95.0)

    def test_expired_limit_cancels_no_late_fill(self):
        n = 60
        touch_bar = 5 + REVERSAL_LIMIT_MAX_WAIT + 5  # first touch AFTER expiry
        lows = [99.0] * n
        lows[touch_bar] = 94.0
        df = _df(lows, [101.0] * n)
        setup = _limit_setup('long', 95.0, 90.0, 250.0, 5)
        res = run_backtest(df, [setup], 10000.0, None, False)
        assert res.total_trades == 0, "expired limit must cancel, not fill late"

    def test_short_limit_requires_high_touch(self):
        n = 40
        df = _df([99.0] * n, [101.0] * n)
        res = run_backtest(
            df, [_limit_setup('short', 105.0, 110.0, 50.0, 5)],
            10000.0, None, False,
        )
        assert res.total_trades == 0

        highs = [101.0] * n
        highs[12] = 105.5  # touch
        df2 = _df([99.0] * n, highs)
        res2 = run_backtest(
            df2, [_limit_setup('short', 105.0, 110.0, 50.0, 5)],
            10000.0, None, False,
        )
        assert res2.total_trades == 1
        assert res2.trades[0].entry_price == pytest.approx(105.0)
        assert res2.trades[0].entry_index == 12


class TestTripwireInvariant:
    def test_every_fill_is_inside_its_entry_bar_range(self):
        # Random walk + a battery of long limits below market. Slippage OFF so
        # entry prices are exact. No fill may occur at a price the entry bar
        # never traded — the universal phantom-fill invariant.
        rng = np.random.default_rng(7)
        n = 500
        closes = 100 + np.cumsum(rng.normal(0, 0.6, n))
        highs = closes + np.abs(rng.normal(0, 0.4, n))
        lows = closes - np.abs(rng.normal(0, 0.4, n))
        df = _df(list(lows), list(highs), list(closes))

        setups = []
        for k in range(20, 420, 20):
            entry = float(closes[k] - 1.5)
            setups.append(_limit_setup('long', entry, entry - 5.0, entry + 15.0, k))

        res = run_backtest(df, setups, 100000.0, None, False)
        assert res.total_trades > 0, "battery should produce at least one fill"
        for t in res.trades:
            lo = df['Low'].iloc[t.entry_index]
            hi = df['High'].iloc[t.entry_index]
            assert lo - 1e-9 <= t.entry_price <= hi + 1e-9, (
                f"PHANTOM FILL: trade {t.trade_id} entered at {t.entry_price} "
                f"but bar {t.entry_index} traded only [{lo}, {hi}]"
            )
