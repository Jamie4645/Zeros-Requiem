---
tags: [ablation, sbrs-v2, validation, round-2]
aliases: [Ablation Round 2, Ablation 2026-04-16, Feature Verdict Round 2]
related: [[00-MOC-Zeros-Requiem]], [[48-Ablation-Study-Results]], [[63-FVG-Downshift-Change]], [[64-Risk-Manager-Gold-Cap-Fix]], [[51-Confluence-Scoring-System]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the ablation PF/Sharpe/PnL table below is a void artifact, not
> current state. Retained as historical record only. Current canon: root `CLAUDE.md` +
> [[00-MOC-Zeros-Requiem]].

# Ablation Round 2 — SBRS 2.0 Feature Verdict (2026-04-16)

> *"Measure, don't predict. If the ablation says FVG hurts, the ablation says FVG hurts."*

Full 17-config ablation study on 10Y Gold, OANDA data, SBRS 2.0. Baseline produced 413 trades, PF 1.31, Sharpe 0.64, DD 10.1%. This round challenges several findings from [[48-Ablation-Study-Results]] — specifically the "FVG is critical" claim.

## Test Results Table

| # | Variant | Trades | WR | PF | PnL | Sharpe | DD | Δ vs Base |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | Baseline (full v2.0) | 413 | 39.5% | 1.31 | $8,177 | 0.64 | 10.1% | BASE |
| 1 | **No FVG** | 327 | 43.7% | **2.11** | **$20,811** | **1.15** | **7.5%** | **+154.5%** |
| 2 | No Liquidity Sweep | 373 | 40.0% | 1.24 | $5,614 | 0.49 | 10.1% | -31.3% |
| 3 | No FVG + No Liquidity | 37 | 29.7% | 0.99 | -$18 | 0.01 | 10.7% | -100.2% |
| 4 | No MA Cross Score | 201 | 40.8% | 1.33 | $4,114 | 0.46 | 10.0% | -49.7% |
| 5 | MA Cross ONLY | 0 | 0.0% | — | $0 | 0.00 | 0.0% | -100.0% |
| 6 | No Level Gate (0 touches) | 432 | 39.1% | 1.25 | $6,788 | 0.54 | 10.5% | -17.0% |
| 7 | No Counter-Trend | 252 | 42.5% | 1.43 | $6,682 | 0.65 | 10.2% | -18.3% |
| 8 | **No Session Filter** | 201 | 42.3% | 1.33 | $3,935 | 0.45 | 10.6% | **-51.9%** |
| 9 | No Squeeze Filter | 413 | 39.5% | 1.31 | $8,177 | 0.64 | 10.1% | +0.0% |
| 10 | No Whipsaw Detection | 413 | 39.5% | 1.31 | $8,177 | 0.64 | 10.1% | +0.0% |
| 11 | Old MA Convention | 413 | 39.5% | 1.31 | $8,177 | 0.64 | 10.1% | +0.0%* |
| 12 | Higher Threshold (1.5) | 271 | 41.3% | 1.22 | $3,552 | 0.38 | 10.4% | -56.6% |
| 13 | Kitchen Sink OFF | 0 | 0.0% | — | $0 | 0.00 | 0.0% | -100.0% |
| 14 | Tight Retest (0.3 ATR all) | 356 | 39.3% | 1.26 | $5,935 | 0.52 | 10.2% | -27.4% |
| 15 | Wide Retest (0.8 ATR all) | 221 | 39.8% | 1.26 | $3,657 | 0.40 | 10.7% | -55.3% |
| 16 | No False BO Filter | 456 | 39.7% | 1.25 | $7,160 | 0.54 | 10.1% | -12.4% |
| 17 | No Chop Filter | 413 | 39.5% | 1.31 | $8,177 | 0.64 | 10.1% | +0.0% |

*Test #11 was buggy in Round 1 (patch didn't actually invert the MA comparison). Fixed in this codebase; will re-test.*

## Verdict by Component

### KEEP AS-IS (8 features)
- **Session filter** — single most valuable component (-52% if removed)
- **MA cross score** (+0.5 weight) — removing it loses 50% of PnL
- **Liquidity Sweep** (+1.0 weight) — -31% if removed
- **Level 2-touch gate** — -17% if removed
- **False BO filter** — -12% if removed
- **Retest tolerance 0.5 ATR** — both tighter and wider hurt
- **Confluence threshold 1.0** — raising to 1.5 destroys performance
- **Counter-trend @ threshold 2.0** — adds +$1,495 net

### CHANGED — FVG DOWNWEIGHT +1.0 → +0.5

See [[63-FVG-Downshift-Change]] for full rationale and pre/post comparison.

Key finding: **"No FVG" variant produced $20,811 vs baseline $8,177 — a 154% improvement at lower drawdown.** The 327 surviving trades had WR 43.7% vs baseline 39.5%. At weight +1.0, FVG single-handedly qualified marginal setups over the 1.0 threshold; at +0.5 it now requires pairing with another booster.

This directly contradicts the published [[48-Ablation-Study-Results]] claim that "FVG disabled = -$1,519." The previous finding appears to have been on earlier data or earlier risk-manager behaviour; current reality is the opposite.

### DELETED — Dead Code Confirmed (3 features)
- **Squeeze filter** — 0.0% impact across all tests. Code path retained as `False` stub for dataclass compatibility; `detect_bollinger_squeeze` import removed from `sbrs_v2.py`.
- **Chop filter** — 0.0% impact. `is_choppy()` function deleted from `sbrs_v2.py`.
- **Whipsaw detection** — already removed in earlier refactor; ablation variant made no-op.

## Why Round 2 Disagreed with Round 1

Three factors probably account for the reversal:

1. **Risk manager direction-counting bug fix** ([[61-Audit-Remediation-2026-04]]). Layer 4 (direction concentration) now fires correctly. Previous baseline was inflated by Layer 4 never blocking same-direction entries.
2. **Data source drift.** Round 1 may have used Yahoo data; Round 2 used OANDA (now the canonical source per Phase 2).
3. **Post-2024 regime.** Gold entered a secular bull run in late 2024. FVG signal (fair value gap = inefficiency) fires more often in trending markets but the trend itself is already captured by the 4H trend gate + MA cross — so FVG becomes redundant boost rather than independent signal.

## Infrastructure Bugs Found

- `tests/ablation_study.py:144` — referenced `v2_module.detect_ma_whipsaw` which had been removed. Guarded with `hasattr()`.
- `tests/ablation_study.py:161` — MA-convention test didn't actually invert the comparison (used same `w_curr > s_curr` as v2). Fixed to test genuine SMMA>WMA=bull convention.
- `main.py:284` — default `--strategy sbrs_v1`. SBRS 1.1 is retired; changed to `sbrs_v2`.

## Related

- [[63-FVG-Downshift-Change]] — Pre/post comparison of the FVG weight change
- [[64-Risk-Manager-Gold-Cap-Fix]] — Gold DD cap fix (Layer 2 regression)
- [[51-Confluence-Scoring-System]] — Confluence scoring architecture
- [[48-Ablation-Study-Results]] — Round 1 (historical, findings now partially superseded)
- [[61-Audit-Remediation-2026-04]] — Direction-normalisation bug fix
