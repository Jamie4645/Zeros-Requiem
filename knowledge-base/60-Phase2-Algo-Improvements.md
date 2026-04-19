---
tags: [research, strategy, milestone]
aliases: [Algo Improvements, Phase 2 Results, ATR Filter, Adaptive RR]
related: [[55-Multi-Asset-Expansion]], [[59-Strategy-Comparison-v1-vs-v2]], [[58-GBP-USD-Discovery]]
date: 2026-04-05
---

# 60 — SBRS 2.0 Algo Improvements (Post-Expansion)

Three improvements were implemented and tested on 2026-04-05. All three passed validation gates and were kept.

---

## What Changed

### 1. ATR Percentile Volatility Filter
Skip entries when ATR is below the 25th percentile of the last 100 bars. Targets low-volatility dead zones.
- Enabled for: Gold, Forex
- Disabled for: Indices (session filters sufficient), Crypto

### 2. Adaptive R:R Based on ATR Regime
Scale TP target by current ATR relative to 50-bar average:
- `effective_rr = base_rr * clamp(current_atr / avg_atr, 0.7, 1.5)`
- High vol: wider TP (up to 1.5x). Low vol: tighter TP (down to 0.7x).

### 3. Indices-Specific Exit Optimization
- Max hold: 40 -> 25 bars for indices
- BE trigger: 1.5R -> 1.0R for indices
- Trailing trigger: 3.0R -> 2.0R for indices

---

## Results vs Baseline

### Single Backtests (10Y)

| Asset | Metric | Before | After | Change |
|-------|--------|--------|-------|--------|
| **Gold** | PF | 1.97 | **2.85** | +45% |
| **Gold** | Sharpe | 1.77 | **2.11** | +19% |
| **Gold** | DD | 9.17% | **8.72%** | -0.45pp |
| **DAX** | PF | 1.53 | **1.56** | +2% |
| **DAX** | DD | 11.41% | **9.81%** | -1.6pp |
| **DAX** | WR | 41.8% | **47.7%** | +5.9pp |
| **NASDAQ** | PF | 1.57 | **1.61** | +2.5% |
| **NASDAQ** | WR | 45.3% | **52.8%** | +7.5pp |
| **GBP/USD** | PF | 2.69 | **2.72** | +1% |
| **GBP/USD** | DD | 7.84% | **7.58%** | -0.26pp |
| **GBP/USD** | Max Streak | 17 | **13** | -4 |

### Walk-Forward Consistency

| Asset | Before WF | After WF | Change |
|-------|-----------|----------|--------|
| Gold | 75% (6/8) | 75% (6/8) | Maintained |
| DAX | 88% (7/8) | 88% (7/8) | Maintained |
| NASDAQ | 88% (7/8) | 88% (7/8) | Maintained |
| **GBP/USD** | **62% (5/8)** | **100% (8/8)** | **+38pp (FIXED)** |

### Crypto Walk-Forward (5Y Binance Data — NEW)

| Asset | WF | Status |
|-------|------|--------|
| **ETH** | **75% (6/8)** | **Tier 1 — Validated** |
| BTC | 50% (4/8) | Tier 3 — Bear markets destroy edge |

---

## GBP/USD Fix Details

The ATR percentile filter eliminated the W7 disaster:
- Before: W7 = -$2,012, 21.5% WR, PF 0.59
- After: W7 = +$345, 31.1% WR, PF 1.04

The filter correctly identified Oct 2023 - Jan 2025 as a low-volatility regime for GBP/USD and blocked the worst entries. Combined WF went from 62% to 100%.

---

## Updated Portfolio (5 Walk-Forward Validated Strategies)

| Strategy | WF | PF | DD | Status |
|----------|------|-----|------|--------|
| Gold 1H | 75% (6/8) | 2.85 | 8.72% | **Live Ready** |
| GBP/USD 1H | 100% (8/8) | 2.72 | 7.58% | **Paper Ready** |
| DAX 1H | 88% (7/8) | 1.56 | 9.81% | **Paper Ready** |
| NASDAQ 1H | 88% (7/8) | 1.61 | 17.99% | **Paper Ready** |
| ETH 1H | 75% (6/8) | — | — | **Paper Ready** |

**5 validated strategies across 4 asset classes. The 5-market goal is met.**

---

## Related

- [[55-Multi-Asset-Expansion]] — Pre-improvement multi-asset results
- [[59-Strategy-Comparison-v1-vs-v2]] — Complete v1.1 vs v2.0 comparison
- [[58-GBP-USD-Discovery]] — GBP/USD investigation (now resolved)
- [[57-Monte-Carlo-Gold-v2]] — Gold Monte Carlo results

---

*Created: 2026-04-05 | Status: Validated & Applied*
