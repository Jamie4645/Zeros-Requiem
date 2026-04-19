"""
Tests for Smart Money Indicators (SBRS 2.0)

Comprehensive tests for all 8 functions in src/indicators/smart_money.py.
Uses synthetic OHLC DataFrames to validate correctness and look-ahead safety.
"""

import pytest
import pandas as pd
import numpy as np

from src.indicators.smart_money import (
    detect_fvg_bullish,
    detect_fvg_bearish,
    detect_fvg_near_level,
    detect_liquidity_sweep,
    detect_ma_whipsaw,
    detect_bollinger_squeeze,
    count_level_touches,
    detect_false_breakout,
)


def _make_df(ohlc_rows):
    """Helper: create DataFrame from list of (Open, High, Low, Close) tuples."""
    df = pd.DataFrame(ohlc_rows, columns=['Open', 'High', 'Low', 'Close'])
    df.index = pd.date_range('2025-01-01', periods=len(df), freq='1h')
    return df


# ============================================================
# Fair Value Gap — Bullish
# ============================================================

class TestFVGBullish:
    def test_bullish_fvg_detected(self):
        """Bar[0].High=100, Bar[2].Low=102 => gap (100, 102)."""
        rows = [
            (99, 100, 98, 99),   # bar 0: High=100
            (100, 103, 99, 101), # bar 1: middle candle
            (102, 105, 102, 104),# bar 2: Low=102 > bar[0].High=100
            (104, 106, 103, 105),# bar 3
            (105, 107, 104, 106),# bar 4
        ]
        df = _make_df(rows)
        result = detect_fvg_bullish(df, current_idx=4, lookback=10)
        assert result is not None
        idx, gap_low, gap_high = result
        assert idx == 1
        assert gap_low == 100.0
        assert gap_high == 102.0

    def test_no_bullish_fvg_when_overlapping(self):
        """Overlapping candles => no gap."""
        rows = [
            (99, 102, 98, 100),  # bar 0: High=102
            (100, 103, 99, 101), # bar 1
            (101, 104, 101, 103),# bar 2: Low=101 < bar[0].High=102 => no gap
            (103, 105, 102, 104),# bar 3
            (104, 106, 103, 105),# bar 4
        ]
        df = _make_df(rows)
        result = detect_fvg_bullish(df, current_idx=4, lookback=10)
        assert result is None

    def test_bullish_fvg_lookback_limit(self):
        """FVG outside lookback window should not be found."""
        rows = [
            (99, 100, 98, 99),   # bar 0: FVG candle 1
            (100, 103, 99, 101), # bar 1
            (102, 105, 102, 104),# bar 2: FVG exists here
        ] + [(104, 106, 103, 105)] * 15  # bars 3-17: filler
        df = _make_df(rows)
        # lookback=3 means we only check recent 3 bars; FVG is too far back
        result = detect_fvg_bullish(df, current_idx=17, lookback=3)
        assert result is None


# ============================================================
# Fair Value Gap — Bearish
# ============================================================

class TestFVGBearish:
    def test_bearish_fvg_detected(self):
        """Bar[0].Low=110, Bar[2].High=105 => gap (110, 105)."""
        rows = [
            (112, 115, 110, 112),  # bar 0: Low=110
            (108, 111, 106, 109),  # bar 1: middle candle
            (104, 105, 102, 103),  # bar 2: High=105 < bar[0].Low=110 => gap
            (107, 109, 106, 108),  # bar 3: no gap with bar 1
            (109, 111, 108, 110),  # bar 4: no gap with bar 2
        ]
        df = _make_df(rows)
        result = detect_fvg_bearish(df, current_idx=4, lookback=10)
        assert result is not None
        idx, gap_high, gap_low = result
        assert idx == 1
        assert gap_high == 110.0
        assert gap_low == 105.0

    def test_no_bearish_fvg_when_overlapping(self):
        """No gap if candles overlap."""
        rows = [
            (103, 105, 100, 103),  # bar 0: Low=100
            (101, 103, 99, 101),   # bar 1
            (99, 101, 97, 98),     # bar 2: High=101 > bar[0].Low=100 => no gap
            (98, 99, 96, 97),
            (97, 98, 95, 96),
        ]
        df = _make_df(rows)
        result = detect_fvg_bearish(df, current_idx=4, lookback=10)
        assert result is None


