"""Single disciplined OOS test of ONE combo (no search): the 1Y ablation's three
strongest levers stacked — MIN_TOUCHES=3 + significance gate (S1) + momentum (S2).

Pre-registered (before the run) kill criteria — the combo is a CANDIDATE only if ALL hold:
  (1) beats Gold buy-&-hold on information ratio over the 10Y window;
  (2) positive net-R in EVERY regime fold (up / down / range) — not pooled;
  (3) net-R exceeds the 95th pct of the adjacency-preserving permutation null (p<0.05).
Any miss => KILL (the 1Y gain was regime-luck / in-sample), no re-tune.

Runs on the ONE honest engine (ztt_sim). Usage: py -m analysis.real_trades.phase4.combo_oos
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import ZTTSetup                                # noqa: E402
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from src.regimes.ztt_regime import compute_regime                  # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ  # noqa: E402
from analysis.real_trades.metrics import summarize                 # noqa: E402

PERIOD = '10y'
B = 500
SEED = 4242
FOLDS = ('up', 'down', 'range')


def _mk_setup(df, bar, direction, risk_dist, p):
    entry = df['Close'].values[bar]
    sign = 1.0 if direction == 'long' else -1.0
    sl = entry - sign * risk_dist
    tp = entry + sign * min(p.MIN_RR * risk_dist, abs(entry * p.MAX_MOVE_PCT))
    rr = abs(tp - entry) / risk_dist if risk_dist else 0.0
    return ZTTSetup(entry_index=bar, entry_time=df.index[bar], direction=direction,
                    mode='range', entry_price=entry, stop_loss=sl, take_profit=tp,
                    level_price=entry, level_touches=2, rr=rr, break_index=bar)


def main():
    df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv',
                     index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    combo = ZTTV2Params(MIN_TOUCHES=3, enforce_significance=True, req_momentum=True)
    atr_v = atr_array(df, combo)
    reg = compute_regime(df, combo)
    n = len(df)

    setups = generate_setups_v2(df, combo, apply_gates=True)
    trades, unables = simulate(setups, df, atr_v, reg, one_position=True)
    m = summarize(trades, START_EQ, benchmark_close=df['Close'])

    print(f"=== COMBO OOS — {PERIOD} M10 Gold — MIN_TOUCHES=3 + significance(S1) + momentum(S2) ===")
    print(f"trades {m['n']} (unables {unables}) | IR {m['information_ratio']:.2f} "
          f"| buy&hold IR {m['buy_hold_info_ratio']:.2f} | beats_B&H {m['beats_buy_hold']}")
    print(f"net_R {m['net_r']:.1f} | mean_R {m['mean_r']:.3f} | PF {m['profit_factor']:.2f} "
          f"| WR {m['wr']:.1f}% | maxDD {m['max_dd_pct']:.1f}% | net_pnl ${m['net_pnl']:.0f}")

    # (2) per-regime fold net-R (every fold)
    print("\nper-regime fold (must be POSITIVE in every populated fold):")
    fold_ok = True
    for f in FOLDS:
        sub = [t for t in trades if t['regime'] == f]
        if not sub:
            print(f"  {f:6s} n=0  (empty)"); continue
        nr = sum(t['r'] for t in sub)
        wr = 100 * np.mean([t['pnl'] >= 0 for t in sub])
        print(f"  {f:6s} n={len(sub):4d}  net_R {nr:7.1f}  mean_R {nr/len(sub):+.3f}  WR {wr:.1f}%")
        if nr <= 0:
            fold_ok = False

    # (3) permutation null (adjacency-preserving shift)
    bars = np.array([s.entry_index for s in setups])
    dirs = [s.direction for s in setups]
    rds = np.array([abs(s.entry_price - s.stop_loss) for s in setups])
    actual_nr = m['net_r']
    rng = np.random.default_rng(SEED)
    dist = np.empty(B)
    for k in range(B):
        shift = int(rng.integers(1, n))
        nb = (bars + shift) % n
        dperm = list(rng.permutation(dirs))
        rperm = rng.permutation(rds)
        ok = (nb > 200) & (nb < n - 2)
        sset = [_mk_setup(df, int(b), d, float(r), combo)
                for b, d, r, o in zip(nb, dperm, rperm, ok) if o]
        nt, _ = simulate(sset, df, atr_v, one_position=True)
        dist[k] = sum(t['r'] for t in nt)
    pval = float((dist >= actual_nr).mean())
    pctl = float((dist < actual_nr).mean() * 100)
    print(f"\npermutation null ({B} shifts): null net_R mean {dist.mean():.1f} "
          f"p95 {np.percentile(dist,95):.1f} | actual {actual_nr:.1f} -> pctl {pctl:.1f}% (p={pval:.3f})")

    # verdict
    c1 = bool(m['beats_buy_hold'])
    c2 = fold_ok
    c3 = pval < 0.05
    print("\n--- PRE-REGISTERED VERDICT ---")
    print(f"  (1) beats buy&hold IR : {'PASS' if c1 else 'FAIL'}")
    print(f"  (2) positive every fold: {'PASS' if c2 else 'FAIL'}")
    print(f"  (3) beats null (p<.05) : {'PASS' if c3 else 'FAIL'}")
    print(f"  => {'CANDIDATE — survives OOS' if (c1 and c2 and c3) else 'KILL — regime-luck / in-sample (no re-tune)'}")


if __name__ == '__main__':
    main()
