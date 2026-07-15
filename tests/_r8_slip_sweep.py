"""
Round 8 — Slip-sensitivity sweep on NDX + DAX.

Both councils (Philosophical + Arbiter) converged on this as the single
most load-bearing test. The 2026-04-18 recal halved slip from 1.5 -> 0.75
and resurrected NDX (PF 0.86 -> 2.63) and restored DAX (WF 75% -> 88%).

This sweep asks: is the PF curve a plateau or a cliff around 0.75?

Held constant: data, setups, indicators.
Varied: RiskConfig.slippage_pips in {0.50, 0.75, 1.00, 1.25}.

One-off diagnostic. Not part of pytest suite.
"""
import sys
from pathlib import Path
from dataclasses import replace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.data.fetcher import fetch, detect_asset_class
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


SLIP_LEVELS = [0.50, 0.75, 1.00, 1.25]
INSTRUMENTS = [("^IXIC", "NDX"), ("^GDAXI", "DAX")]
INTERVAL = "1h"
PERIOD = "10y"
CAPITAL = 10_000.0
RISK = 0.01


def run_one(symbol, name, slip_pips, df, setups, ind, base_risk_config):
    rc = replace(base_risk_config, slippage_pips=slip_pips)
    result = run_backtest(df, setups, CAPITAL, rc, apply_slippage=True, sbrs_v2_indicators=ind)
    return {
        "symbol": symbol,
        "name": name,
        "slip": slip_pips,
        "trades": result.total_trades,
        "pf": result.profit_factor,
        "sharpe": result.sharpe_ratio,
        "pnl": result.total_pnl,
        "dd_pct": result.max_drawdown_pct,
        "win_rate": result.win_rate,
    }


def verdict(rows_for_instrument):
    pfs = [r["pf"] for r in rows_for_instrument]
    pf_max = max(pfs)
    pf_min = min(pfs)
    pf_range_pct = ((pf_max - pf_min) / pf_max) * 100 if pf_max > 0 else float("inf")

    pf_by_slip = {r["slip"]: r["pf"] for r in rows_for_instrument}
    pf_075 = pf_by_slip.get(0.75, 0)
    pf_100 = pf_by_slip.get(1.00, 0)
    drop_075_to_100 = ((pf_075 - pf_100) / pf_075) * 100 if pf_075 > 0 else float("inf")

    if pf_range_pct < 30:
        shape = "PLATEAU"
    elif drop_075_to_100 > 50:
        shape = "CLIFF"
    else:
        shape = "SLOPE"

    return {
        "shape": shape,
        "pf_range_pct": pf_range_pct,
        "drop_075_to_100_pct": drop_075_to_100,
        "pf_at_075": pf_075,
        "pf_at_100": pf_100,
    }


def main():
    results = []

    for symbol, name in INSTRUMENTS:
        print(f"\n=== {name} ({symbol}) ===")
        print(f"Fetching {symbol} {INTERVAL} {PERIOD} once (held constant)...")
        df = fetch(symbol, INTERVAL, PERIOD)
        print(f"  {len(df)} bars {df.index[0]} -> {df.index[-1]}")

        asset_class = detect_asset_class(symbol)
        setups = analyze_sbrs_v2(df, CAPITAL, RISK, asset_class=asset_class, symbol=symbol)
        print(f"  {len(setups)} setups (held constant across slip levels)")

        base_rc = risk_config_for_interval(INTERVAL, RISK, asset_class, symbol=symbol)
        ind = get_sbrs_v2_indicators(df)

        rows = []
        for slip in SLIP_LEVELS:
            r = run_one(symbol, name, slip, df, setups, ind, base_rc)
            rows.append(r)
            print(f"  slip={slip:.2f}pt  trades={r['trades']:4d}  PF={r['pf']:.2f}  "
                  f"Sharpe={r['sharpe']:.2f}  PnL=${r['pnl']:>9,.0f}  DD={r['dd_pct']:.2f}%")

        results.extend(rows)

        v = verdict(rows)
        print(f"  VERDICT for {name}: {v['shape']} "
              f"(PF range {v['pf_range_pct']:.1f}%, drop 0.75->1.00: {v['drop_075_to_100_pct']:.1f}%)")

    print("\n=== SUMMARY ===")
    print(f"{'Inst':<6} {'Slip':>6} {'Trades':>7} {'PF':>6} {'Sharpe':>7} {'PnL':>11} {'DD%':>6}")
    for r in results:
        print(f"{r['name']:<6} {r['slip']:>6.2f} {r['trades']:>7d} {r['pf']:>6.2f} "
              f"{r['sharpe']:>7.2f} ${r['pnl']:>10,.0f} {r['dd_pct']:>5.2f}%")

    print("\n=== VERDICTS ===")
    for symbol, name in INSTRUMENTS:
        inst_rows = [r for r in results if r["name"] == name]
        v = verdict(inst_rows)
        print(f"{name}: {v['shape']}  (PF range {v['pf_range_pct']:.1f}%, "
              f"drop 0.75->1.00: {v['drop_075_to_100_pct']:.1f}%)")


if __name__ == "__main__":
    main()
