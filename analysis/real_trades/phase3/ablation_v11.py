"""Phase 3 v1.1 — selectivity ablation on the 3 break-quality SHIFT signals.

User request: ablate {momentum, FVG, liquidity sweep} as break-quality gates —
each alone, each pair, all three — and judge each by the SAME null-baseline test.
Base gates (G3 respect / G4 structure / G5 HTF / G6 volume) are always on.

For each variant report: fire-rate (setups/mo), 25-trade retention (recall),
and null-separation (real matched vs random-date matched, p-value). The honest
question: does requiring a genuine SHIFT make the user's real trades separate
from random — finally precision, not just recall?
"""
import sys
from itertools import combinations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, compute_indicators, shift_signals, ZTTParams  # noqa: E402

df = pd.read_csv(ROOT / 'data/cache/oanda_gold_10y_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
t = pd.read_csv(ROOT / 'analysis/real_trades/trades.csv')
t['dt'] = pd.to_datetime(t['entry_local'])
t['off'] = t['dt'].apply(lambda d: 1 if d >= pd.Timestamp('2026-03-29') else 0)
t['utc'] = t.apply(lambda r: (r['dt'] - pd.Timedelta(hours=r['off'])).tz_localize('UTC'), axis=1)
med_R = float((t['entry_price'] - t['sl']).abs().median())
TOL = 0.3 * med_R
first, last = t['utc'].min(), t['utc'].max()
months = (last - first).days / 30.4
span = df.loc[first - pd.Timedelta(days=45): last + pd.Timedelta(days=12)]
d = compute_indicators(span, ZTTParams())

# Base population: base gates ON, shift OFF (req_*=False)
base_p = ZTTParams(req_momentum=False, req_fvg=False, req_sweep=False)
base = [s for s in generate_setups(span, base_p, apply_gates=True) if first <= s.entry_time <= last]
# v1.0 raw (no gates at all) for reference
raw = [s for s in generate_setups(span, ZTTParams(), apply_gates=False) if first <= s.entry_time <= last]
# precompute shift signals per base setup
sig = {id(s): shift_signals(d, s, ZTTParams()) for s in base}
print(f"median R {med_R:.1f}; tol {TOL:.1f}; span {first.date()}..{last.date()} ({months:.1f}mo)")
print(f"raw v1.0 geometry: {len(raw)} ({len(raw)/months:.0f}/mo) | base-gated (no shift): {len(base)} ({len(base)/months:.0f}/mo)\n")

span_idx = df.loc[first:last].index
dirs = t['direction'].values
rng = np.random.default_rng(0)
NULL_DATES = [(rng.choice(len(span_idx), size=25, replace=False), rng.choice(dirs, size=25, replace=True))
              for _ in range(300)]


def matched_count(setups, date_dir_ref):
    by_dir = {'long': [], 'short': []}
    for s in setups:
        by_dir[s.direction].append(s)
    c = 0
    for target, direction, ref in date_dir_ref:
        lo, hi = target - pd.Timedelta(days=3), target + pd.Timedelta(days=3)
        cands = [s for s in by_dir[direction] if lo <= s.entry_time <= hi]
        if cands and min(abs(s.entry_price - ref) for s in cands) <= TOL:
            c += 1
    return c


def evaluate(setups, label):
    real_dd = [(r['utc'], r['direction'], r['entry_price']) for _, r in t.iterrows()]
    real = matched_count(setups, real_dd)
    nulls = []
    for didx, ddir in NULL_DATES:
        dd = [(span_idx[i], dd_, df.loc[span_idx[i], 'Close']) for i, dd_ in zip(didx, ddir)]
        nulls.append(matched_count(setups, dd))
    nulls = np.array(nulls)
    p = float((nulls >= real).mean())
    fr = len(setups) / months
    flag = 'SIGNAL' if p < 0.05 else ('weak' if p < 0.15 else '—')
    print(f"  {label:22s} n={len(setups):4d} ({fr:5.0f}/mo)  real {real:2d}/25  "
          f"null {nulls.mean():4.1f} (p95 {np.percentile(nulls,95):.0f})  p={p:.3f}  {flag}")


SIGNALS = ['momentum', 'fvg', 'sweep']
print("variant                  setups (rate)     recall   null         signal?")
evaluate(base, 'base only (no shift)')
for r in (1, 2, 3):
    for combo in combinations(SIGNALS, r):
        filt = [s for s in base if any(sig[id(s)][k] for k in combo)]
        evaluate(filt, '+'.join(combo))
