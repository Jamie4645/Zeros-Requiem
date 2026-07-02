"""
Audit 2026-06-01 — Realistic-fill re-validation (post engine fill fix).

After fixing the reversal fill bug (engine.py: reversals are now resting LIMIT
orders that fill only on a real touch of broken_level), re-run the full backtest
for all 5 instruments and report the headline metrics. These SUPERSEDE the canon
numbers, which were built on impossible phantom fills.

Risk passed WITHOUT symbol so SYMBOL_RISK_CAP does not zero USDJPY — raw 1% edge.

Usage:  py -m tests._audit_realistic_revalidation --period 10y
Writes: logs/audit/realistic_revalidation.log
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
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval

INSTRUMENTS = [
    ('GC=F', 'gold'),
    ('^GDAXI', 'indices'),
    ('^IXIC', 'indices'),
    ('GBPUSD=X', 'forex'),
    ('USDJPY=X', 'forex'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', default='10y')
    ap.add_argument('--capital', type=float, default=10000.0)
    args = ap.parse_args()

    lines = []
    p = lambda s: (lines.append(s), print(s))

    p("\n" + "=" * 104)
    p("  REALISTIC-FILL RE-VALIDATION (post fill fix) — 1H, 10Y, raw 1% risk, slippage ON")
    p("  These numbers SUPERSEDE canon (which used impossible phantom fills).")
    p("=" * 104)
    p(f"  {'Symbol':<10} | {'Trades':>6} | {'WR':>6} | {'PF':>6} | {'PnL':>12} | {'Sharpe':>7} | {'MaxDD':>7} | {'Exp/tr':>8}")
    p("  " + "-" * 100)

    rows = []
    for symbol, ac in INSTRUMENTS:
        try:
            df = fetch(symbol, '1h', args.period)
            risk_cfg = risk_config_for_interval('1h', 0.01)
            setups = analyze_sbrs_v2(df, args.capital, 0.01, asset_class=ac)
            indicators = get_sbrs_v2_indicators(df)
            r = run_backtest(df, setups, args.capital, risk_cfg,
                             apply_slippage=True, sbrs_v2_indicators=indicators)
        except Exception as e:
            p(f"  {symbol:<10} | FAILED: {e}")
            continue
        pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
        p(f"  {symbol:<10} | {r.total_trades:>6} | {r.win_rate:>5.1f}% | {pf:>6} | "
          f"${r.total_pnl:>11,.0f} | {r.sharpe_ratio:>7.2f} | {r.max_drawdown_pct:>6.1f}% | ${r.expectancy:>7,.0f}")
        rows.append((symbol, r))

    p("=" * 104)
    p("\n  BENCHMARK GATES (elite): PF>=1.5, Sharpe>=1.5, MaxDD<=15%, expectancy>0")
    for symbol, r in rows:
        passes = r.profit_factor >= 1.5 and r.sharpe_ratio >= 1.5 and r.total_pnl > 0
        p(f"   - {symbol:<10} {'PASS' if passes else 'FAIL'}  (PF {r.profit_factor:.2f}, Sharpe {r.sharpe_ratio:.2f}, PnL ${r.total_pnl:,.0f})")

    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / 'realistic_revalidation.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")


if __name__ == '__main__':
    main()
