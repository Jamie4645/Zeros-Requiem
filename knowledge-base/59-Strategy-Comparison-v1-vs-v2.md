---
tags: [reference, validation, milestone]
aliases: [Strategy Comparison, v1 vs v2, SBRS Comparison, Full Results]
related: [[47-SBRS-2.0-Upgrade]], [[55-Multi-Asset-Expansion]], [[56-Risk-Manager-Calibration]], [[57-Monte-Carlo-Gold-v2]], [[58-GBP-USD-Discovery]]
date: 2026-04-05
---

# 59 — SBRS 1.1 vs 2.0: Complete Strategy Comparison

> *"An edge is nothing more than an indication of a higher probability of one thing happening over another."* — Mark Douglas

## Purpose

This is the single reference document for all SBRS backtest results as of 2026-04-05. It covers the v1.1-to-v2.0 upgrade on Gold, and the v2.0 expansion across 10 instruments in 4 asset classes.

---

## Gold Head-to-Head: SBRS 1.1 vs 2.0

**Data:** 10Y OANDA (59,045 bars, 2016-04 to 2026-04) | Slippage: 1.5 pips | Risk: 1%

| Metric | SBRS 1.1 | SBRS 2.0 | Delta |
|--------|----------|----------|-------|
| Total Trades | 458 | 2,252 | +392% |
| Setups Found | 1,247 | 2,110 | +69% |
| Trades Blocked | 789 (63%) | 1 (0.05%) | -99.9% |
| Win Rate | 41.5% | 38.9% | -2.6pp |
| Total PnL | $10,217 | $146,256 | +1,332% |
| Total Return | 102% | 1,463% | +1,361pp |
| Profit Factor | 1.43 | 1.97 | +37.8% |
| Sharpe Ratio | 0.81 | 1.77 | +118% |
| Sortino Ratio | 0.27 | 1.07 | +296% |
| Max Drawdown | 10.14% | 9.17% | -0.97pp |
| Expectancy / Trade | $22.31 | $64.95 | +191% |
| Expectancy (R) | 0.223R | 0.116R | -48% |
| Avg Win | $178.25 | $338.57 | +90% |
| Avg Loss | $88.25 | $109.25 | +24% |
| Payoff Ratio | 2.02:1 | 3.10:1 | +53% |
| RoMaD | 4.48 | 42.51 | +849% |
| Max Consecutive Wins | 7 | 6 | -1 |
| Max Consecutive Losses | 7 | 15 | +8 |
| **Benchmarks Met** | **3/7** | **7/7** | — |
| Walk-Forward (8 win) | — | 75% (6/8) | — |
| Monte Carlo Profitable | — | 100% | — |

### What Drove the Improvement

| Change | Impact |
|--------|--------|
| Confluence scoring replaces binary MA gate | +1,794 trades (4x more setups pass) |
| Counter-trend trades enabled (score >= 2.0) | ~15% of v2 trades are counter-trend |
| FVG detection (+1.0 score) | Highest-impact single signal (ablation: +$1,519) |
| Wider retest tolerance (0.5 -> 0.7 ATR longs) | More retests qualify, better avg win |
| Chop filter REMOVED from entry loop | Was killing valid setups in Gold |
| MA convention: WMA > SMMA = bullish | Ablation-validated, +$3,300 vs reverse |

See [[48-Ablation-Study-Results]] and [[54-Fine-Tuning-Process]] for the full ablation study.

---

## SBRS 2.0 Multi-Asset Results (10 Instruments)

**All tests:** 1H timeframe | Slippage: 1.5 pips | Risk: 1% | $10k starting capital

