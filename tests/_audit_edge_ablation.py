"""
Audit 2026-06-01 — Edge-divergence + adaptive-R:R ablation (blockers #2 & #6).

Measures, on Gold 1H, the P&L / PF / expectancy contribution of three features
the council flagged:

  #2  REVERSAL_ENTRY    failed-breakout-reversal injected entries (engine.py)
  #2  STRUCTURE_EXIT    structure-break-against-position exit       (engine.py)
       -> both present in the backtest but ABSENT from the live engine
  #6  SUB_3R_FILLS      Gold with-trend fills below 3.0R admitted by the
                        adaptive-R:R clamp (ATR_RR_CLAMP_LOW=0.7 -> ~2.1R floor)

Variants:
  Baseline                         full v2.0 backtested edge
  No reversal entries              REVERSAL_ENTRY_ENABLED=False
  No structure exit                STRUCTURE_EXIT_ENABLED=False
  LIVE-matching (both #2 off)      reversal + structure exit both disabled
  R:R 3.0 hard floor (#6)          ATR_RR_CLAMP_LOW=1.0  (rejects sub-3.0 fills)

All runs use symbol='' so the SYMBOL_RISK_CAP clamp does NOT bind — risk held
constant at 1% so PF/expectancy comparisons isolate the feature, not sizing.

Usage:
    py -m tests._audit_edge_ablation                # 10y Gold (default)
    py -m tests._audit_edge_ablation --period 5y
Writes: logs/audit/edge_ablation.log
"""

import sys
import argparse
import time
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

from src.data.fetcher import fetch
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
import src.regimes.sbrs_v2 as v2
import src.core.engine as engine
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


@dataclass
class Row:
    name: str
    trades: int
    win_rate: float
    pnl: float
    pf: float
    sharpe: float
    max_dd: float
    expectancy: float


def _run(df, indicators, risk_cfg, capital) -> Row:
    """Run one backtest at the CURRENT module-flag state and summarise."""
    setups = analyze_sbrs_v2(df, capital, 0.01, asset_class='gold')  # no symbol -> no cap
    res = run_backtest(
        df, setups, capital, risk_cfg,
        apply_slippage=True, sbrs_v2_indicators=indicators,
    )
    return Row(
        name='', trades=res.total_trades, win_rate=res.win_rate,
        pnl=res.total_pnl, pf=res.profit_factor, sharpe=res.sharpe_ratio,
        max_dd=res.max_drawdown_pct, expectancy=res.expectancy,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', default='10y')
    ap.add_argument('--symbol', default='GC=F')
    ap.add_argument('--capital', type=float, default=10000.0)
    args = ap.parse_args()

    risk_cfg = risk_config_for_interval('1h', 0.01)
    lines = []
    p = lambda s: (lines.append(s), print(s))

    p(f"\n  Fetching {args.symbol} 1H {args.period}...")
    t0 = time.time()
    df = fetch(args.symbol, '1h', args.period)
    p(f"  Loaded {len(df)} candles ({df.index[0]} -> {df.index[-1]}) in {time.time()-t0:.1f}s")
    indicators = get_sbrs_v2_indicators(df)

    rows = []

    def variant(label, *, reversal=True, structure=True, clamp_low=None):
        o_rev, o_str = engine.REVERSAL_ENTRY_ENABLED, engine.STRUCTURE_EXIT_ENABLED
        o_clamp = v2.ATR_RR_CLAMP_LOW
        engine.REVERSAL_ENTRY_ENABLED = reversal
        engine.STRUCTURE_EXIT_ENABLED = structure
        if clamp_low is not None:
            v2.ATR_RR_CLAMP_LOW = clamp_low
        try:
            r = _run(df, indicators, risk_cfg, args.capital)
            r.name = label
            rows.append(r)
            p(f"  [done] {label:<32} {r.trades:>4} tr | PF {r.pf:>5.2f} | ${r.pnl:>11,.0f} | exp ${r.expectancy:>7,.2f}")
        finally:
            engine.REVERSAL_ENTRY_ENABLED = o_rev
            engine.STRUCTURE_EXIT_ENABLED = o_str
            v2.ATR_RR_CLAMP_LOW = o_clamp

    p("\n  Running variants...\n")
    variant("Baseline (full v2.0)")
    variant("No reversal entries (#2)", reversal=False)
    variant("No structure exit (#2)", structure=False)
    variant("LIVE-matching (both #2 off)", reversal=False, structure=False)
    variant("R:R 3.0 hard floor (#6)", clamp_low=1.0)

    base = rows[0]
    p("\n" + "=" * 104)
    p("  AUDIT EDGE ABLATION — Gold 1H — feature contribution (positive vs-base = feature HELPS)")
    p("=" * 104)
    p(f"  {'Variant':<32} | {'Trades':>6} | {'WR':>6} | {'PF':>5} | {'PnL':>12} | {'Sharpe':>6} | {'MaxDD':>6} | {'Exp':>8} | {'vs base PnL':>12}")
    p("  " + "-" * 100)
    for r in rows:
        delta = "BASE" if r is base else f"{((r.pnl-base.pnl)/abs(base.pnl)*100):+.1f}%" if base.pnl else "n/a"
        pf = f"{r.pf:.2f}" if r.pf < 100 else "inf"
        p(f"  {r.name:<32} | {r.trades:>6} | {r.win_rate:>5.1f}% | {pf:>5} | ${r.pnl:>11,.0f} | {r.sharpe:>6.2f} | {r.max_dd:>5.1f}% | ${r.expectancy:>6,.0f} | {delta:>12}")
    p("=" * 104)

    p("\n  INTERPRETATION")
    for r in rows[1:]:
        d = r.pnl - base.pnl
        feat = "feature CONTRIBUTES (removing hurts)" if d < 0 else "feature is DEAD/NEGATIVE (removing helps)" if d > 0 else "neutral"
        p(f"   - {r.name:<32} dPnL ${d:>+11,.0f} | dPF {r.pf-base.pf:>+5.2f} | {feat}")

    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / 'edge_ablation.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")
    p(f"  Total {time.time()-t0:.0f}s")


if __name__ == '__main__':
    main()