# ============================================================
# FVG Near Level
# ============================================================

class TestFVGNearLevel:
    def test_bullish_fvg_near_level(self):
        """Bullish FVG gap (100, 102) near level=101, ATR=2 => True."""
        rows = [
            (99, 100, 98, 99),
            (100, 103, 99, 101),
            (102, 105, 102, 104),
            (104, 106, 103, 105),
            (105, 107, 104, 106),
        ]
        df = _make_df(rows)
        result = detect_fvg_near_level(
            df, current_idx=4, level=101.0, direction='long',
            atr_val=2.0, lookback=10, proximity_atr=1.0
        )
        assert result == True

    def test_bullish_fvg_far_from_level(self):
        """Bullish FVG gap (100, 102) far from level=200 => False."""
        rows = [
            (99, 100, 98, 99),
            (100, 103, 99, 101),
            (102, 105, 102, 104),
            (104, 106, 103, 105),
            (105, 107, 104, 106),
        ]
        df = _make_df(rows)
        result = detect_fvg_near_level(
            df, current_idx=4, level=200.0, direction='long',
            atr_val=2.0, lookback=10, proximity_atr=1.0
        )
        assert result == False

    def test_bearish_fvg_near_level(self):
        """Bearish FVG near the given level."""
        rows = [
            (103, 105, 102, 103),
            (101, 103, 100, 101),
            (99, 100, 97, 98),
            (98, 99, 96, 97),
            (97, 98, 95, 96),
        ]
        df = _make_df(rows)
        result = detect_fvg_near_level(
            df, current_idx=4, level=101.0, direction='short',
            atr_val=2.0, lookback=10, proximity_atr=1.0
        )
        assert result == True


# ============================================================
# Liquidity Sweep
# ============================================================

class TestLiquiditySweep:
    def _make_sweep_data(self):
        """Swing low at bar 2 (value=100), sweep at bar 5, reversal at bar 5."""
        rows = [
            (103, 105, 103, 104),  # bar 0
            (104, 106, 103, 105),  # bar 1
            (102, 103, 100, 101),  # bar 2: swing low = 100
            (101, 104, 101, 103),  # bar 3
            (103, 105, 102, 104),  # bar 4
            (102, 103, 99, 101),   # bar 5: Low=99 < 100 (sweep), Close=101 > 100 (reversal)
            (101, 104, 100, 103),  # bar 6
        ]
        df = _make_df(rows)
        # Manually set swing masks
        swing_low_mask = pd.Series([False] * 7, index=df.index)
        swing_low_mask.iloc[2] = True
        swing_high_mask = pd.Series([False] * 7, index=df.index)
        return df, swing_high_mask, swing_low_mask

    def test_liquidity_sweep_long(self):
        df, sh_mask, sl_mask = self._make_sweep_data()
        result = detect_liquidity_sweep(
            df, current_idx=6, swing_high_mask=sh_mask, swing_low_mask=sl_mask,
            direction='long', lookback=20, sweep_confirm_bars=3
        )
        assert result == True

    def test_no_sweep_when_price_keeps_going(self):
        """Price breaks below swing low and stays below => not a sweep."""
        rows = [
            (103, 105, 103, 104),
            (104, 106, 103, 105),
            (102, 103, 100, 101),  # bar 2: swing low = 100
            (101, 104, 101, 103),
            (103, 105, 102, 104),
            (99, 100, 97, 98),     # bar 5: breaks below and closes below
            (97, 98, 95, 96),      # bar 6: stays below
        ]
        df = _make_df(rows)
        sl_mask = pd.Series([False] * 7, index=df.index)
        sl_mask.iloc[2] = True
        sh_mask = pd.Series([False] * 7, index=df.index)

        result = detect_liquidity_sweep(
            df, current_idx=6, swing_high_mask=sh_mask, swing_low_mask=sl_mask,
            direction='long', lookback=20, sweep_confirm_bars=3
        )
        assert result == False

    def test_liquidity_sweep_short(self):
        """Sweep above swing high then reversal below."""
        rows = [
            (97, 98, 96, 97),
            (96, 97, 95, 96),
            (98, 105, 97, 100),   # bar 2: swing high = 105
            (100, 103, 99, 101),
            (101, 102, 100, 101),
            (103, 107, 102, 104), # bar 5: High=107 > 105 (sweep), Close=104 < 105 (reversal)
            (102, 103, 101, 102),
        ]
        df = _make_df(rows)
        sh_mask = pd.Series([False] * 7, index=df.index)
        sh_mask.iloc[2] = True
        sl_mask = pd.Series([False] * 7, index=df.index)

        result = detect_liquidity_sweep(
            df, current_idx=6, swing_high_mask=sh_mask, swing_low_mask=sl_mask,
            direction='short', lookback=20, sweep_confirm_bars=3
        )
        assert result == True


