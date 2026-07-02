"""
SBRS 3.0 — first backtest of the clean-slate structural-exit strategy (Gold).

Compares against the bare-core PF 1.07 baseline (the floor to beat). All runs use
realistic fills, the doc MA convention (SMMA>WMA=bull), no reversal injection.

Variants:
  v3 TP=near   structural TP at the NEAREST prior level (user's preferred)
  v3 TP=far    structural TP at the MAJOR prior level
  v3 near, no 3R floor   take structural target regardless of R:R

Usage:  py -m tests._audit_sbrs_v3 --symbol GC=F --asset-class gold --period 10y
Writes: logs/audit/sbrs_v3.log
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

from src.data.fetcher import fetch
from src.regimes.sbrs_v2 import get_sbrs_v2_indicators
import src.regimes.sbrs_v2 as v2
import src.regimes.sbrs_v3 as v3
import src.core.engine as engine
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol', default='GC=F')
    ap.add_argument('--asset-class', default='gold')
    ap.add_argument('--period', default='10y')
    ap.add_argument('--capital', type=float, default=10000.0)
    args = ap.parse_args()

    lines = []
    p = lambda s: (lines.append(s), print(s))
    df = fetch(args.symbol, '1h', args.period)
    p(f"\n  {args.symbol} {args.asset_class} — {len(df)} candles ({df.index[0]} -> {df.index[-1]})")
    indicators = get_sbrs_v2_indicators(df)
    rc = risk_config_for_interval('1h', 0.01)

    p("\n" + "=" * 104)
    p("  SBRS 3.0 — structural-exit backtest (realistic fills, SMMA>WMA=bull, no reversal)")
    p("=" * 104)
    p(f"  {'Variant':<34} | {'Trades':>6} | {'WR':>6} | {'PF':>6} | {'PnL':>12} | {'Sharpe':>7} | {'MaxDD':>7} | {'AvgRR':>6}")
    p("  " + "-" * 100)

    def run(label, tp_mode, min_rr_floor):
        # Own ALL global flags spanning analyze + backtest, then restore.
        s_conv = v2.USE_OLD_MA_CONVENTION
        s_rev = engine.REVERSAL_ENTRY_ENABLED
        v2.USE_OLD_MA_CONVENTION = True          # doc convention SMMA>WMA=bull
        engine.REVERSAL_ENTRY_ENABLED = False    # no reversal in v3 baseline
        try:
            setups = v3.analyze_sbrs_v3(df, args.capital, 0.01, asset_class=args.asset_class,
                                        tp_mode=tp_mode, min_rr_floor=min_rr_floor)
            avg_rr = (sum(s.risk_reward for s in setups) / len(setups)) if setups else 0.0
            r = run_backtest(df, setups, args.capital, rc,
                             apply_slippage=True, sbrs_v2_indicators=indicators)
        finally:
            v2.USE_OLD_MA_CONVENTION = s_conv
            engine.REVERSAL_ENTRY_ENABLED = s_rev
        pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
        flag = "  <== ELITE" if (r.profit_factor >= 1.5 and r.sharpe_ratio >= 1.5 and r.total_pnl > 0) \
            else ("  <== +ve" if r.total_pnl > 0 and r.profit_factor >= 1.2 else "")
        p(f"  {label:<34} | {r.total_trades:>6} | {r.win_rate:>5.1f}% | {pf:>6} | "
          f"${r.total_pnl:>11,.0f} | {r.sharpe_ratio:>7.2f} | {r.max_drawdown_pct:>6.1f}% | {avg_rr:>6.2f}{flag}")

    run("v3 TP=near (3R floor)", 'near', 3.0)
    run("v3 TP=far (3R floor)", 'far', 3.0)
    run("v3 TP=near (no floor)", 'near', 0.0)
    run("v3 TP=far (no floor)", 'far', 0.0)
    p("=" * 104)
    p("  Baseline to beat (bare-core, fixed-3R): PF 1.07, +$1,431, Sharpe 0.16, DD 20.6%")

    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / 'sbrs_v3.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")


if __name__ == '__main__':
    main()
