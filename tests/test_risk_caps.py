"""
Round 5 A2 — per-symbol risk caps.

GBP/USD has 274 WF trades (<500-minimum). Council hard-capped sizing at 0.25%
until trade count crosses 500. This test locks the cap into the risk_config
factory so no caller can accidentally pass risk_per_trade=0.01 for GBPUSD.

See knowledge-base/67-Round-5-Post-Council-Validation.md (R5) and the
round5-remediation plan.
"""
import pytest

from src.core.risk_manager import (
    RiskConfig,
    risk_config_for_interval,
    SYMBOL_RISK_CAP,
)


@pytest.mark.parametrize("symbol", ["GBPUSD", "GBPUSD=X", "GBP_USD", "gbpusd"])
def test_gbpusd_sizing_capped_at_25bps(symbol):
    config = risk_config_for_interval(
        interval="1h",
        risk_per_trade=0.01,
        asset_class="forex",
        symbol=symbol,
    )
    assert config.risk_per_trade == pytest.approx(0.0025), (
        f"GBPUSD variant {symbol!r} must be hard-capped at 0.25% "
        f"until WF trade count >=500; got {config.risk_per_trade}"
    )


def test_gbpusd_cap_wins_even_if_caller_passes_higher_risk():
    """If the caller passes 5% risk, the cap still collapses to 0.25%."""
    config = risk_config_for_interval("1h", 0.05, "forex", symbol="GBPUSD=X")
    assert config.risk_per_trade == pytest.approx(0.0025)


def test_gbpusd_cap_does_not_lift_below_caller_floor():
    """If the caller voluntarily goes LOWER than the cap, keep the lower value."""
    config = risk_config_for_interval("1h", 0.001, "forex", symbol="GBPUSD=X")
    assert config.risk_per_trade == pytest.approx(0.001)


def test_non_capped_symbol_is_unchanged():
    """Gold / DAX / NASDAQ / EUR/USD must see no behaviour change."""
    for sym in ("GC=F", "^GDAXI", "^IXIC", "EURUSD=X", None):
        config = risk_config_for_interval("1h", 0.01, "gold", symbol=sym)
        assert config.risk_per_trade == pytest.approx(0.01), (
            f"Non-capped symbol {sym!r} had sizing mutated to {config.risk_per_trade}"
        )


def test_symbol_risk_cap_exposes_gbpusd_entry():
    """Module-level mapping must be discoverable for other call sites."""
    assert "GBPUSD" in SYMBOL_RISK_CAP
    assert SYMBOL_RISK_CAP["GBPUSD"] == pytest.approx(0.0025)


@pytest.mark.parametrize("symbol", ["USDJPY", "USDJPY=X", "USD_JPY", "usdjpy"])
def test_usdjpy_sizing_capped_at_25bps(symbol):
    """Round 7 council: USDJPY WF trade count 160 (<500 minimum) — same 0.25% cap as GBPUSD."""
    config = risk_config_for_interval(
        interval="1h",
        risk_per_trade=0.01,
        asset_class="forex",
        symbol=symbol,
    )
    assert config.risk_per_trade == pytest.approx(0.0025), (
        f"USDJPY variant {symbol!r} must be hard-capped at 0.25% "
        f"until WF trade count >=500; got {config.risk_per_trade}"
    )


def test_symbol_risk_cap_exposes_usdjpy_entry():
    assert "USDJPY" in SYMBOL_RISK_CAP
    assert SYMBOL_RISK_CAP["USDJPY"] == pytest.approx(0.0025)
