"""
Audit 2026-06-01 — Entry-mode A/B: candle-close vs limit-at-retest (blocker #7).

Tests the methodology-faithful entry. Your doc: "limit orders exclusively, never
at market" — enter at the broken/retest level. The code entered at the retest-bar
CLOSE. This A/Bs both on realistic limit-fill machinery:
  - close : current behaviour (enter at retest-bar close)
  - limit : enter at broken_level via a resting limit (fills only on a real touch)

Both run with the reversal fill fix in place (engine.py), so neither benefits from
phantom fills. Risk passed WITHOUT symbol so SYMBOL_RISK_CAP does not bind.

Usage:  py -m tests._audit_entry_mode_ab --symbol GC=F --asset-class gold --period 10y
        py -m tests._audit_entry_mode_ab --all
Writes: logs/audit/entry_mode_ab.log
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

ALL = [('GC=F', 'gold'), ('^GDAXI', 'indices'), ('^IXIC', 'indices'),
       ('GBPUSD=X', 'forex'), ('USDJPY=X', 'forex')]


def run_mode(df, indicators, risk_cfg, capital, ac, mode):
    setups = analyze_sbrs_v2(df, capital, 0.01, asset_class=ac, entry_mode=mode)
    r = run_backtest(df, setups, capital, risk_cfg,
                     apply_slippage=True, sbrs_v2_indicators=indicators)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--symbol', default='GC=F')
    ap.add_argument('--asset-class', default='gold')
    ap.add_argument('--period', default='10y')
    ap.add_argument('--capital', type=float, default=10000.0)
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()

    lines = []
    p = lambda s: (lines.append(s), print(s))
    targets = ALL if args.all else [(args.symbol, args.asset_class)]

    p("\n" + "=" * 100)
    p("  ENTRY-MODE A/B — close vs limit-at-retest — 1H 10Y, realistic fills, raw 1% risk")
    p("=" * 100)
    p(f"  {'Symbol':<10} {'Mode':<7} | {'Trades':>6} | {'WR':>6} | {'PF':>6} | {'PnL':>12} | {'Sharpe':>7} | {'MaxDD':>7} | {'Exp':>7}")
    p("  " + "-" * 96)

    for symbol, ac in targets:
        try:
            df = fetch(symbol, '1h', args.period)
            indicators = get_sbrs_v2_indicators(df)
            risk_cfg = risk_config_for_interval('1h', 0.01)
        except Exception as e:
            p(f"  {symbol}: fetch failed: {e}")
            continue
        for mode in ('close', 'limit'):
            r = run_mode(df, indicators, risk_cfg, args.capital, ac, mode)
            pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
            p(f"  {symbol:<10} {mode:<7} | {r.total_trades:>6} | {r.win_rate:>5.1f}% | {pf:>6} | "
              f"${r.total_pnl:>11,.0f} | {r.sharpe_ratio:>7.2f} | {r.max_drawdown_pct:>6.1f}% | ${r.expectancy:>6,.0f}")
        p("  " + "-" * 96)

    p("=" * 100)
    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / 'entry_mode_ab.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")


if __name__ == '__main__':
    main()
