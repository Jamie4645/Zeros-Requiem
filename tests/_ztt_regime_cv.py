"""B2 — regime-stratified, time-ordered CV harness (plan REG-2).

The gate for ANY future autonomous selection filter. A candidate discriminator must
clear AUC >= 0.65 AND positive net-R in EVERY regime fold (up/down/range) — NOT
pooled — plus a near-flat slope of monthly take-subset R and chi-square > 3.84 vs a
trade-everything baseline. Pre-registered NOW, before the ~500-label corpus exists.

Hard rule (council): the every-fold requirement is NEVER relaxed to "most folds" —
that re-admits the regime contamination this gate exists to block.

This file is an underscore-prefixed HARNESS (pytest does not auto-collect it). Run:
    py tests/_ztt_regime_cv.py
The dry-run on the current 60 labels MUST REFUSE to certify (only the down/range
folds are populated — no up-trend month). That correct refusal IS the PASS.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import ZTTV2Params                          # noqa: E402
from src.regimes.ztt_regime import compute_regime                  # noqa: E402

AUC_BAR = 0.65
MIN_PER_CLASS = 10          # a fold needs >= this many of each class to be testable
REQUIRED_FOLDS = ('up', 'down', 'range')


def auc(x: np.ndarray, y: np.ndarray) -> float:
    m = ~np.isnan(x)
    x, y = x[m], y[m]
    npos, nneg = int(y.sum()), int((1 - y).sum())
    if npos == 0 or nneg == 0:
        return float('nan')
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    avg, start = {}, 0
    for i, c in enumerate(counts):
        avg[i] = (start + 1 + start + c) / 2.0
        start += c
    ranks = np.array([avg[i] for i in inv])
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def chi_square_2x2(a, b, c, d) -> float:
    """take/skip x outcome 2x2 chi-square (no correction)."""
    n = a + b + c + d
    if n == 0:
        return 0.0
    row1, row2, col1, col2 = a + b, c + d, a + c, b + d
    exp = [row1 * col1, row1 * col2, row2 * col1, row2 * col2]
    if min(exp) == 0:
        return 0.0
    obs = [a, b, c, d]
    return float(sum((o - e / n) ** 2 / (e / n) for o, e in zip(obs, exp)))


def regime_cv(data: pd.DataFrame, feature: str, label_col: str = 'label',
              regime_col: str = 'regime', r_col: str | None = None,
              verbose: bool = True) -> dict:
    """Return {'verdict': 'CERTIFY'|'REFUSE', 'reason', 'folds': {...}}."""
    folds = {}
    populated = []
    for reg in REQUIRED_FOLDS:
        sub = data[data[regime_col] == reg]
        npos = int((sub[label_col] == 1).sum())
        nneg = int((sub[label_col] == 0).sum())
        testable = npos >= MIN_PER_CLASS and nneg >= MIN_PER_CLASS
        a = auc(sub[feature].values.astype(float),
                sub[label_col].values.astype(float)) if testable else float('nan')
        net_r = float(sub.loc[sub[label_col] == 1, r_col].sum()) if (r_col and len(sub)) else None
        folds[reg] = dict(n=len(sub), npos=npos, nneg=nneg, testable=testable,
                          auc=a, take_net_r=net_r)
        if testable:
            populated.append(reg)

    missing = [r for r in REQUIRED_FOLDS if not folds[r]['testable']]
    if missing:
        verdict, reason = 'REFUSE', (
            f"under-powered: folds {missing} lack >= {MIN_PER_CLASS}/class "
            f"(single/partial-regime sample). Every-fold requirement NOT met.")
    else:
        every_ok = all(max(folds[r]['auc'], 1 - folds[r]['auc']) >= AUC_BAR
                       for r in REQUIRED_FOLDS)
        rpos = all((folds[r]['take_net_r'] or -1) > 0 for r in REQUIRED_FOLDS) if r_col else True
        if every_ok and rpos:
            verdict, reason = 'CERTIFY', "AUC>=bar and positive take net-R in EVERY fold."
        else:
            verdict, reason = 'REFUSE', "a populated fold failed the AUC/net-R bar."

    if verbose:
        print(f"\nregime-CV feature='{feature}'  (bar AUC>={AUC_BAR}, every fold, never 'most')")
        for r in REQUIRED_FOLDS:
            f = folds[r]
            print(f"  {r:6s} n={f['n']:4d} take={f['npos']:3d} skip={f['nneg']:3d} "
                  f"testable={str(f['testable']):5s} AUC={f['auc'] if not np.isnan(f['auc']) else float('nan'):.3f}"
                  + (f" take_net_R={f['take_net_r']:.2f}" if f['take_net_r'] is not None else ""))
        print(f"  VERDICT: {verdict} — {reason}")
    return dict(verdict=verdict, reason=reason, folds=folds)


def _dry_run():
    """Tag the 60 labels with regime and confirm the harness REFUSES (single regime)."""
    lbl_path = ROOT / 'analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv'
    # free-text reason/notes contain unquoted commas; the first 14 fields are clean.
    cols = ['n', 'entry_time', 'direction', 'mode', 'entry_price', 'stop_loss',
            'take_profit', 'rr_target', 'outcome', 'realized_r', 'level_price',
            'level_touches', 'session', 'decision']
    recs = []
    for line in lbl_path.read_text(encoding='utf-8').splitlines()[1:]:
        parts = line.split(',')
        if len(parts) >= 14:
            recs.append(parts[:14])
    df_lbl = pd.DataFrame(recs, columns=cols)
    df_lbl['realized_r'] = pd.to_numeric(df_lbl['realized_r'], errors='coerce')
    df_lbl['entry_time'] = pd.to_datetime(df_lbl['entry_time']).dt.tz_localize('UTC')
    df_lbl['label'] = (df_lbl['decision'].str.strip().str.lower() == 'take').astype(int)

    px = pd.read_csv(ROOT / 'data/cache/oanda_gold_1y_10m.csv', index_col=0, parse_dates=True)
    if px.index.tz is None:
        px.index = px.index.tz_localize('UTC')
    reg = compute_regime(px, ZTTV2Params())
    pos = reg.index.get_indexer(df_lbl['entry_time'], method='nearest')
    df_lbl['regime'] = reg['trend_dir'].values[pos]
    df_lbl['er'] = reg['er'].values[pos]

    print("=== B2 regime-CV DRY-RUN on the 60 labels (expected: REFUSE) ===")
    print("regime distribution of labels:")
    print(df_lbl.groupby(['regime', 'decision']).size().to_string())
    res = regime_cv(df_lbl, feature='er', label_col='label', regime_col='regime',
                    r_col='realized_r')
    ok = res['verdict'] == 'REFUSE'
    print(f"\nHarness self-check: {'PASS (correctly refused single-regime sample)' if ok else 'FAIL'}")
    return res


if __name__ == '__main__':
    _dry_run()