# ============================================================
# MA Whipsaw Detection
# ============================================================

class TestMAWhipsaw:
    def test_whipsaw_detected(self):
        """WMA crosses SMMA 4 times in 15 bars => whipsaw (> 2 crosses)."""
        # WMA oscillates clearly above and below SMMA (no zero crossings)
        wma_vals = pd.Series([
            9, 10, 13, 10, 9, 13, 10, 9, 13, 10,
            9, 13, 10, 9, 13
        ], dtype=float)
        smma_vals = pd.Series([11.0] * 15, dtype=float)
        # diff = wma - smma: -2, -1, 2, -1, -2, 2, -1, -2, 2, -1, -2, 2, -1, -2, 2
        # Strict sign changes: 1->2 (-→+), 2->3 (+→-), 4->5 (-→+), 5->6 (+→-), etc.
        result = detect_ma_whipsaw(wma_vals, smma_vals, current_idx=14, lookback=15, max_crosses=2)
        assert result == True

    def test_clean_single_cross(self):
        """WMA crosses SMMA once => not whipsaw."""
        wma_vals = pd.Series([
            8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22
        ], dtype=float)
        smma_vals = pd.Series([15.0] * 15, dtype=float)
        # diff: -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7
        # One cross around bar 7->8
        result = detect_ma_whipsaw(wma_vals, smma_vals, current_idx=14, lookback=15, max_crosses=2)
        assert result == False

    def test_no_crosses(self):
        """WMA always above SMMA => no whipsaw."""
        wma_vals = pd.Series([20.0] * 15, dtype=float)
        smma_vals = pd.Series([10.0] * 15, dtype=float)
        result = detect_ma_whipsaw(wma_vals, smma_vals, current_idx=14, lookback=15, max_crosses=2)
        assert result == False


# ============================================================
# Bollinger Squeeze
# ============================================================

class TestBollingerSqueeze:
    def test_squeeze_detected(self):
        """Very tight recent bands vs historically wide bands => squeeze."""
        np.random.seed(42)
        # Wide volatility followed by very tight
        wide = np.random.normal(100, 10, 60)
        tight = np.random.normal(100, 0.5, 20)
        prices = np.concatenate([wide, tight])
        rows = [(p, p + 0.1, p - 0.1, p) for p in prices]
        df = _make_df(rows)

        result = detect_bollinger_squeeze(
            df, current_idx=len(df) - 1,
            bb_period=20, bb_std=2.0, squeeze_threshold=0.5, lookback=50
        )
        assert result == True

    def test_no_squeeze_with_wide_bands(self):
        """Consistently volatile => no squeeze."""
        np.random.seed(42)
        prices = np.random.normal(100, 10, 80)
        rows = [(p, p + 5, p - 5, p) for p in prices]
        df = _make_df(rows)

        result = detect_bollinger_squeeze(
            df, current_idx=len(df) - 1,
            bb_period=20, bb_std=2.0, squeeze_threshold=0.5, lookback=50
        )
        assert result == False

    def test_insufficient_data(self):
        """Not enough data => False."""
        rows = [(100, 101, 99, 100)] * 10
        df = _make_df(rows)
        result = detect_bollinger_squeeze(df, current_idx=9, bb_period=20, lookback=50)
        assert result == False


