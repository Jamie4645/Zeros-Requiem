"""
Round 6 R6-1 — NASDAQ slippage isolation diagnostic.

Tests whether the PF 3.49 → 0.86 collapse between Round 5 canon (IBKR cache
+ old $0.15 index slip) and Round 6 fresh BT (OANDA + new 1.5pt bracket) is
driven by the slippage model flip or the data-source flip.

Strategy: hold the DATA constant (single OANDA fetch, reused) and run three
backtests with different slippage configurations:
  (a) Current B1 bracket live: 1.5 * 1.0 = 1.5pt slip (new canon)
  (b) Reduced to 1.5 * 0.1 = 0.15pt (old Gold-era bracket — isolates the B1 change)
  (c) Slippage OFF entirely (apply_slippage=False — upper-bound PF uplift)

If PF recovers to ~3 in (b) or (c), slippage dominates → NDX edge is real but
over-counted before B1. If PF stays ~0.86 across all three, DATA SOURCE
(IBKR-vs-OANDA) dominates → NDX canon was an IBKR artefact.

One-off diagnostic. Not part of the pytest suite.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from dataclasses import replace

from src.data.fetcher import fetch, detect_asset_class
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


SYMBOL = "^IXIC"
INTERVAL = "1h"
PERIOD = "10y"
CAPITAL = 10_000.0
RISK = 0.01


def run(tag: str, df, setups, risk_config, ind, apply_slippage: bool):
    print(f"\n[R6-1] {tag}")
    result = run_backtest(df, setups, CAPITAL, risk_config, apply_slippage=apply_slippage, sbrs_v2_indicators=ind)
    print(
        f"[R6-1] {tag}: trades={result.total_trades} "
        f"PF={result.profit_factor:.2f} Sharpe={result.sharpe_ratio:.2f} "
        f"PnL=${result.total_pnl:,.2f} DD={result.max_drawdown_pct:.2f}%"
    )
    return result


def main():
    print(f"[R6-1] Fetching {SYMBOL} {INTERVAL} {PERIOD} once (DATA held constant)...")
    df = fetch(SYMBOL, INTERVAL, PERIOD)
    print(f"[R6-1] {len(df)} bars {df.index[0]} -> {df.index[-1]}")

    asset_class = detect_asset_class(SYMBOL)

    setups = analyze_sbrs_v2(df, CAPITAL, RISK, asset_class=asset_class, symbol=SYMBOL)
    print(f"[R6-1] {len(setups)} setups (same for all variants)")

    risk_config_new = risk_config_for_interval(INTERVAL, RISK, asset_class, symbol=SYMBOL)
    ind = get_sbrs_v2_indicators(df)

    # (a) New B1 bracket: slippage_pips=1.5, hits >5000 branch → 1.5 * 1.0 = 1.5pt slip
    print(f"\n[R6-1] RiskConfig.slippage_pips (new): {risk_config_new.slippage_pips}")
    run("Variant A — NEW B1 bracket (1.5pt slip on indices)", df, setups, risk_config_new, ind, True)

    # (b) Old bracket equivalent: reduce slippage_pips so the new bracket
    #     still multiplies by 1.0 but the per-side cost matches the OLD 0.15pt
    #     (what DAX/NDX paid before B1). Set slippage_pips=0.15.
    risk_config_old = replace(risk_config_new, slippage_pips=0.15)
    print(f"\n[R6-1] RiskConfig.slippage_pips (old-equivalent): {risk_config_old.slippage_pips}")
    run("Variant B — OLD index slip (0.15pt/fill, pre-B1 cost)", df, setups, risk_config_old, ind, True)

    # (c) Slippage OFF — upper-bound PF
    run("Variant C — Slippage OFF (upper-bound)", df, setups, risk_config_new, ind, False)

    print("\n[R6-1] Interpretation:")
    print("  If B recovers to PF ~3: slippage bracket dominates.")
    print("  If C recovers to PF ~3: slippage is meaningful but setup count also matters.")
    print("  If all three are ~0.86: DATA SOURCE (IBKR-vs-OANDA) dominates.")


if __name__ == "__main__":
    main()
