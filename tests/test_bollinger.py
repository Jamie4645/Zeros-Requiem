"""
Tests for bollinger_bands in src/indicators/technical.py

Validates correctness: middle = SMA, symmetry, NaN handling.
"""

import pytest
import pandas as pd
import numpy as np

from src.indicators.technical import bollinger_bands


def _make_close_series(values):
    """Helper: create a Close price Series with DatetimeIndex."""
    return pd.Series(values, dtype=float,
                     index=pd.date_range('2025-01-01', periods=len(values), freq='1h'))


class TestBollingerBands:
    def test_middle_equals_sma(self):
        """Middle band should equal the simple moving average."""
        np.random.seed(0)
        prices = _make_close_series(np.random.normal(100, 5, 50))
        upper, middle, lower = bollinger_bands(prices, period=20, std_dev=2.0)

        expected_sma = prices.rolling(window=20).mean()
        pd.testing.assert_series_equal(middle, expected_sma, check_names=False)

    def test_symmetry(self):
        """Upper - middle should equal middle - lower (symmetric bands)."""
        np.random.seed(1)
        prices = _make_close_series(np.random.normal(100, 5, 50))
        upper, middle, lower = bollinger_bands(prices, period=20, std_dev=2.0)

        upper_dist = upper - middle
        lower_dist = middle - lower
        pd.testing.assert_series_equal(upper_dist, lower_dist, check_names=False)

    def test_first_period_minus_one_are_nan(self):
        """First period-1 values should be NaN."""
        prices = _make_close_series(range(1, 31))  # 30 values
        period = 20
        upper, middle, lower = bollinger_bands(prices, period=period)

        for band in [upper, middle, lower]:
            assert band.iloc[:period - 1].isna().all(), \
                f"Expected NaN for first {period - 1} values"
            assert not np.isnan(band.iloc[period - 1]), \
                f"Value at index {period - 1} should not be NaN"

    def test_band_width_scales_with_std_dev(self):
        """Doubling std_dev should double the band width."""
        np.random.seed(2)
        prices = _make_close_series(np.random.normal(100, 5, 50))

        upper1, middle1, lower1 = bollinger_bands(prices, period=20, std_dev=1.0)
        upper2, middle2, lower2 = bollinger_bands(prices, period=20, std_dev=2.0)

        width1 = (upper1 - lower1).dropna()
        width2 = (upper2 - lower2).dropna()

        ratio = width2 / width1
        np.testing.assert_allclose(ratio.values, 2.0, atol=1e-10)

    def test_constant_prices_zero_width(self):
        """Constant prices should produce zero-width bands (upper == lower == middle)."""
        prices = _make_close_series([100.0] * 30)
        upper, middle, lower = bollinger_bands(prices, period=20, std_dev=2.0)

        valid = middle.dropna()
        assert (valid == 100.0).all()
        # std of constant series is 0, so upper == lower == middle
        np.testing.assert_allclose(
            upper.dropna().values, lower.dropna().values, atol=1e-10
        )
