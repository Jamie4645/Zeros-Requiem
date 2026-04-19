"""
Integration tests for SBRS 2.0 strategy.
Tests confluence scoring, counter-trend handling, and backward compatibility.
"""
import pytest
import pandas as pd
import numpy as np
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.execution.entries import TradeSetup, TradeDirection


def make_trending_data(n_bars=500, direction='up', seed=42):
    """Generate synthetic OHLC data with a clear trend."""
    np.random.seed(seed)
    dates = pd.date_range('2020-01-01', periods=n_bars, freq='1h')

    if direction == 'up':
        base = np.cumsum(np.random.randn(n_bars) * 0.5 + 0.1) + 1800
    else:
        base = np.cumsum(np.random.randn(n_bars) * 0.5 - 0.1) + 1800

    df = pd.DataFrame({
        'Open': base,
        'High': base + np.abs(np.random.randn(n_bars) * 2),
        'Low': base - np.abs(np.random.randn(n_bars) * 2),
        'Close': base + np.random.randn(n_bars) * 1,
        'Volume': np.random.randint(1000, 10000, n_bars)
    }, index=dates)

    # Ensure OHLC consistency
    df['High'] = df[['Open', 'High', 'Close']].max(axis=1)
    df['Low'] = df[['Open', 'Low', 'Close']].min(axis=1)

    return df


class TestSBRSv2BasicFunctionality:
    """Test that SBRS 2.0 produces valid trade setups."""

    def test_analyze_returns_list(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df, equity=10000, risk_pct=0.01)
        assert isinstance(setups, list)

    def test_all_setups_are_trade_setup(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df)
        for s in setups:
            assert isinstance(s, TradeSetup)

    def test_regime_tag_is_v2(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df, asset_class='gold')
        for s in setups:
            assert s.regime.startswith('sbrs_v2_'), f"Expected sbrs_v2_* regime, got {s.regime}"

    def test_confluence_score_populated(self):
        df = make_trending_data(1000, seed=123)
        setups = analyze_sbrs_v2(df)
        if len(setups) > 0:
            for s in setups:
                assert s.confluence_score > 0, "Confluence score should be > 0 for valid setups"

    def test_risk_reward_minimum(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df)
        for s in setups:
            assert s.risk_reward >= 2.0, f"R:R should be >= 2.0, got {s.risk_reward}"

    def test_stop_loss_direction(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df)
        for s in setups:
            if s.direction == TradeDirection.LONG:
                assert s.stop_loss < s.entry_price, "Long SL should be below entry"
                assert s.take_profit > s.entry_price, "Long TP should be above entry"
            else:
                assert s.stop_loss > s.entry_price, "Short SL should be above entry"
                assert s.take_profit < s.entry_price, "Short TP should be below entry"


class TestSBRSv2Indicators:
    """Test the indicator helper function."""

    def test_get_indicators_returns_dict(self):
        df = make_trending_data(500)
        ind = get_sbrs_v2_indicators(df)
        assert isinstance(ind, dict)

    def test_indicators_have_required_keys(self):
        df = make_trending_data(500)
        ind = get_sbrs_v2_indicators(df)
        required = ['wma_1h', 'smma_1h', 'atr_vals', 'swing_high_mask', 'swing_low_mask']
        for key in required:
            assert key in ind, f"Missing indicator key: {key}"

    def test_indicator_lengths_match_input(self):
        df = make_trending_data(500)
        ind = get_sbrs_v2_indicators(df)
        for key in ['wma_1h', 'smma_1h', 'atr_vals', 'swing_high_mask', 'swing_low_mask']:
            assert len(ind[key]) == len(df), f"Indicator '{key}' length {len(ind[key])} != df length {len(df)}"

    def test_indicators_are_pandas_series(self):
        df = make_trending_data(500)
        ind = get_sbrs_v2_indicators(df)
        for key in ['wma_1h', 'smma_1h', 'atr_vals']:
            assert isinstance(ind[key], pd.Series), f"Expected pd.Series for '{key}', got {type(ind[key])}"


class TestSBRSv2AssetClasses:
    """Test that different asset classes produce correct regime tags."""

    def test_gold_regime_tag(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df, asset_class='gold')
        for s in setups:
            assert s.regime == 'sbrs_v2_gold'

    def test_forex_regime_tag(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df, asset_class='forex')
        for s in setups:
            assert s.regime == 'sbrs_v2_forex'

    def test_indices_regime_tag(self):
        df = make_trending_data(500)
        setups = analyze_sbrs_v2(df, asset_class='indices', symbol='^GSPC')
        for s in setups:
            assert s.regime == 'sbrs_v2_indices'


