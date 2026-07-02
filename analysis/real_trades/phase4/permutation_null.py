"""A3 — trade-shuffle permutation null (plan V2).

Does the strategy's TIMING/selection beat random placement, or is the P&L just
"being in Gold sometimes"? Hold the realized #entries, long/short ratio, R:R
structure, and the identical %-cap exit + cost model constant; randomize only WHEN
the trades are placed, then build the null distribution of net-R and report where the
actual net-R lands (empirical p-value).

Two nulls (Chan: naive IID shuffling is "unusually severe" because it breaks the
structural-exit cause/effect chain):
  * shift : circular shift of the actual entry SCHEDULE — preserves trade-adjacency
            and spacing (the adjacency-preserving block null). PRIMARY.
  * iid   : uniform-random entry bars — the severe null, reported for context.

Reuses the ONE honest engine (ztt_sim.simulate), so every null trade is filled and
costed identically to the real backtest. Pre-registered gate: actual net-R must
exceed the 95th percentile (p<0.05) of the SHIFT null to credit a timing edge.

Usage:  py -m analysis.real_trades.phase4.permutation_null [10y|1y] [n_shuffles]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import ZTTSetup                                # noqa: E402
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array        # noqa: E402

PERIOD = sys.argv[1] if len(sys.argv) > 1 else '10y'
B = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
SEED = 12345


def _mk_setup(df, atr_v, bar, direction, risk_dist, p):
    """Synthetic setup at `bar`: entry=close, SL=risk_dist away, TP=min(3R, MAX_MOVE%)."""
    entry = df['Close'].values[bar]
    sign = 1.0 if direction == 'long' else -1.0
    sl = entry - sign * risk_dist
    tp_3r = entry + sign * p.MIN_RR * risk_dist
    tp_pct = entry * (1.0 + sign * p.MAX_MOVE_PCT)
    tp = entry + sign * min(abs(tp_3r - entry), abs(tp_pct - entry))
    rr = abs(tp - entry) / risk_dist if risk_dist else 0.0
    return ZTTSetup(entry_index=bar, entry_time=df.index[bar], direction=direction,
                    mode='range', entry_price=entry, stop_loss=sl, take_profit=tp,
                    level_price=entry, level_touches=2, rr=rr, break_index=bar)


def _net_r(setups, df, atr_v):
    trades, _ = simulate(setups, df, atr_v, one_position=True)
    return sum(t['r'] for t in trades)


def main():
    df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv',
                     index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    p = ZTTV2Params()
    atr_v = atr_array(df, p)
    n = len(df)

    actual_setups = generate_setups_v2(df, p, apply_gates=True)
    actual_trades, _ = simulate(actual_setups, df, atr_v, one_position=True)
    actual_net_r = sum(t['r'] for t in actual_trades)
    bars = np.array([s.entry_index for s in actual_setups])
    dirs = [s.direction for s in actual_setups]
    risk_dists = np.array([abs(s.entry_price - s.stop_loss) for s in actual_setups])
    n_tr = len(actual_setups)
    long_ratio = np.mean([d == 'long' for d in dirs])

    valid = np.where(~np.isnan(atr_v) & (atr_v > 0))[0]
    valid = valid[(valid > 200) & (valid < n - 2)]
    rng = np.random.default_rng(SEED)

    print(f"=== A3 permutation null — {PERIOD} M10 Gold, {B} shuffles ===")
    print(f"actual: {n_tr} setups placed -> {len(actual_trades)} filled "
          f"(one-position), long_ratio {long_ratio:.2f}, net_R {actual_net_r:.1f}")

    for null in ('shift', 'iid'):
        dist = np.empty(B)
        for k in range(B):
            d_perm = list(rng.permutation(dirs))               # keep exact ratio, shuffle assignment
            rd_perm = rng.permutation(risk_dists)
            if null == 'shift':
                shift = int(rng.integers(1, n))
                nb = (bars + shift) % n
            else:
                nb = rng.choice(valid, size=n_tr, replace=False)
            ok = (nb > 200) & (nb < n - 2)
            sset = [_mk_setup(df, atr_v, int(b), d, float(r), p)
                    for b, d, r, o in zip(nb, d_perm, rd_perm, ok) if o]
            dist[k] = _net_r(sset, df, atr_v)
        pctl = float((dist < actual_net_r).mean() * 100)
        pval = float((dist >= actual_net_r).mean())
        print(f"\n  [{null}] null net_R: mean {dist.mean():.1f}  p5 {np.percentile(dist,5):.1f}  "
              f"p50 {np.percentile(dist,50):.1f}  p95 {np.percentile(dist,95):.1f}")
        print(f"  actual {actual_net_r:.1f} -> percentile {pctl:.1f}%  (p={pval:.3f})  "
              f"{'BEATS null (p<0.05)' if pval < 0.05 else 'does NOT beat random placement'}")

    print("\nGate: actual net_R must exceed the 95th pct of the SHIFT null (p<0.05) to credit "
          "timing edge. A pass is necessary-not-sufficient (Gold kurtosis favors momentum).")


if __name__ == '__main__':
    main()