| Asset | Class | Data | Trades | WR | PnL | PF | Sharpe | DD | WF | Tier |
|-------|-------|------|--------|----|-----|----|--------|----|----|------|
| **Gold** | Commodity | 10Y OANDA | 2,252 | 38.9% | $146,256 | 1.97 | 1.77 | 9.17% | 75% (6/8) | **1** |
| **GBP/USD** | Forex | 10Y OANDA | 1,323 | 35.8% | $152,680 | 2.69 | 2.00 | 7.84% | 62% (5/8) | **2** |
| **NASDAQ** | Index | 10Y IBKR | 888 | 45.3% | $27,910 | 1.57 | 1.11 | 17.84% | 88% (7/8) | **1** |
| **DAX** | Index | 10Y IBKR | 1,096 | 41.8% | $33,912 | 1.53 | 1.18 | 11.41% | 88% (7/8) | **1** |
| **USD/JPY** | Forex | 10Y OANDA | 1,228 | 34.5% | $21,811 | 1.27 | 0.84 | 15.65% | — | 3 |
| **EUR/USD** | Forex | 10Y OANDA | 501 | 32.5% | $2,532 | 1.08 | 0.23 | 20.14% | — | 3 |
| **Bitcoin** | Crypto | 2Y Yahoo | 747 | 34.7% | $31,539 | 1.59 | 2.76 | 9.56% | — | 2 |
| **Ethereum** | Crypto | 2Y Yahoo | 748 | 32.2% | $33,890 | 1.63 | 2.63 | 9.70% | — | 2 |
| **S&P 500** | Index | 10Y IBKR | 64 | 32.8% | -$1,654 | 0.63 | -0.39 | 20.40% | — | 4 |
| **AUD/USD** | Forex | 10Y OANDA | 153 | 28.8% | -$1,197 | 0.89 | -0.15 | 21.29% | — | 4 |

### Asset-Specific R:R Targets (v2.0)

| Asset Class | With-Trend R:R | Counter-Trend R:R | Retest Tolerance |
|-------------|---------------|-------------------|-----------------|
| Gold | 3.0 | 2.0 | 0.7 ATR (long) / 0.3 ATR (short) |
| Forex | 2.5 | 2.0 | 0.3 ATR (both) |
| Indices | 2.0 | 2.0 | 0.6 ATR (long) / 0.3 ATR (short) |
| Crypto | 2.5 | 2.0 | 0.5 ATR (both) |

---

## Walk-Forward Validation (All Tested Assets)

### Gold 1H — 75% (6/8)
```
W1 2016-04→2017-07: $7,715  PF 1.48  Sharpe 1.84  ✅
W2 2017-07→2018-10: $940    PF 1.17  Sharpe 0.47  ✅
W3 2018-10→2020-01: $1,634  PF 1.21  Sharpe 0.71  ✅
W4 2020-01→2021-04: $7,604  PF 1.51  Sharpe 1.96  ✅
W5 2021-04→2022-07: -$608   PF 0.88  Sharpe -0.29 ❌
W6 2022-07→2023-10: -$76    PF 0.99  Sharpe 0.02  ❌
W7 2023-10→2025-01: $328    PF 1.06  Sharpe 0.22  ✅
W8 2025-01→2026-04: $1,229  PF 1.22  Sharpe 0.60  ✅
Combined: $18,765 | Edge slope: -$736/window (slightly degrading)
```

### DAX 1H — 88% (7/8)
```
W1 2016-03→2017-06: $2,217  PF 1.25  Sharpe 0.82  ✅
W2 2017-06→2018-09: $2,546  PF 1.39  Sharpe 1.14  ✅
W3 2018-09→2019-12: $4,946  PF 1.60  Sharpe 1.71  ✅
W4 2019-12→2021-03: $2,079  PF 1.28  Sharpe 0.94  ✅
W5 2021-03→2022-06: $1,218  PF 1.18  Sharpe 0.53  ✅
W6 2022-06→2023-09: $358    PF 1.05  Sharpe 0.22  ✅
W7 2023-09→2024-12: $3,647  PF 1.46  Sharpe 1.52  ✅
W8 2024-12→2026-03: -$218   PF 0.97  Sharpe -0.04 ❌
Combined: $16,794 | Edge slope: -$312/window (stable)
```

### NASDAQ 1H — 88% (7/8)
```
W1 2016-03→2017-06: $948    PF 1.15  Sharpe 0.50  ✅
W2 2017-06→2018-09: $60     PF 1.01  Sharpe 0.08  ✅
W3 2018-09→2019-12: $2,888  PF 1.62  Sharpe 1.35  ✅
W4 2019-12→2021-03: -$681   PF 0.89  Sharpe -0.29 ❌
W5 2021-03→2022-06: $3,946  PF 1.80  Sharpe 1.92  ✅
W6 2022-06→2023-09: $5,726  PF 1.82  Sharpe 2.15  ✅
W7 2023-09→2024-12: $5,053  PF 1.94  Sharpe 2.02  ✅
W8 2024-12→2026-03: $1,556  PF 1.27  Sharpe 0.77  ✅
Combined: $19,496 | Edge slope: +$504/window (IMPROVING)
```

