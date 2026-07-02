"""
Audit 2026-06-01 — Selectivity + retest-fidelity sweep (blocker #7, options 1 & 2).

Question: with realistic fills (reversal bug fixed), can TIGHTENING what gets
traded turn the primary breakout-retest edge positive? Your methodology trades a
small, curated set and skips contested / false-breakout / low-quality setups.

Levers (monkeypatched module constants, read at runtime by analyze_sbrs_v2):
  Option 1 (selectivity): MIN_LEVEL_TOUCHES, CONFLUENCE_MIN_WITH_TREND,
                          CONFLUENCE_MIN_COUNTER_TREND, CONFLUENCE_MIN_AFTER_FALSE_BO
  Option 2 (retest fidelity): RETEST_TOLERANCE_ATR (+ short / indices variants)

All runs: entry_mode='close' (the better mode), realistic fills, raw 1% risk,
no symbol (cap off). SACRED-param test still guards the defaults; we only sweep
tunables here, restoring them after each run.

Usage:  py -m tests._audit_selectivity_sweep --symbol GC=F --asset-class gold --period 10y
        py -m tests._audit_selectivity_sweep --all
Writes: logs/audit/selectivity_sweep.log
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
import src.regimes.sbrs_v2 as v2
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval

ALL = [('GC=F', 'gold'), ('^GDAXI', 'indices'), ('^IXIC', 'indices'),
       ('GBPUSD=X', 'forex'), ('USDJPY=X', 'forex')]

# (label, {const: value})
CONFIGS = [
    ("Baseline (current gates)", {}),
    ("Level 3+ touches", {"MIN_LEVEL_TOUCHES": 3}),
    ("Confluence >=1.5", {"CONFLUENCE_MIN_WITH_TREND": 1.5, "CONFLUENCE_MIN_WITH_TREND_FOREX": 1.5}),
    ("Confluence >=2.0", {"CONFLUENCE_MIN_WITH_TREND": 2.0, "CONFLUENCE_MIN_WITH_TREND_FOREX": 2.0}),
    ("No counter-trend", {"CONFLUENCE_MIN_COUNTER_TREND": 99.0}),
    ("No false-BO levels", {"CONFLUENCE_MIN_AFTER_FALSE_BO": 99.0}),
    ("Tight retest 0.3 ATR", {"RETEST_TOLERANCE_ATR": 0.3, "RETEST_TOLERANCE_ATR_SHORT": 0.3,
                              "INDICES_RETEST_TOLERANCE_ATR_V2": 0.3}),
    ("Max selectivity combo", {"MIN_LEVEL_TOUCHES": 3, "CONFLUENCE_MIN_WITH_TREND": 2.0,
                               "CONFLUENCE_MIN_WITH_TREND_FOREX": 2.0,
                               "CONFLUENCE_MIN_COUNTER_TREND": 99.0,
                               "CONFLUENCE_MIN_AFTER_FALSE_BO": 99.0}),
    ("Ultra (combo + conf2.5 + tight retest)",
     {"MIN_LEVEL_TOUCHES": 3, "CONFLUENCE_MIN_WITH_TREND": 2.5,
      "CONFLUENCE_MIN_WITH_TREND_FOREX": 2.5, "CONFLUENCE_MIN_COUNTER_TREND": 99.0,
      "CONFLUENCE_MIN_AFTER_FALSE_BO": 99.0, "RETEST_TOLERANCE_ATR": 0.4,
      "RETEST_TOLERANCE_ATR_SHORT": 0.4, "INDICES_RETEST_TOLERANCE_ATR_V2": 0.4}),
]


def patch(overrides):
    saved = {}
    for k, v in overrides.items():
        if hasattr(v2, k):
            saved[k] = getattr(v2, k)
            setattr(v2, k, v)
    return saved


def restore(saved):
    for k, v in saved.items():
        setattr(v2, k, v)


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
    risk_cfg = risk_config_for_interval('1h', 0.01)

    for symbol, ac in targets:
        try:
            df = fetch(symbol, '1h', args.period)
            indicators = get_sbrs_v2_indicators(df)
        except Exception as e:
            p(f"  {symbol}: fetch failed: {e}")
            continue
        p("\n" + "=" * 104)
        p(f"  SELECTIVITY SWEEP — {symbol} ({ac}) — 1H {args.period}, realistic fills, close entry")
        p("=" * 104)
        p(f"  {'Config':<40} | {'Trades':>6} | {'WR':>6} | {'PF':>6} | {'PnL':>12} | {'Sharpe':>7} | {'MaxDD':>7}")
        p("  " + "-" * 100)
        for label, ov in CONFIGS:
            saved = patch(ov)
            try:
                setups = analyze_sbrs_v2(df, args.capital, 0.01, asset_class=ac, entry_mode='close')
                r = run_backtest(df, setups, args.capital, risk_cfg,
                                 apply_slippage=True, sbrs_v2_indicators=indicators)
            finally:
                restore(saved)
            pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
            flag = "  <== EDGE" if (r.profit_factor >= 1.5 and r.total_pnl > 0) else ""
            p(f"  {label:<40} | {r.total_trades:>6} | {r.win_rate:>5.1f}% | {pf:>6} | "
              f"${r.total_pnl:>11,.0f} | {r.sharpe_ratio:>7.2f} | {r.max_drawdown_pct:>6.1f}%{flag}")
        p("=" * 104)

    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / 'selectivity_sweep.log'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")


if __name__ == '__main__':
    main()
