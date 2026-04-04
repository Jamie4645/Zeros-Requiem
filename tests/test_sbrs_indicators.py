"""
SBRS 1.0 — Indicator Unit Tests (pytest edition)

Tests WMA, SMMA, and swing detection logic used by the SBRS strategy.
Run: python -m pytest tests/test_sbrs_indicators.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.indicators.technical import (
    wma,
    smma,
    detect_swing_high,
    detect_swing_low,
    get_recent_swing_high,
    get_recent_swing_low,
)


# ====================================================================
# WMA Tests
# ====================================================================
class TestWMA:
    """Weighted Moving Average calculation tests."""

    @pytest.fixture()
    def prices(self):
        return pd.Series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0])

    def test_wma_seed_value(self, prices):
        """WMA(3) at index 2: (10*1 + 11*2 + 12*3) / 6 = 11.333"""
        w = wma(prices, period=3)
        assert abs(w.iloc[2] - 11.333) < 0.01, f"Expected ~11.333, got {w.iloc[2]:.3f}"

    def test_wma_rolling_value(self, prices):
        """WMA(3) at index 3: (11*1 + 12*2 + 13*3) / 6 = 12.333"""
        w = wma(prices, period=3)
        assert abs(w.iloc[3] - 12.333) < 0.01, f"Expected ~12.333, got {w.iloc[3]:.3f}"

    def test_wma_nan_padding(self, prices):
        """First (period - 1) values must be NaN."""
        w = wma(prices, period=3)
        assert np.isnan(w.iloc[0]), "Index 0 should be NaN"
        assert np.isnan(w.iloc[1]), "Index 1 should be NaN"

    def test_wma_period_9_first_valid(self, prices):
        """WMA(9) on 9 values: only the last value should be non-NaN."""
        w9 = wma(prices, period=9)
        assert not np.isnan(w9.iloc[8]), f"Index 8 should be valid, got {w9.iloc[8]}"

    def test_wma_period_9_nan_before(self, prices):
        """WMA(9) on 9 values: index 7 should still be NaN."""
        w9 = wma(prices, period=9)
        assert np.isnan(w9.iloc[7]), f"Index 7 should be NaN, got {w9.iloc[7]}"


# ====================================================================
# SMMA Tests
# ====================================================================
class TestSMMA:
    """Smoothed Moving Average calculation tests."""

    @pytest.fixture()
    def prices(self):
        return pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0])

    def test_smma_seed_equals_sma(self, prices):
        """SMMA(3) seed at index 2 should equal SMA(1,2,3) = 2.0."""
        s = smma(prices, period=3)
        assert abs(s.iloc[2] - 2.0) < 0.001, f"Expected 2.000, got {s.iloc[2]:.3f}"

    def test_smma_recursive_step_1(self, prices):
        """SMMA at index 3: (2.0 * 2 + 4.0) / 3 = 2.667."""
        s = smma(prices, period=3)
        assert abs(s.iloc[3] - 2.6667) < 0.01, f"Expected ~2.667, got {s.iloc[3]:.3f}"

    def test_smma_recursive_step_2(self, prices):
        """SMMA at index 4: (prev * 2 + 5.0) / 3."""
        s = smma(prices, period=3)
        expected = (2.6667 * 2 + 5.0) / 3
        assert abs(s.iloc[4] - expected) < 0.01, f"Expected {expected:.3f}, got {s.iloc[4]:.3f}"

    def test_smma_nan_padding(self, prices):
        """First (period - 1) values must be NaN."""
        s = smma(prices, period=3)
        assert np.isnan(s.iloc[0]), f"Index 0 should be NaN, got {s.iloc[0]}"
        assert np.isnan(s.iloc[1]), f"Index 1 should be NaN, got {s.iloc[1]}"

    def test_smma_values_within_data_range(self, prices):
        """SMMA values should stay within the data range [1, 7]."""
        s = smma(prices, period=3)
        for i in range(2, 7):
            assert 1.0 <= s.iloc[i] <= 7.0, f"Index {i} value {s.iloc[i]} out of range"


# ====================================================================
# Swing High Detection Tests
# ====================================================================
class TestSwingHigh:
    """Swing high detection using left/right bar comparisons."""

    def test_single_swing_high(self):
        """Clear swing high at index 5 (peak of 110)."""
        highs = pd.Series([100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100])
        sh = detect_swing_high(highs, left=3, right=3)
        assert sh.iloc[5] == True, f"Expected swing high at index 5, got {sh.iloc[5]}"

    def test_single_swing_high_count(self):
        """Only one swing high should be detected."""
        highs = pd.Series([100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100])
        sh = detect_swing_high(highs, left=3, right=3)
        assert sh.sum() == 1, f"Expected 1 swing high, got {sh.sum()}"

    def test_equal_highs_no_swing(self):
        """Equal highs should NOT form a swing (strictly less than required)."""
        highs_eq = pd.Series([100, 101, 102, 103, 103, 103, 102, 101, 100, 98, 97])
        sh_eq = detect_swing_high(highs_eq, left=3, right=3)
        assert sh_eq.sum() == 0, f"Expected 0 swing highs with equal values, got {sh_eq.sum()}"

    def test_multiple_swing_highs(self):
        """Two distinct peaks should produce two swing highs."""
        highs_multi = pd.Series(
            [90, 91, 92, 93, 100, 93, 92, 91, 92, 93, 105, 93, 92, 91, 90]
        )
        sh_multi = detect_swing_high(highs_multi, left=3, right=3)
        assert sh_multi.sum() == 2, f"Expected 2 swing highs, got {sh_multi.sum()}"

    def test_multiple_swing_high_positions(self):
        """Swing highs should be at indices 4 and 10."""
        highs_multi = pd.Series(
            [90, 91, 92, 93, 100, 93, 92, 91, 92, 93, 105, 93, 92, 91, 90]
        )
        sh_multi = detect_swing_high(highs_multi, left=3, right=3)
        assert sh_multi.iloc[4] == True, f"Expected swing high at index 4, got {sh_multi.iloc[4]}"
        assert sh_multi.iloc[10] == True, f"Expected swing high at index 10, got {sh_multi.iloc[10]}"


# ====================================================================
# Swing Low Detection Tests
# ====================================================================
class TestSwingLow:
    """Swing low detection using left/right bar comparisons."""

    def test_single_swing_low(self):
        """Clear swing low at index 5 (trough of 90)."""
        lows = pd.Series([100, 99, 98, 97, 96, 90, 96, 97, 98, 99, 100])
        sl = detect_swing_low(lows, left=3, right=3)
        assert sl.iloc[5] == True, f"Expected swing low at index 5, got {sl.iloc[5]}"

    def test_single_swing_low_count(self):
        """Only one swing low should be detected."""
        lows = pd.Series([100, 99, 98, 97, 96, 90, 96, 97, 98, 99, 100])
        sl = detect_swing_low(lows, left=3, right=3)
        assert sl.sum() == 1, f"Expected 1 swing low, got {sl.sum()}"

    def test_equal_lows_no_swing(self):
        """Equal lows should NOT form a swing."""
        lows_eq = pd.Series([100, 99, 98, 97, 97, 97, 98, 99, 100, 101, 102])
        sl_eq = detect_swing_low(lows_eq, left=3, right=3)
        assert sl_eq.sum() == 0, f"Expected 0 swing lows with equal values, got {sl_eq.sum()}"


# ====================================================================
# Swing Lookup (with 3-bar lag) Tests
# ====================================================================
class TestSwingLookup:
    """get_recent_swing_high/low with confirmation lag."""

    @pytest.fixture()
    def highs_and_mask(self):
        highs = pd.Series([100, 101, 102, 103, 104, 110, 104, 103, 102, 101, 100])
        sh = detect_swing_high(highs, left=3, right=3)
        return highs, sh

    @pytest.fixture()
    def lows_and_mask(self):
        lows = pd.Series([100, 99, 98, 97, 96, 90, 96, 97, 98, 99, 100])
        sl = detect_swing_low(lows, left=3, right=3)
        return lows, sl

    def test_swing_high_found_at_bar_8(self, highs_and_mask):
        """Swing at index 5 is detectable at bar 8 (search_end = 8-3 = 5)."""
        highs, sh = highs_and_mask
        result = get_recent_swing_high(highs, sh, current_idx=8, lookback=20)
        assert result == (5, 110.0), f"Expected (5, 110.0), got {result}"

    def test_swing_high_not_found_at_bar_7(self, highs_and_mask):
        """Swing at index 5 is NOT yet visible at bar 7 (3-bar lag)."""
        highs, sh = highs_and_mask
        result = get_recent_swing_high(highs, sh, current_idx=7, lookback=20)
        assert result is None, f"Expected None (3-bar lag), got {result}"

    def test_swing_high_not_found_short_lookback(self, highs_and_mask):
        """Short lookback (2 bars) should miss the swing at index 5."""
        highs, sh = highs_and_mask
        result = get_recent_swing_high(highs, sh, current_idx=10, lookback=2)
        assert result is None, f"Expected None (lookback=2), got {result}"

    def test_swing_low_found_at_bar_8(self, lows_and_mask):
        """Swing low at index 5 is detectable at bar 8."""
        lows, sl = lows_and_mask
        result = get_recent_swing_low(lows, sl, current_idx=8, lookback=20)
        assert result == (5, 90.0), f"Expected (5, 90.0), got {result}"

    def test_swing_low_not_found_at_bar_7(self, lows_and_mask):
        """Swing low at index 5 is NOT yet visible at bar 7 (3-bar lag)."""
        lows, sl = lows_and_mask
        result = get_recent_swing_low(lows, sl, current_idx=7, lookback=20)
        assert result is None, f"Expected None (3-bar lag), got {result}"


# ====================================================================
# WMA / SMMA Cross Logic Tests
# ====================================================================
class TestMACross:
    """WMA should react faster than SMMA to price changes."""

    def test_wma_crosses_above_smma_on_rising_data(self):
        """On rising prices, WMA(3) should eventually cross above SMMA(3)."""
        rising = pd.Series([10, 10, 10, 10, 10, 10, 12, 14, 16, 18, 20])
        w_cross = wma(rising, period=3)
        s_cross = smma(rising, period=3)

        cross_found = False
        for i in range(3, len(rising)):
            if np.isnan(w_cross.iloc[i]) or np.isnan(s_cross.iloc[i]):
                continue
            if np.isnan(w_cross.iloc[i - 1]) or np.isnan(s_cross.iloc[i - 1]):
                continue
            if w_cross.iloc[i] > s_cross.iloc[i] and w_cross.iloc[i - 1] <= s_cross.iloc[i - 1]:
                cross_found = True
                break

        assert cross_found, "WMA should cross above SMMA when prices start rising"
