---
tags: [validation, risk, methodology]
aliases: [Monte Carlo, MC Simulation]
related: [[CLAUDE]], [[16-Risk-Management-Elite-System]], [[25-Walk-Forward-Full-Results]], [[29-P5-P7-P8-OANDA-Portfolio]], [[00-MOC-Zeros-Requiem]]
---

# P4: Monte Carlo Simulation

**Date:** 2026-02-12

---

## Purpose

Monte Carlo simulation is the last Elite Benchmark that wasn't built:
> Monte Carlo: < 5% probability of 20% drawdown

The simulation resamples from actual trade PnLs with replacement to generate 10,000 synthetic equity curves. This answers: "Given this trade distribution, how likely am I to hit a catastrophic drawdown?"

## Implementation

**New file:** `src/core/monte_carlo.py`

**Algorithm:**
1. Extract PnL array from backtest trades
2. Generate `(n_simulations, n_trades)` random indices (vectorised with numpy)
3. Build cumulative equity curves for all sims simultaneously
4. Compute max drawdown per simulation
5. Report percentiles and probabilities

**Performance:** 10,000 sims x 73 trades = under 3 seconds (fully vectorised with numpy).

**CLI integration:** `py main.py --symbol GC=F --interval 4h --period 1y --monte-carlo`

Optional: `--mc-sims 50000` to increase simulation count.

## Results

### Gold 4H (73 trades, 10,000 sims)

| Metric | Value |
|--------|-------|
| Median Max DD | 6.06% |
| 95th Percentile DD | 11.85% |
| 99th Percentile DD | 16.30% |
| **Prob of 15% DD** | **1.65%** |
| **Prob of 20% DD** | **0.28%** [ELITE: PASS] |
| Prob of 30% DD | 0.00% |
| Prob Profitable | 97.4% |
| Worst 5% PnL | +$389 (still profitable!) |
| Prepare for streak | 11 consecutive losses |

### Gold Daily (44 trades, 10,000 sims)

| Metric | Value |
|--------|-------|
| Median Max DD | 4.65% |
| 95th Percentile DD | 9.47% |
| **Prob of 20% DD** | **0.02%** [ELITE: PASS] |
| Prob Profitable | 98.0% |
| Worst 5% PnL | +$410 |
| Prepare for streak | 7 consecutive losses |

### GBP/USD 4H (25 trades, 10,000 sims)

| Metric | Value |
|--------|-------|
| Median Max DD | 4.69% |
| 95th Percentile DD | 10.20% |
| **Prob of 20% DD** | **0.02%** [ELITE: PASS] |
| Prob Profitable | 83.7% |
| Worst 5% PnL | -$540 (can lose in worst scenarios) |
| Prepare for streak | 7 consecutive losses |

## Elite Benchmark Summary

| Strategy | Prob 20% DD | Target | Status |
|----------|-------------|--------|--------|
| Gold 4H | 0.28% | < 5% | **PASS** |
| Gold Daily | 0.02% | < 5% | **PASS** |
| GBP/USD 4H | 0.02% | < 5% | **PASS** |

All three core strategies pass the Monte Carlo Elite Benchmark with massive margin. The highest risk is Gold 4H at 0.28% — still 18x below the 5% threshold.

## Key Insights

1. **Gold 4H is robust**: 97.4% chance of profit, even worst 5% of scenarios make money
2. **Gold Daily is the safest**: 98% profitable, 0.02% chance of 20% DD
3. **GBP/USD is solid but smaller edge**: 83.7% profitable, small chance of loss in worst scenarios
4. **Prepare for 7-11 consecutive losses**: The Monte Carlo confirms this is normal — Mark Douglas Fundamental Truth #3 in action
5. **Position sizing is critical**: The 1% risk per trade + ATR sizing keeps drawdowns manageable even during losing streaks

## Caveats

- Monte Carlo assumes trades are independent (no serial correlation)
- With 25-73 trades, the resampling pool is moderate — results become more reliable with 100+ trades
- Real markets can have regime shifts that create correlated losses (not captured by resampling)
- The simulation uses the exact trade distribution — if the edge degrades, future DD could be worse