# ============================================================
# Level Touches
# ============================================================

class TestLevelTouches:
    def test_three_touches_with_gaps(self):
        """Price touches level=100 three times with gaps between."""
        rows = [
            (98, 100.2, 97, 98),   # bar 0: High near 100 => touch
            (97, 98, 96, 97),      # bar 1: away
            (96, 97, 95, 96),      # bar 2: away
            (95, 96, 94, 95),      # bar 3: away (gap of 3 bars)
            (97, 100.1, 96, 98),   # bar 4: High near 100 => touch
            (98, 99, 97, 98),      # bar 5: away
            (97, 98, 96, 97),      # bar 6: away
            (96, 97, 95, 96),      # bar 7: away (gap of 3 bars)
            (98, 100.3, 97, 99),   # bar 8: High near 100 => touch
            (99, 101, 98, 100),    # bar 9
        ]
        df = _make_df(rows)
        count = count_level_touches(
            df, level=100.0, current_idx=9, atr_val=2.0,
            lookback=50, tolerance_atr=0.3
        )
        assert count == 3

    def test_consecutive_bars_counted_once(self):
        """Consecutive touches within 3 bars should count as one."""
        rows = [
            (99, 100.1, 98, 99),   # bar 0: touch
            (99, 100.2, 98, 99),   # bar 1: still near (< 3 bars gap)
            (99, 100.1, 98, 99),   # bar 2: still near (< 3 bars gap)
            (95, 96, 94, 95),      # bar 3: away
            (94, 95, 93, 94),      # bar 4: away
            (93, 94, 92, 93),      # bar 5: away
        ]
        df = _make_df(rows)
        count = count_level_touches(
            df, level=100.0, current_idx=5, atr_val=2.0,
            lookback=50, tolerance_atr=0.3
        )
        assert count == 1


# ============================================================
# False Breakout
# ============================================================

class TestFalseBreakout:
    def test_false_breakout_long(self):
        """Price closes above level then back below within 3 bars."""
        rows = [
            (99, 100, 98, 99),    # bar 0
            (100, 102, 99, 101),  # bar 1: close above 100
            (101, 102, 98, 99),   # bar 2: close back below 100
            (99, 100, 97, 98),    # bar 3
            (98, 99, 96, 97),     # bar 4
        ]
        df = _make_df(rows)
        result = detect_false_breakout(
            df, level=100.0, direction='long',
            current_idx=4, atr_val=2.0, lookback=30
        )
        assert result == True

    def test_valid_breakout_long(self):
        """Price closes above level and stays => not a false breakout."""
        rows = [
            (99, 100, 98, 99),
            (100, 102, 99, 101),  # close above 100
            (101, 103, 100, 102), # stays above
            (102, 104, 101, 103), # stays above
            (103, 105, 102, 104), # stays above
        ]
        df = _make_df(rows)
        result = detect_false_breakout(
            df, level=100.0, direction='long',
            current_idx=4, atr_val=2.0, lookback=30
        )
        assert result == False

    def test_false_breakout_short(self):
        """Price closes below level then back above within 3 bars."""
        rows = [
            (101, 102, 100, 101),
            (100, 101, 98, 99),   # close below 100
            (99, 101, 98, 101),   # close back above 100
            (101, 102, 100, 101),
            (101, 103, 100, 102),
        ]
        df = _make_df(rows)
        result = detect_false_breakout(
            df, level=100.0, direction='short',
            current_idx=4, atr_val=2.0, lookback=30
        )
        assert result == True

    def test_valid_breakout_short(self):
        """Price closes below and stays => not false breakout."""
        rows = [
            (101, 102, 100, 101),
            (100, 101, 98, 99),   # close below 100
            (99, 100, 97, 98),    # stays below
            (98, 99, 96, 97),     # stays below
            (97, 98, 95, 96),     # stays below
        ]
        df = _make_df(rows)
        result = detect_false_breakout(
            df, level=100.0, direction='short',
            current_idx=4, atr_val=2.0, lookback=30
        )
        assert result == False
