"""Phase 3 HONEST RE-SCORE (council-mandated, no re-tune spent).

Answers the Red-Team / Socrates challenge: is "19/19 seen" real signal, or an
artifact of overfiring (~108 setups/mo)? We:
  1. Generate the ZTT setup population ONCE over the trade span.
  2. PRECISION / fire-rate: total setups vs the user's 25.
  3. Match REAL trades (entry within 0.3R, both ±3d as pre-registered AND ±10d) — recall.
  4. NULL BASELINE: K random (date, direction) draws, ref = close at that date,
     scored under the IDENTICAL rule. If real ≈ null, "seen" is meaningless.
Deterministic (seeded) random via numpy default_rng(0).
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, ZTTParams  # noqa: E402

df = pd.read_csv(ROOT / 'data/cache/oanda_gold_10y_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
t = pd.read_csv(ROOT / 'analysis/real_trades/trades.csv')
t['dt'] = pd.to_datetime(t['entry_local'])
t['off'] = t['dt'].apply(lambda d: 1 if d >= pd.Timestamp('2026-03-29') else 0)
t['utc'] = t.apply(lambda r: (r['dt'] - pd.Timedelta(hours=r['off'])).tz_localize('UTC'), axis=1)
med_R = float((t['entry_price'] - t['sl']).abs().median())
TOL = 0.3 * med_R     # fixed tolerance for apples-to-apples real-vs-null
print(f"median user R = {med_R:.1f}  ->  fixed match tol (0.3R) = {TOL:.1f}")

first, last = t['utc'].min(), t['utc'].max()
ARM = ZTTParams()      # Arm B
pop = generate_setups(df.loc[first - pd.Timedelta(days=45): last + pd.Timedelta(days=12)], ARM)
inspan = [s for s in pop if first <= s.entry_time <= last]
months = (last - first).days / 30.4
print(f"\nPRECISION / FIRE-RATE over trade span ({first.date()}..{last.date()}, {months:.1f} mo):")
print(f"  algo setups in span: {len(inspan)}  (~{len(inspan)/months:.0f}/mo)  vs user 25 (~{25/months:.1f}/mo)")
print(f"  precision proxy (user-taken / algo-fired) = 25/{len(inspan)} = {100*25/max(len(inspan),1):.1f}%")


def matched(target, direction, ref, window_days, tol):
    """Is there a same-dir setup within +-window of target AND within tol of ref price?"""
    lo, hi = target - pd.Timedelta(days=window_days), target + pd.Timedelta(days=window_days)
    cands = [s for s in pop if s.direction == direction and lo <= s.entry_time <= hi]
    if not cands:
        return False
    best = min(cands, key=lambda s: abs(s.entry_price - ref))
    return abs(best.entry_price - ref) <= tol


for win in (3, 10):
    real = sum(matched(r['utc'], r['direction'], r['entry_price'], win, TOL) for _, r in t.iterrows())
    print(f"\n=== window +-{win}d, tol {TOL:.1f} (fixed 0.3R) ===")
    print(f"  REAL trades matched: {real}/25 ({100*real/25:.0f}%)")
    # null baseline: K random dates, direction sampled to match real mix
    rng = np.random.default_rng(0)
    K = 300
    span_idx = df.loc[first:last].index
    dirs = t['direction'].values
    counts = []
    for _ in range(K):
        picks_dates = rng.choice(len(span_idx), size=25, replace=False)
        picks_dir = rng.choice(dirs, size=25, replace=True)
        c = 0
        for di, dd in zip(picks_dates, picks_dir):
            ts = span_idx[di]
            ref = df.loc[ts, 'Close']
            if matched(ts, dd, ref, win, TOL):
                c += 1
        counts.append(c)
    counts = np.array(counts)
    print(f"  NULL baseline (K={K} random-date sets): mean {counts.mean():.1f}/25, "
          f"95th pct {np.percentile(counts,95):.0f}, max {counts.max()}")
    z = (real - counts.mean()) / (counts.std() + 1e-9)
    p = float((counts >= real).mean())
    print(f"  real vs null: z={z:.1f}, empirical p(null>=real)={p:.3f}  "
          f"-> {'SIGNAL' if p < 0.05 else 'NOT distinguishable from overfiring'}")
