"""
Per-symbol risk caps — ZTT Gold-only freeze (re-anchored 2026-06-09).

While the ZTT (Zero's True Trade) intraday-Gold strategy is built and validated,
ALL non-Gold instruments are PAUSED. SYMBOL_RISK_CAP is the authoritative ceiling:
    GOLD 1.00% | DAX 0.00% | NDX 0.00% | GBPUSD 0.00% | USDJPY 0.00%
    (Gold raised 0.50%→1.00% on 2026-06-09 — only live instrument; reverts when others return.)

(Prior Round-8 sizes were DAX 0.25% / NDX 0.15% / GBPUSD 0.20%; all zeroed by the
Gold-only freeze. Restore alongside src/live/runner.py SYMBOLS_CONFIG when ZTT ships.)

This suite locks BOTH enforcement points so no caller can size above the ceiling:
  1. risk_config_for_interval()  — the walk-forward / RiskConfig factory path
  2. capped_risk_pct()           — the chokepoint inside analyze_sbrs_v2 shared
                                   by backtest, walk-forward, AND the live engine

See knowledge-base/89-ZTT-Rebuild.md and the ACTIVE REBUILD banner in CLAUDE.md.
"""
import pytest

from src.core.risk_manager import (
    risk_config_for_interval,
    SYMBOL_RISK_CAP,
)
from src.regimes.sbrs_v2 import capped_risk_pct


# Canonical caps under the ZTT Gold-only freeze — keep in lockstep with
# src/core/risk_manager.py.
FROZEN_CAPS = {
    'GOLD': 0.0100,
    'DAX': 0.0000,
    'NDX': 0.0000,
    'GBPUSD': 0.0000,
    'USDJPY': 0.0000,
}


# ── SYMBOL_RISK_CAP dict integrity ────────────────────────────────────────
@pytest.mark.parametrize("key,expected", list(FROZEN_CAPS.items()))
def test_symbol_risk_cap_values_are_frozen(key, expected):
    assert key in SYMBOL_RISK_CAP, f"{key} missing from SYMBOL_RISK_CAP"
    assert SYMBOL_RISK_CAP[key] == pytest.approx(expected), (
        f"{key} cap drifted from frozen value {expected}; got {SYMBOL_RISK_CAP[key]}"
    )


def test_symbol_risk_cap_has_no_extra_symbols():
    """A stray entry here silently re-sizes live trades — pin the exact set."""
    assert set(SYMBOL_RISK_CAP) == set(FROZEN_CAPS)


# ── risk_config_for_interval enforcement ──────────────────────────────────
@pytest.mark.parametrize("symbol", ["GBPUSD", "GBPUSD=X", "GBP_USD", "gbpusd"])
def test_gbpusd_capped_at_zero(symbol):
    """ZTT freeze: GBPUSD paused — cap is 0.00%."""
    config = risk_config_for_interval("1h", 0.01, "forex", symbol=symbol)
    assert config.risk_per_trade == pytest.approx(0.0000), (
        f"GBPUSD variant {symbol!r} must cap at 0.00% (frozen); got {config.risk_per_trade}"
    )


@pytest.mark.parametrize("symbol", ["USDJPY", "USDJPY=X", "USD_JPY", "usdjpy"])
def test_usdjpy_capped_at_zero(symbol):
    """USDJPY paused — cap is 0.00%."""
    config = risk_config_for_interval("1h", 0.01, "forex", symbol=symbol)
    assert config.risk_per_trade == pytest.approx(0.0000), (
        f"USDJPY variant {symbol!r} must cap at 0.00%; got {config.risk_per_trade}"
    )


@pytest.mark.parametrize("symbol,cap", [
    ("GC=F", 0.0100), ("XAU_USD", 0.0100),
    ("^GDAXI", 0.0000), ("DE30_EUR", 0.0000),
    ("^IXIC", 0.0000), ("NAS100_USD", 0.0000),
])
def test_capped_symbols_bind_below_caller_request(symbol, cap):
    """Caller asks for 1% — every capped symbol must collapse to its frozen ceiling."""
    config = risk_config_for_interval("1h", 0.01, "indices", symbol=symbol)
    assert config.risk_per_trade == pytest.approx(cap), (
        f"{symbol!r} must cap at {cap}; got {config.risk_per_trade}"
    )


def test_cap_wins_even_if_caller_passes_higher_risk():
    """Paused GBPUSD collapses any caller request to 0.00%."""
    config = risk_config_for_interval("1h", 0.05, "forex", symbol="GBPUSD=X")
    assert config.risk_per_trade == pytest.approx(0.0000)


def test_cap_does_not_lift_below_caller_floor():
    """If the caller voluntarily goes LOWER than the cap, keep the lower value.

    Uses Gold (cap 0.50%) since the non-Gold caps are 0.00% under the freeze.
    """
    config = risk_config_for_interval("1h", 0.001, "gold", symbol="GC=F")
    assert config.risk_per_trade == pytest.approx(0.001)


def test_uncapped_symbol_is_unchanged():
    """Symbols with no cap entry must pass through untouched."""
    for sym in ("EURUSD=X", "AUDUSD=X", None):
        config = risk_config_for_interval("1h", 0.01, "forex", symbol=sym)
        assert config.risk_per_trade == pytest.approx(0.01), (
            f"Uncapped symbol {sym!r} had sizing mutated to {config.risk_per_trade}"
        )


# ── analyze_sbrs_v2 chokepoint (capped_risk_pct) ──────────────────────────
# This is the path the LIVE engine uses (engine_live + runner both call
# analyze_sbrs_v2 with symbol=). The cap binds here too.
@pytest.mark.parametrize("symbol,cap", [
    ("GC=F", 0.0100), ("XAU_USD", 0.0100),
    ("^GDAXI", 0.0000), ("DE30_EUR", 0.0000),
    ("^IXIC", 0.0000), ("NAS100_USD", 0.0000),
    ("GBPUSD=X", 0.0000), ("GBP_USD", 0.0000),
])
def test_capped_risk_pct_clamps_to_ceiling(symbol, cap):
    assert capped_risk_pct(0.01, symbol) == pytest.approx(cap)


@pytest.mark.parametrize("symbol", ["USDJPY=X", "USD_JPY", "usdjpy"])
def test_capped_risk_pct_zeroes_usdjpy(symbol):
    """USDJPY clamps to 0.0 → position_size collapses to 0 → no live setups."""
    assert capped_risk_pct(0.01, symbol) == pytest.approx(0.0)


def test_capped_risk_pct_passes_through_uncapped():
    for sym in ("EURUSD=X", "AUDUSD=X", "", None):
        assert capped_risk_pct(0.01, sym) == pytest.approx(0.01)


def test_capped_risk_pct_does_not_lift_below_cap():
    """Caller below the cap keeps its value (Gold; non-Gold caps are 0 under freeze)."""
    assert capped_risk_pct(0.0008, "GC=F") == pytest.approx(0.0008)
