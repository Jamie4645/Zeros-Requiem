---
name: ablation
description: Run the 17-config ablation study to measure each SBRS feature's contribution. Use when the user says "ablation", "feature impact", "test removing", "what if we disable", or "isolate feature".
user_invocable: true
argument-hint: [period]
allowed-tools: Bash(py -m tests.ablation_study:*), Bash(python -m tests.ablation_study:*), Read
---

# /ablation — SBRS Feature Isolation Study

Wraps `tests/ablation_study.py`. Monkey-patches constants one at a time, reruns the full backtest, reports each feature's $ / Sharpe / PF impact.

## Protocol

### Step 1 — Parse arg
| Arg | Default | Use |
|---|---|---|
| Period | `10y` | `2y` for quick iteration, `10y` for authoritative |

### Step 2 — Run (single shell call — heavy, can take several minutes)
```bash
py -m tests.ablation_study --period <PERIOD>
```

### Step 3 — Present ranked contribution table
From stdout, produce:
```
═══════════════════════════════════════════════════════
  ABLATION: SBRS 2.0 vs variants, <PERIOD> Gold 1H
═══════════════════════════════════════════════════════
  Variant                   PnL     Δ vs Base   Sharpe  PF
  Baseline (full v2.0)      $X      —           X.XX    X.XX
  1. No FVG                 $X      -$X,XXX     X.XX    X.XX    ← CRITICAL
  2. No Liquidity Sweep     $X      -$XXX       X.XX    X.XX
  ...
═══════════════════════════════════════════════════════

  TOP CONTRIBUTORS (do not remove):
  1. FVG: -$X,XXX when disabled
  2. ...

  DEAD WEIGHT (consider removing if session-consistent):
  ...
```

### Step 4 — Compare to known baseline
Published ablation results (see `knowledge-base/48-Ablation-Study-Results.md`):
- FVG disabled: **-$1,519** (CRITICAL signal)
- Liquidity sweep disabled: valuable
- Whipsaw filter: HURTS perf (confirmed removed)
- Squeeze/chop filters: dead weight (confirmed removed)

If current run contradicts this by >20%, FLAG — data or strategy drift.

### Step 5 — Interpretation rules
- Feature impact >$1,000: CRITICAL, keep
- Feature impact $200–1,000: valuable
- Feature impact <$200 or negative: candidate for removal
- Don't remove anything without user confirmation (CLAUDE.md rule)

## Remember
Ablation tests the *contribution*, not the *necessity*. A feature with small impact on Gold may still matter on GBP/USD. Run per-asset before removing anything from the core pipeline.
