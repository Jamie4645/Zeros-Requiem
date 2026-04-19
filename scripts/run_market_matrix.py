"""
Batch: 10Y backtest + Monte Carlo + walk-forward (SBRS 2.0) for all registry symbols.

Usage (from repo root):
  py scripts/run_market_matrix.py
  py scripts/run_market_matrix.py --symbols GC=F,^IXIC
  py scripts/run_market_matrix.py --skip-wf --mc-sims 2000

Outputs summary table to stdout; optional --json results_market_matrix.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List


def log(msg: str) -> None:
    print(msg, flush=True)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.fetcher import SYMBOLS, fetch, detect_asset_class, get_symbol_name
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval
from src.core.walk_forward import run_walk_forward
from src.core.monte_carlo import run_monte_carlo


def all_symbols() -> List[str]:
    out: List[str] = []
    for k in ("gold", "indices", "forex", "crypto"):
        out.extend(SYMBOLS[k])
    return out


def run_one_backtest(symbol: str, capital: float, risk: float, period: str):
    asset_class = detect_asset_class(symbol)
    df = fetch(symbol, "1h", period)
    setups = analyze_sbrs_v2(df, capital, risk, asset_class=asset_class, symbol=symbol)
    ind = get_sbrs_v2_indicators(df)
    rc = risk_config_for_interval("1h", risk, asset_class=asset_class)
    result = run_backtest(
        df, setups, capital, rc,
        apply_slippage=True,
        sbrs_v2_indicators=ind,
    )
    return df, result


def run_one_wf(symbol: str, capital: float, risk: float, n_windows: int):
    asset_class = detect_asset_class(symbol)
    df = fetch(symbol, "1h", "10y")
    analyze_fn = lambda d, eq, rp: analyze_sbrs_v2(
        d, eq, rp, asset_class=asset_class, symbol=symbol
    )
    return run_walk_forward(
        df=df,
        analyze_fn=analyze_fn,
        n_windows=n_windows,
        initial_capital=capital,
        risk_pct=risk,
        apply_slippage=True,
        min_bars=100,
        sbrs_indicator_fn=get_sbrs_v2_indicators,
        interval="1h",
        asset_class=asset_class,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--period", default="10y", help="Backtest period (default 10y)")
    p.add_argument("--windows", type=int, default=8)
    p.add_argument("--capital", type=float, default=10000.0)
    p.add_argument("--risk", type=float, default=0.01)
    p.add_argument("--mc-sims", type=int, default=5000)
    p.add_argument("--json-out", type=str, default="")
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Comma-separated tickers (default: all registry symbols)",
    )
    p.add_argument("--skip-wf", action="store_true", help="Skip walk-forward (faster)")
    p.add_argument("--skip-mc", action="store_true", help="Skip Monte Carlo")
    args = p.parse_args()

    rows: List[Dict[str, Any]] = []
    if args.symbols.strip():
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = all_symbols()

    t0 = time.perf_counter()
    log("=" * 88)
    log(
        f"  MARKET MATRIX — SBRS 2.0 | 1H | slippage ON | period={args.period} | "
        f"n={len(symbols)} | MC={'off' if args.skip_mc else args.mc_sims} | "
        f"WF={'off' if args.skip_wf else str(args.windows) + 'w'}"
    )
    log("=" * 88)

    for i, symbol in enumerate(symbols, start=1):
        name = get_symbol_name(symbol)
        rec: Dict[str, Any] = {
            "symbol": symbol,
            "name": name,
            "error": None,
            "backtest": None,
            "monte_carlo": None,
            "walk_forward": None,
        }
        sym_t0 = time.perf_counter()
        log(f"\n  [{i}/{len(symbols)}] {symbol} ({name}) -- starting")
        try:
            log(f"      > fetch + analyze_sbrs_v2 + backtest ({args.period})...")
            df, result = run_one_backtest(symbol, args.capital, args.risk, args.period)
            rs = result.risk_stats if result.risk_stats else {}
            rec["backtest"] = {
                "bars": len(df),
                "trades": result.total_trades,
                "win_rate": round(result.win_rate, 2),
                "total_pnl": round(result.total_pnl, 2),
                "profit_factor": round(result.profit_factor, 4) if result.profit_factor < 100 else 999,
                "sharpe": round(result.sharpe_ratio, 4),
                "max_dd_pct": round(result.max_drawdown_pct, 2),
                "blocked": rs.get("total_blocked", 0),
            }
            log(
                f"      OK backtest done: {result.total_trades} trades, "
                f"{time.perf_counter() - sym_t0:.1f}s elapsed this symbol"
            )

            if not args.skip_mc:
                if result.total_trades >= 3:
                    log(f"      > Monte Carlo ({args.mc_sims} sims)...")
                    mc = run_monte_carlo(
                        result.trades,
                        initial_capital=args.capital,
                        n_simulations=args.mc_sims,
                        seed=42,
                    )
                    rec["monte_carlo"] = {
                        "sims": args.mc_sims,
                        "prob_profitable_pct": round(mc.prob_profitable * 100, 2),
                        "prob_20dd_pct": round(mc.prob_20pct_drawdown * 100, 2),
                        "p95_max_dd_pct": round(mc.p95_max_drawdown_pct, 2),
                    }
                    log("      OK Monte Carlo done")
                else:
                    rec["monte_carlo"] = {"skipped": "fewer than 3 trades"}
                    log("      -- Monte Carlo skipped (<3 trades)")
            else:
                rec["monte_carlo"] = {"skipped": "--skip-mc"}

            if not args.skip_wf:
                log(f"      > walk-forward ({args.windows} windows, 10y fetch)...")
                wf = run_one_wf(symbol, args.capital, args.risk, args.windows)
                rec["walk_forward"] = {
                    "windows": wf.total_windows,
                    "profitable_windows": wf.profitable_windows,
                    "consistency_pct": round(wf.consistency_score * 100, 1),
                    "avg_pf": round(wf.avg_profit_factor, 3),
                    "avg_sharpe": round(wf.avg_sharpe, 3),
                    "total_pnl": round(wf.total_pnl, 2),
                }
                log("      OK walk-forward done")
            else:
                rec["walk_forward"] = {"skipped": "--skip-wf"}

        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["trace"] = traceback.format_exc()
            log(f"      ERROR: {rec['error']}")

        rows.append(rec)

        # Line summary
        bt = rec.get("backtest") or {}
        wf = rec.get("walk_forward") or {}
        mc = rec.get("monte_carlo") or {}
        if rec.get("error"):
            log(f"  {symbol:12s} FAIL {rec['error'][:80]}")
        else:
            pp = mc.get("prob_profitable_pct", "—")
            cc = wf.get("consistency_pct", "—")
            wf_w = wf.get("windows", "—")
            wf_p = wf.get("profitable_windows", "—")
            log(
                f"  {symbol:12s} | T={bt.get('trades')} PF={bt.get('profit_factor')} "
                f"Sharpe={bt.get('sharpe')} DD={bt.get('max_dd_pct')}% | "
                f"MC_prof={pp}% | WF={cc}% ({wf_p}/{wf_w}) | "
                f"symbol_time={time.perf_counter() - sym_t0:.1f}s"
            )

    log("=" * 88)
    log(f"  TOTAL wall time: {time.perf_counter() - t0:.1f}s ({len(symbols)} symbols)")
    log("=" * 88)

    if args.json_out:
        outp = ROOT / args.json_out
        outp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"  Wrote {outp}")

    return 0 if all(r.get("error") is None for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