### GBP/USD 1H — 62% (5/8) — FAILS 75% target
```
W1 2016-04→2017-07: $7,373  PF 1.77  Sharpe 2.22  ✅
W2 2017-07→2018-10: $2,288  PF 1.22  Sharpe 0.81  ✅
W3 2018-10→2020-01: $712    PF 1.08  Sharpe 0.34  ✅
W4 2020-01→2021-04: -$1     PF 1.00  Sharpe 0.07  ❌
W5 2021-04→2022-07: $3,404  PF 1.31  Sharpe 1.19  ✅
W6 2022-07→2023-10: -$281   PF 0.98  Sharpe -0.02 ❌
W7 2023-10→2025-01: -$2,012 PF 0.59  Sharpe -1.19 ❌  ← Problem window
W8 2025-01→2026-04: $1,810  PF 1.21  Sharpe 0.74  ✅
Combined: $13,293 | Edge slope: -$715/window (degrading)
```

---

## Index Improvement: Before vs After Risk Manager Fix

See [[56-Risk-Manager-Calibration]] for technical details.

| Index | Before (Trades / PF) | After (Trades / PF) | Root Cause |
|-------|---------------------|---------------------|------------|
| S&P 500 | 37 / 0.69 | 64 / 0.63 | No edge (strategy doesn't fit S&P) |
| NASDAQ | 37 / 0.87 | **888 / 1.57** | 10% DD breaker was killing sample size |
| DAX | 19 / 0.24 | **1,096 / 1.53** | 10% DD breaker + 3.0R too aggressive |

Changes: DD cap 10% -> 20%, R:R 3.0 -> 2.0 for indices, concurrent risk 8% -> 10%.

---

## Monte Carlo: Gold v2.0 (10,000 Simulations)

See [[57-Monte-Carlo-Gold-v2]] for full analysis.

| Metric | Value |
|--------|-------|
| Probability Profitable | 100% |
| Median Max Drawdown | 14.40% |
| Prob of 15% DD | 46.39% |
| Prob of 20% DD | 23.86% |
| 95th pctile losing streak | 19 trades |
| Recommended starting risk | **0.5%** (not 1%) |

---

## Tier Classification

### Tier 1 — Walk-Forward Validated (Paper Trade Ready)
- **Gold** — 75% WF, 7/7 benchmarks, MC 100% profitable
- **DAX** — 88% WF, most consistent index
- **NASDAQ** — 88% WF, edge improving over time

### Tier 2 — Promising (Needs More Validation)
- **GBP/USD** — PF 2.69 (highest) but WF 62% (5/8). W7 under investigation.
- **Bitcoin** — PF 1.59, Sharpe 2.76. Only 2Y data (red flag).
- **Ethereum** — PF 1.63, Sharpe 2.63. Only 2Y data.

### Tier 3 — Marginal Edge
- **USD/JPY** — PF 1.27, thin edge, 19-bar max losing streak
- **EUR/USD** — PF 1.08, barely profitable, 22-bar max losing streak

### Tier 4 — No Edge (Rejected)
- **S&P 500** — PF 0.63, no edge found
- **AUD/USD** — PF 0.89, 28.8% WR

---

## Strategic Roadmap

```
YOU ARE HERE                     NEXT MILESTONES
     |
     v
[3 WF-validated]  -->  [Paper trade 60-90d]  -->  [Live 0.5% risk]  -->  [5-strategy portfolio]
 Gold 75%               Gold + DAX + NASDAQ        Gold first              + GBP/USD + BTC?
 DAX 88%                                           then indices
 NASDAQ 88%
```

**Goal:** 5+ strategies at 0.15-0.2% risk each = ~1% total portfolio risk.

---

## Related

- [[47-SBRS-2.0-Upgrade]] — SBRS 2.0 upgrade documentation
- [[48-Ablation-Study-Results]] — Ablation study driving the v2.0 design
- [[55-Multi-Asset-Expansion]] — Multi-asset expansion session
- [[56-Risk-Manager-Calibration]] — Risk manager fix for indices
- [[57-Monte-Carlo-Gold-v2]] — Monte Carlo simulation results
- [[58-GBP-USD-Discovery]] — GBP/USD deep-dive and W7 failure

---

*Created: 2026-04-05 | Status: Reference Document*
