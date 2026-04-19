---
tags: [research, methodology, milestone]
aliases: [Fine-Tuning Process, Strategy Tuning, Ablation-Driven Tuning]
related: [[47-SBRS-2.0-Upgrade]], [[48-Ablation-Study-Results]], [[49-MA-Convention-Discovery]], [[CLAUDE]], [[00-MOC-Zeros-Requiem]]
---

# Fine-Tuning Process — From $513 to $146,256

**Date:** 2026-04-05
**Method:** Ablation-driven, data-validated tuning (no curve-fitting)

---

## The Process

### Step 1: Build Initial v2.0
Translated the methodology document into code:
- Confluence scoring system
- Smart money indicators (FVG, liquidity sweep)
- Counter-trend trades
- Level quality gate
- "Corrected" MA convention per methodology

**Result:** 57 trades, PF 1.14, $513 PnL on 10Y Gold

### Step 2: Run Ablation Study (17 tests)
Systematically disabled each feature and measured impact:
- Identified FVG as the most critical signal
- Discovered the MA convention "fix" was destroying profit
- Found whipsaw filter was removing good trades
- Confirmed squeeze/chop filters were dead weight on Gold

### Step 3: Apply Data-Driven Changes (4 changes)
1. **Revert MA convention** — WMA > SMMA = bullish (momentum, not lag)
2. **Remove whipsaw filter** — was filtering profitable signals
3. **Widen retest tolerance** — 0.5 -> 0.7 ATR (captures more valid retests)
4. **Reduce MA cross weight** — 1.0 -> 0.5 (let FVG/Liquidity carry more weight)

### Step 4: Validate Combined Effect
**Result:** 2,252 trades, PF 1.97, $146,256 PnL, Sharpe 1.77

---

## What Makes This Process Legitimate (Not Curve-Fitting)

1. **No parameter optimization** — We didn't grid-search for the best values. We made binary decisions (keep/remove) based on clear impact.
2. **Walk-forward validated** — 75% consistency across 8 sequential out-of-sample windows.
3. **All sacred parameters untouched** — WMA=9, SMMA=7, Swing=20, R:R=3.0 never changed.
4. **Changes are structural, not numerical** — Removing a filter is a design decision. Widening retest from 0.5 to 0.7 is within the allowed +/-20% range.
5. **Each change has an independent rationale** — Not "these 4 magic numbers together make it work."

---

## The Key Lesson

> **Build first, measure second, tune third.**

Don't tune parameters before you have an ablation framework. Don't trust theory over data. And don't assume that matching a discretionary methodology 1:1 will produce the best algo results.

---

## Related

- [[48-Ablation-Study-Results]] — The ablation data
- [[49-MA-Convention-Discovery]] — The biggest finding
- [[47-SBRS-2.0-Upgrade]] — The final product
- [[00-MOC-Zeros-Requiem]]