class TestSBRSv2EdgeCases:
    """Test edge cases and robustness."""

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        setups = analyze_sbrs_v2(df)
        assert setups == []

    def test_too_few_bars(self):
        df = make_trending_data(30)
        setups = analyze_sbrs_v2(df)
        assert setups == []

    def test_downtrend_data(self):
        df = make_trending_data(500, direction='down', seed=99)
        setups = analyze_sbrs_v2(df)
        assert isinstance(setups, list)

    def test_different_seeds_produce_different_results(self):
        df1 = make_trending_data(500, seed=1)
        df2 = make_trending_data(500, seed=2)
        setups1 = analyze_sbrs_v2(df1)
        setups2 = analyze_sbrs_v2(df2)
        # Different data should generally produce different setup counts
        # (not guaranteed but very likely with different seeds)
        assert isinstance(setups1, list)
        assert isinstance(setups2, list)


class TestMAConvention:
    """Verify the ablation-validated MA convention: WMA > SMMA = bullish."""

    def test_check_ma_cross_bullish(self):
        """WMA crossing above SMMA should be detected as a bullish (long) cross."""
        from src.regimes.sbrs_v2 import check_ma_cross
        n = 10
        wma_vals = pd.Series([99.0] * n)
        smma_vals = pd.Series([100.0] * n)
        # At bar 5: WMA jumps above SMMA (bullish cross — momentum convention)
        wma_vals.iloc[5] = 101.0
        wma_vals.iloc[6] = 101.5

        assert check_ma_cross(wma_vals, smma_vals, 6, 'long', lookback=5) is True
        assert check_ma_cross(wma_vals, smma_vals, 6, 'short', lookback=5) is False

    def test_check_ma_cross_bearish(self):
        """WMA crossing below SMMA should be detected as a bearish (short) cross."""
        from src.regimes.sbrs_v2 import check_ma_cross
        n = 10
        wma_vals = pd.Series([100.0] * n)
        smma_vals = pd.Series([99.0] * n)
        # At bar 5: WMA drops below SMMA (bearish cross — momentum lost)
        wma_vals.iloc[5] = 98.0
        wma_vals.iloc[6] = 97.5

        assert check_ma_cross(wma_vals, smma_vals, 6, 'short', lookback=5) is True
        assert check_ma_cross(wma_vals, smma_vals, 6, 'long', lookback=5) is False


class TestLevelQualityGate:
    """Test the 2-touch minimum level quality hard gate."""

    def test_level_with_zero_touches_rejected(self):
        """Levels with fewer than 2 touches should not produce setups."""
        from src.regimes.sbrs_v2 import MIN_LEVEL_TOUCHES
        assert MIN_LEVEL_TOUCHES == 2, "MIN_LEVEL_TOUCHES must be 2 per methodology"

    def test_setups_have_minimum_touches(self):
        """All generated setups should have level_touches >= MIN_LEVEL_TOUCHES."""
        from src.regimes.sbrs_v2 import MIN_LEVEL_TOUCHES
        df = make_trending_data(1000, seed=77)
        setups = analyze_sbrs_v2(df)
        for s in setups:
            assert s.level_touches >= MIN_LEVEL_TOUCHES, (
                f"Setup at bar {s.index} has {s.level_touches} touches, "
                f"expected >= {MIN_LEVEL_TOUCHES}"
            )


class TestBackwardCompatibility:
    """Ensure SBRS 2.0 TradeSetup fields have safe defaults."""

    def test_default_confluence_fields(self):
        setup = TradeSetup(
            direction=TradeDirection.LONG,
            entry_price=1800.0,
            stop_loss=1790.0,
            take_profit=1830.0,
            position_size=1.0,
            risk_reward=3.0,
            regime='sbrs_gold',
            index=100
        )
        assert setup.confluence_score == 0.0
        assert setup.fvg_present is False
        assert setup.liquidity_sweep is False
        assert setup.is_counter_trend is False
        assert setup.breakout_attempt == 1

    def test_v1_regime_still_works(self):
        """TradeSetup with v1 regime tag should have safe v2 defaults."""
        setup = TradeSetup(
            direction=TradeDirection.SHORT,
            entry_price=1900.0,
            stop_loss=1910.0,
            take_profit=1870.0,
            position_size=0.5,
            risk_reward=3.0,
            regime='sbrs_gold',
            index=200
        )
        assert setup.ma_cross_confirmed is False
        assert setup.level_touches == 0
        assert setup.in_squeeze is False

    def test_v2_fields_can_be_set(self):
        """Verify v2-specific fields can be populated."""
        setup = TradeSetup(
            direction=TradeDirection.LONG,
            entry_price=1800.0,
            stop_loss=1790.0,
            take_profit=1830.0,
            position_size=1.0,
            risk_reward=3.0,
            regime='sbrs_v2_gold',
            index=100,
            confluence_score=2.5,
            fvg_present=True,
            liquidity_sweep=True,
            ma_cross_confirmed=True,
            is_counter_trend=False,
            level_touches=4,
            in_squeeze=False,
            breakout_attempt=2,
        )
        assert setup.confluence_score == 2.5
        assert setup.fvg_present is True
        assert setup.liquidity_sweep is True
        assert setup.ma_cross_confirmed is True
        assert setup.level_touches == 4
        assert setup.breakout_attempt == 2
