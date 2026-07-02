"""
Slip Reconciliation Report (Round 8 Falsifier #1).

Reads logs/paper/slip_reconciliation.jsonl and reports:
  - Per-symbol fill count, mean |slip|, p95 |slip|
  - Modeled slip from the canonical R7/R8 assumption
  - Ratio realized/modeled; flags FAIL if >1.33 across the rolling window
  - Last-N-days rolling stats (default 60d)

Usage:
    py scripts/slip_reconcile.py [--window-days 60]
"""

from __future__ import annotations

import json, argparse, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

LOG_PATH = Path(__file__).resolve().parent.parent / 'logs' / 'paper' / 'slip_reconciliation.jsonl'

# Modeled slip per asset class under the R7/R8 canonical assumption.
# Indices: 0.75 pt/side (B1 recal post-Round 7).
# FX:     0.0001 × multiplier → realistic mean slip ≈ 0.00005 price units for majors.
# Gold:   0.1 × price multiplier on the 0.10 branch → realistic ≈ 0.005 price units.
MODELED_SLIP = {
    'GOLD':   0.05,
    'DAX':    0.75,
    'NDX':    0.75,
    'GBPUSD': 0.00005,
    'USDJPY': 0.005,
}

FAIL_RATIO = 1.33  # Falsifier #1: realized mean |slip| > 1.33× modeled


def _normalize(symbol):
    s = (symbol or '').upper().strip()
    table = {
        'GC=F': 'GOLD', 'XAU_USD': 'GOLD', 'XAUUSD=X': 'GOLD',
        '^IXIC': 'NDX', 'NAS100_USD': 'NDX',
        '^GDAXI': 'DAX', 'DE30_EUR': 'DAX', 'DE40_EUR': 'DAX',
        'GBPUSD=X': 'GBPUSD', 'GBP_USD': 'GBPUSD',
        'USDJPY=X': 'USDJPY', 'USD_JPY': 'USDJPY',
    }
    return table.get(s, s.replace('=X', '').replace('_', ''))


def load(window_days):
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days) if window_days else None
    if not LOG_PATH.exists():
        return []
    rows = []
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get('slip_abs') is None:
                continue
            try:
                ts = datetime.fromisoformat(r['ts'].replace('Z', '+00:00'))
            except (KeyError, ValueError):
                continue
            if cutoff and ts < cutoff:
                continue
            rows.append(r)
    return rows


def summarise(rows):
    by_sym = defaultdict(list)
    for r in rows:
        key = _normalize(r.get('symbol'))
        by_sym[key].append(r['slip_abs'])
    out = []
    for k in sorted(by_sym.keys()):
        slips = sorted(by_sym[k])
        n = len(slips)
        mean = sum(slips) / n if n else 0.0
        p95 = slips[int(0.95 * (n - 1))] if n > 1 else (slips[0] if slips else 0.0)
        modeled = MODELED_SLIP.get(k, None)
        ratio = (mean / modeled) if (modeled and modeled > 0) else None
        verdict = '-'
        if ratio is not None:
            verdict = 'PASS' if ratio <= FAIL_RATIO else 'FAIL'
        out.append(dict(
            sym=k, n=n, mean=mean, p95=p95,
            modeled=modeled, ratio=ratio, verdict=verdict,
        ))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window-days', type=int, default=60)
    args = ap.parse_args()

    rows = load(args.window_days)
    summary = summarise(rows)

    print("=" * 84)
    print(f"  SLIP RECONCILIATION | last {args.window_days}d | rows={len(rows)}")
    print("=" * 84)
    print(f"  {'sym':<8} {'n':>5} {'mean':>12} {'p95':>12} {'modeled':>12} {'ratio':>8} {'verdict':<7}")
    print("-" * 84)
    fails = 0
    for s in summary:
        ratio = f"{s['ratio']:.2f}x" if s['ratio'] is not None else '-'
        modeled = f"{s['modeled']:.5f}" if s['modeled'] is not None else '-'
        if s['verdict'] == 'FAIL':
            fails += 1
        print(f"  {s['sym']:<8} {s['n']:>5} {s['mean']:>12.5f} {s['p95']:>12.5f} {modeled:>12} {ratio:>8} {s['verdict']:<7}")
    print("-" * 84)
    if not rows:
        print("  No fills recorded yet. Falsifier #1 inactive until paper-trade fills accumulate.")
    elif fails == 0:
        print(f"  RESULT: Falsifier #1 holds — all symbols <= {FAIL_RATIO}× modeled slip.")
    else:
        print(f"  RESULT: {fails} symbol(s) TRIPPED Falsifier #1 — re-convene council.")

    sys.exit(0 if fails == 0 else 2)


if __name__ == '__main__':
    main()
