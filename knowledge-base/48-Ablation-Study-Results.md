--
tags: [research, validation, methodology]
aliases: [Ablation Study, Feature Testing, Feature Isolation]
related: [[47-SBRS-2.0-Upgrade]], [[49-MA-Convention-Discovery]], [[51-Confluence-Scoring-System]], [[CLAUDE]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **VOID/RETIRED (see root `CLAUDE.md`).** This ablation ran on SBRS 2.0's phantom-fill engine
> (2026-06-01 audit) and SBRS is now fully retired. Feature-contribution numbers below are void
> artifacts, not current state. Retained as historical record only. Current strategy: ZTT
> (`knowledge-base/89-ZTT-Rebuild.md`).

# Ablation Study — Feature Contribution Analysis

**Date:** 2026-04-05
**Data:** Gold 1H, 10Y, 59,049 bars via OANDA
**Method:** Systematically disable each feature/filter and measure impact on PnL, PF, trade count

---

## What Is an Ablation Study?

A technique from machine learning research applied to trading strategy development. Instead of guessing which features help, we scientifically isolate each one by disabling it and measuring the delta. Features that hurt when removed are HELPING. Features that improve when removed are HURTING.

---

## Full Results Table

| # | Test | Trades | PF | PnL | vs Baseline |
|---|------|--------|------|-------|-------------|
| -- | **Baseline (pre-tuning v2.0)** | **57** | **1.14** | **$513** | **BASE** |
| 1 | No FVG | 19 | 0.37 | -$1,006 | -296% |
| 2 | No Liquidity Sweep | 73 | 1.05 | $232 | -55% |
| 3 | No FVG + No Liquidity | 48 | 0.89 | -$362 | -170% |
| 4 | No MA Cross Score | 64 | 1.21 | $900 | +76% |
| 5 | MA Cross ONLY | 48 | 0.89 | -$362 | -170% |
| 6 | No Level Gate | 62 | 1.09 | $376 | -27% |
| 7 | No Counter-Trend | 59 | 0.92 | -$294 | -157% |
| 8 | No Session Filter | 71 | 1.06 | $256 | -50% |
| 9 | No Squeeze Filter | 57 | 1.14 | $513 | 0% |
| 10 | No Whipsaw Detection | 92 | 1.15 | $906 | +77% |
| **11** | **Old MA Convention** | **167** | **1.36** | **$3,814** | **+643%** |
| 12 | Higher Threshold (1.5) | 55 | 1.09 | $318 | -38% |
| 13 | Kitchen Sink OFF | 18 | 0.41 | -$870 | -270% |
| 14 | Tight Retest (0.3 ATR) | 79 | 1.11 | $577 | +12% |
| 15 | Wide Retest (0.8 ATR) | 85 | 1.12 | $678 | +32% |
| 16 | No False BO Filter | 97 | 1.02 | $149 | -71% |
| 17 | No Chop Filter | 57 | 1.14 | $513 | 0% |

---

## Feature Impact Summary

### HELPING (removing makes performance WORSE)

| Feature | Impact | Verdict |
|---------|--------|---------|
| **FVG Detection** | -$1,519 when removed | CRITICAL — keep |
| **Counter-Trend** | -$807 when removed | VALUABLE — keep |
| **False BO Filter** | -$364 when removed | PROTECTIVE — keep |
| **Session Filter** | -$257 when removed | PROTECTIVE — keep |
| **Level Quality Gate** | -$137 when removed | MINOR — keep |

### HURTING (removing makes performance BETTER)

| Feature | Impact | Verdict |
|---------|--------|---------|
| **"Corrected" MA Convention** | +$3,301 when reverted | REVERT — the "fix" destroyed profit |
| **Whipsaw Filter** | +$393 when removed | REMOVE — filters good signals |
| **MA Cross weight at 1.0** | +$387 when reduced | REDUCE to 0.5 |

### DEAD WEIGHT (zero measurable effect)

| Feature | Verdict |
|---------|---------|
| **Squeeze Filter** | Never triggers on Gold |
| **Chop Filter** | Never triggers during valid setups |

---

## Actions Taken

All findings were applied to SBRS 2.0:
1. MA convention reverted to WMA > SMMA = bullish
2. Whipsaw filter removed
3. Retest tolerance widened to 0.7 ATR
4. MA cross score reduced to 0.5
5. Squeeze/chop dead code removed from entry loop

Result after combined changes: **$146,256 PnL, PF 1.97, Sharpe 1.77** (see [[47-SBRS-2.0-Upgrade]])

---

## Test Runner

The ablation framework is reusable: `tests/ablation_study.py`

```bash
py -m tests.ablation_study --period 10y           # Full run
py -m tests.ablation_study --period 5y             # Quick validation
py -m tests.ablation_study --symbol ^GSPC          # Test on indices
```

---

## Related

- [[47-SBRS-2.0-Upgrade]] — The strategy these findings optimised
- [[49-MA-Convention-Discovery]] — Deep dive on the MA convention question
- [[51-Confluence-Scoring-System]] — The scoring system that was tuned
- [[00-MOC-Zeros-Requiem]]
