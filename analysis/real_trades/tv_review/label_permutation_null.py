"""Label-selection permutation null on the 60 user take/skip labels.

2026-07-02 books-review action #2 (Chan test #3 / Woodriff random-target /
Taleb Monte Carlo — independently prescribed by three books): the +10.29R
take-subset result has never faced a null. This script answers: *is the
user's 30-of-60 selection statistically distinguishable from luck on this
sample?*

Three views:
  1. OVERALL null — shuffle which 30 of the 60 setups are "takes" (10,000x),
     locate the actual take-subset net-R in the null distribution.
  2. DIRECTION-STRATIFIED null — shuffle labels WITHIN longs and WITHIN
     shorts separately, preserving the take-count of each direction. This
     removes the "short-biased takes in a down-month" regime effect and
     isolates within-direction selection skill.
  3. Benchmarks — take-everything net-R, and the take/skip direction mix.

NOTE (pre-registered honesty): the labels are retrospective, single-regime
(one bearish month), and hindsight risk is undocumented. A significant p
here upgrades the discretionary-edge premise from "narrative" to "worth a
forward test (F8)" — it does NOT validate it.

Usage: py -m analysis.real_trades.tv_review.label_permutation_null [n_shuffles]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / 'analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv'
LOG = ROOT / 'logs/audit/label_permutation.log'

B = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
SEED = 20260702


def main() -> None:
    df = pd.read_csv(CSV)
    df['decision'] = df['decision'].str.strip().str.lower()
    assert set(df['decision']) <= {'take', 'skip'}, sorted(set(df['decision']))

    r = df['realized_r'].to_numpy(float)
    take_mask = (df['decision'] == 'take').to_numpy()
    n, k = len(df), int(take_mask.sum())

    actual_take_r = r[take_mask].sum()
    actual_skip_r = r[~take_mask].sum()
    take_all_r = r.sum()

    rng = np.random.default_rng(SEED)
    lines = []

    def emit(s: str) -> None:
        print(s)
        lines.append(s)

    emit(f"=== Label-selection permutation null — {n} labels, {k} takes, B={B} ===")
    emit(f"actual take-subset net-R : {actual_take_r:+.2f}")
    emit(f"actual skip-subset net-R : {actual_skip_r:+.2f}")
    emit(f"take-everything net-R    : {take_all_r:+.2f}")
    emit(f"skip zero-win check      : skip wins = {int((r[~take_mask] > 0).sum())} / {n - k}")

    # ── 1. Overall null: any k-of-n selection ─────────────────────────────
    null = np.empty(B)
    for b in range(B):
        idx = rng.choice(n, size=k, replace=False)
        null[b] = r[idx].sum()
    p_overall = float((null >= actual_take_r).mean())
    emit("")
    emit("[1] OVERALL null (any 30-of-60):")
    emit(f"    null mean {null.mean():+.2f} | p5 {np.percentile(null, 5):+.2f} "
         f"| p95 {np.percentile(null, 95):+.2f} | p99 {np.percentile(null, 99):+.2f}")
    emit(f"    P(null >= actual) = {p_overall:.4f}"
         f"  -> {'SIGNIFICANT at 5%' if p_overall < 0.05 else 'NOT significant at 5%'}")

    # ── 2. Direction-stratified null ──────────────────────────────────────
    dirs = df['direction'].str.lower().to_numpy()
    strat_null = np.zeros(B)
    for d in ('long', 'short'):
        dm = dirs == d
        rd = r[dm]
        kd = int((take_mask & dm).sum())
        nd = int(dm.sum())
        emit("")
        emit(f"    [{d}] {nd} setups, {kd} taken, take-R "
             f"{r[take_mask & dm].sum():+.2f}, all-R {rd.sum():+.2f}")
        if kd == 0 or nd == 0:
            continue
        for b in range(B):
            idx = rng.choice(nd, size=kd, replace=False)
            strat_null[b] += rd[idx].sum()
    p_strat = float((strat_null >= actual_take_r).mean())
    emit("")
    emit("[2] DIRECTION-STRATIFIED null (shuffle within longs / within shorts,")
    emit("    take-counts per direction preserved — removes down-month short bias):")
    emit(f"    null mean {strat_null.mean():+.2f} | p5 {np.percentile(strat_null, 5):+.2f} "
         f"| p95 {np.percentile(strat_null, 95):+.2f} | p99 {np.percentile(strat_null, 99):+.2f}")
    emit(f"    P(null >= actual) = {p_strat:.4f}"
         f"  -> {'SIGNIFICANT at 5%' if p_strat < 0.05 else 'NOT significant at 5%'}")

    # ── 3. Verdict ────────────────────────────────────────────────────────
    emit("")
    emit("[3] VERDICT:")
    if p_overall < 0.05 and p_strat < 0.05:
        emit("    Selection beats luck overall AND within direction on this sample.")
        emit("    Upgrade to: 'worth the pre-registered forward test (F8)'. Not proof.")
    elif p_overall < 0.05:
        emit("    Selection beats a random 30-of-60 — but NOT once direction mix is")
        emit("    held fixed. The separation is substantially directional/regime;")
        emit("    within-direction skill is unproven on this sample.")
    else:
        emit("    Selection is NOT distinguishable from luck on this sample.")
        emit("    The +10.29R take-subset result cannot support the 'user IS the")
        emit("    selection layer' premise; F8 forward evidence is mandatory.")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text('\n'.join(lines), encoding='utf-8')
    print(f"\nwritten -> {LOG}")


if __name__ == '__main__':
    main()
