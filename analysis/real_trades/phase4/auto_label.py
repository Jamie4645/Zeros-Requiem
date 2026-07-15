"""C1 — 10Y auto-label OUTCOME study (plan SEL-4/REG-4/V1, built ONCE).

Attacks the real binding constraint (60 labels, one regime) with thousands of
OBJECTIVE outcome labels: run the raw break-retest geometry over 10Y, simulate every
setup under the honest fill engine (ztt_sim), and label each good/bad by OUTCOME.
Then ask whether ANY feature separates good outcomes from bad — overall AND in every
regime fold.

EPISTEMICS (council-mandated, do not blur): auto-labels answer WALL 4 ("does the
feature predict a profitable OUTCOME?", large-N) — NOT WALL 1 ("does it predict the
USER's take?", 60 small-N labels). A feature that predicts outcome across regimes is
a real edge candidate; one that only fires in the down fold is regime-bound.

GUARD (sacred): if the good-rate comes back 95-100%, that is the SBRS fill-leak
signature — HALT, do not trust the labels.

Feature credit additionally requires beating the A3 trade-shuffle null
(permutation_null.py) and clearing the B2 regime-CV (_ztt_regime_cv.py); this script
produces the corpus + the AUC screen.

Usage:  py -m analysis.real_trades.phase4.auto_label [10y|1y]
Outputs: logs/ztt_autolabel/corpus_<period>.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from src.regimes.ztt_regime import compute_regime                   # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST              # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array        # noqa: E402

PERIOD = sys.argv[1] if len(sys.argv) > 1 else '10y'
GOOD_R = 1.5            # outcome label threshold (>=1.5R or a TP/cap win = "good")
AUC_BAR = 0.65         # per-fold discrimination bar (plan)
OUT = ROOT / 'logs' / 'ztt_autolabel'


def auc(x: np.ndarray, y: np.ndarray) -> float:
    """Rank-based AUC of feature x predicting binary label y (1=good). NaN-safe."""
    m = ~np.isnan(x)
    x, y = x[m], y[m]
    npos, nneg = int(y.sum()), int((1 - y).sum())
    if npos == 0 or nneg == 0:
        return float('nan')
    order = np.argsort(x, kind='mergesort')
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1)
    # average ranks for ties
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    csum = np.cumsum(counts)
    avg = {}
    start = 0
    for i, c in enumerate(counts):
        avg[i] = (start + 1 + start + c) / 2.0
        start += c
    ranks = np.array([avg[i] for i in inv])
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def main():
    df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv',
                     index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')

    p = ZTTV2Params()
    reg = compute_regime(df, p)
    setups = generate_setups_v2(df, p, apply_gates=False)   # raw geometry, large N
    trades, unables = simulate(setups, df, atr_array(df, p), reg, one_position=False)
    by_key = {(t['entry_index'], t['direction']): t for t in trades}

    rows = []
    for s in setups:
        t = by_key.get((s.entry_index, s.direction))
        if t is None:
            continue
        rtag = reg.iloc[s.entry_index]
        good = int(t['exit_reason'] in ('tp', 'cap') or t['r'] >= GOOD_R)
        rows.append(dict(
            entry_time=s.entry_time, direction=s.direction, mode=s.mode,
            session=COST.session_label(int(pd.Timestamp(s.entry_time).hour)),
            rr=s.rr, level_touches=s.level_touches,
            sl_pct=abs(s.entry_price - s.stop_loss) / s.entry_price * 100,
            tp_pct=abs(s.take_profit - s.entry_price) / s.entry_price * 100,
            er=rtag['er'], adx=rtag['adx'], vol_ratio=rtag['vol_ratio'],
            trend_dir=rtag['trend_dir'], vol_bucket=rtag['vol_bucket'],
            r=t['r'], exit_reason=t['exit_reason'], good=good,
        ))
    data = pd.DataFrame(rows).sort_values('entry_time').reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT / f'corpus_{PERIOD}.csv', index=False)

    n = len(data)
    gr = data['good'].mean()
    print(f"=== C1 auto-label outcome study — {PERIOD} M10 Gold (raw geometry, honest fills) ===")
    print(f"setups labelled: {n}  | unables: {unables}  | good-rate: {gr:.1%}  "
          f"| mean R: {data['r'].mean():.3f}  | net R: {data['r'].sum():.1f}")
    if gr >= 0.95:
        print("!!! HALT: good-rate >= 95% — SBRS fill-leak signature. Labels NOT trustworthy.")
        return
    print(f"corpus -> {OUT / f'corpus_{PERIOD}.csv'}")

    folds = ['up', 'down', 'range']
    numeric = ['er', 'adx', 'vol_ratio', 'rr', 'level_touches', 'sl_pct', 'tp_pct']
    print(f"\n-- numeric feature discrimination (AUC of 'good outcome'); bar = {AUC_BAR} in EVERY fold --")
    print(f"{'feature':14s} {'overall':>8s} " + ' '.join(f'{f:>8s}' for f in folds) + "   every-fold>=bar?")
    y_all = data['good'].values.astype(float)
    for feat in numeric:
        x_all = data[feat].values.astype(float)
        a_all = auc(x_all, y_all)
        per = {}
        for f in folds:
            sub = data[data['trend_dir'] == f]
            per[f] = auc(sub[feat].values.astype(float), sub['good'].values.astype(float)) \
                if len(sub) else float('nan')
        # AUC is symmetric around 0.5; treat max(a,1-a) as discrimination strength
        strong = all((not np.isnan(per[f])) and (max(per[f], 1 - per[f]) >= AUC_BAR) for f in folds)
        print(f"{feat:14s} {a_all:8.3f} " + ' '.join(f'{per[f]:8.3f}' for f in folds)
              + f"   {'YES' if strong else 'no'}")

    print("\n-- categorical good-rate (descriptive; NOT a fitted gate) --")
    for feat in ['trend_dir', 'vol_bucket', 'mode', 'session', 'direction']:
        cnts = data.groupby(feat)['good'].agg(['mean', 'count'])
        cells = ' | '.join(f"{k}:{r['mean']:.2f}(n{int(r['count'])})" for k, r in cnts.iterrows())
        print(f"  {feat:11s} {cells}")

    print("\nNOTE: AUC here = predicts OUTCOME (WALL 4), not the user's take (WALL 1). "
          "A feature is credited only if it ALSO clears the A3 null + B2 regime-CV.")


if __name__ == '__main__':
    main()
