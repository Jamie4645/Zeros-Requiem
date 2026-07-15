---
tags: [validation, risk, gold]
aliases: [Monte Carlo Gold v2, MC Simulation, Drawdown Risk]
related: [[55-Multi-Asset-Expansion]], [[28-P4-Monte-Carlo]], [[47-SBRS-2.0-Upgrade]]
date: 2026-04-05
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the Monte Carlo drawdown/profitability figures below are void
> artifacts, not current state. Retained as historical record only. Current canon: root `CLAUDE.md`
> + [[00-MOC-Zeros-Requiem]].

# 57 — Monte Carlo Simulation: Gold SBRS 2.0

## Setup

- **Simulations:** 10,000
- **Trades per sim:** 2,252 (full 10Y Gold backtest)
- **Method:** Random resampling of trade PnL sequence
- **Slippage:** ON (1.5 pips modelled)

---

## Results

### Drawdown Risk

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Median Max DD | 14.40% | ≤15% | Borderline |
| 95th Percentile DD | 31.88% | — | High |
| Prob of 15% DD | 46.39% | <5% | **FAIL** |
| Prob of 20% DD | 23.86% | <5% | **FAIL** |
| Prob of 30% DD | 6.35% | — | Concerning |
| Prob of 50% DD (ruin) | 0.42% | <1% | ✅ Pass |

### Profit Distribution

| Metric | Value |
|--------|-------|
| Median Final PnL | $145,772 |
| Mean Final PnL | $146,119 |
| 5th Percentile (worst 5%) | $111,751 |
| 95th Percentile (best 5%) | $182,121 |
| Probability Profitable | **100%** |

### Losing Streaks

| Metric | Value |
|--------|-------|
| Median Max Streak | 14 trades |
| 95th Percentile | 19 trades |

---

## Key Takeaway: Risk Sizing

The Monte Carlo reveals a critical insight: while Gold SBRS 2.0 is **100% profitable** over 2,252 trades, the path to that profit includes a **46% chance of hitting 15% drawdown** at some point.

### Recommended Position Sizing

| Account Size | Risk Per Trade | Rationale |
|-------------|---------------|-----------|
| $10k-$25k | **0.5%** | MC shows 1% is too aggressive for DD tolerance |
| $25k-$50k | 0.3-0.5% | Tighter as account grows |
| $50k+ | 0.2-0.3% | Elite sizing |

**DO NOT start live at 1% risk.** The backtest used 1% but MC shows the drawdown tail risk is real. Start at 0.5% and increase only after 60-90 days of live paper trading confirms the edge.

---

## Comparison to Previous Monte Carlo

| Metric | SBRS 1.1 ([[28-P4-Monte-Carlo]]) | SBRS 2.0 (this) |
|--------|----------------------------------|-----------------|
| Trades | ~894 | 2,252 |
| Prob Profitable | ~95% | **100%** |
| Median DD | ~12% | 14.4% |
| Max Losing Streak (95th) | ~12 | 19 |

v2.0 is more profitable but has slightly higher drawdown risk due to the 5x increase in trade count. More trades = more opportunities for clustering of losses.

---

## Related

- [[28-P4-Monte-Carlo]] — Original v1.1 Monte Carlo
- [[47-SBRS-2.0-Upgrade]] — SBRS 2.0 documentation
- [[55-Multi-Asset-Expansion]] — Multi-asset results
- [[16-Risk-Management-Elite-System]] — Risk management layers

---

*Created: 2026-04-05 | Status: Validated*
