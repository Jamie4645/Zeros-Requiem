---
tags: [bug-fix, risk, gold]
aliases: [BE Stop Fix, Breakeven Stop Fix]
related: [[CLAUDE]], [[25-Walk-Forward-Full-Results]], [[27-P3-P6-Forex-Fixes]], [[16-Risk-Management-Elite-System]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the Gold Sharpe/PF/PnL numbers and "Elite Benchmark Status: PASS"
> table below are artifacts of the same flawed backtest engine later found to have no realistic-fill
> edge, not current state. Retained as historical record only. Current canon: root `CLAUDE.md` +
> [[00-MOC-Zeros-Requiem]].

# P1: Gold Breakeven Stop Fix

**Date:** 2026-02-12

---

## Problem

The N2 breakeven stop (move SL to entry+buffer at 1.5R profit) was applied to ALL regimes except `gold_ny_momentum` and `gold_daily_momentum`. This meant `gold_asia_mr` and `gold_daily_mr` were still getting their winners clipped at 1.5R.

Gold's edge profile is **asymmetric**: rare large wins (avg $212) vs frequent small losses (avg $84). The breakeven stop destroys this asymmetry by cutting off the fat-tail winners that make the edge profitable.

Meanwhile, Forex pairs benefit from the BE stop (GBP/USD WR jumped to 50%, PF 1.54) because their edge is more symmetric — more frequent, smaller moves where locking in breakeven reduces drawdowns.

## Fix

**File:** `src/core/engine.py` (line 135)

**Before:**
```python
gold_momentum_regimes = ('gold_ny_momentum', 'gold_daily_momentum')
```

**After:**
```python
gold_regimes = ('gold_ny_momentum', 'gold_daily_momentum', 'gold_asia_mr', 'gold_daily_mr')
```

One line. All four Gold regime labels now excluded from the breakeven stop.

## Results — Gold 4H (1 Year)

| Metric | Post-N2 (BE on Gold) | After Fix (BE off Gold) | Change |
|--------|---------------------|------------------------|--------|
| **Sharpe** | 0.69 | **1.49** | +116% |
| **Profit Factor** | 1.22 | **1.71** | +40% |
| **Total PnL** | +$868 | **+$2,573** | +196% |
| **Total Return** | ~8.7% | **25.73%** | +17pp |
| **Max Drawdown** | 7.3% | **3.14%** | -57% (better) |
| **Expectancy** | ~$11/trade | **$35.24/trade** | +220% |
| **Avg Win** | clipped | **$205.75** | fat-tail restored |
| **Avg Loss** | — | **$83.72** | 2.46:1 ratio |
| **Expectancy (R)** | — | **0.290R/trade** | solid |
| **RoMaD** | — | **7.37** | excellent |

## Results — Full Quick Test (All Regimes)

| Regime | Trades | WR | PnL | PF | MaxDD |
|--------|--------|----|-----|-----|-------|
| Gold 1D | 44 | 55% | +$2,197 | 2.05 | 5.1% |
| **Gold 4H** | **73** | **41%** | **+$2,574** | **1.71** | **3.1%** |
| Gold 1H | 78 | 33% | -$104 | 0.98 | 11.6% |
| EUR/USD 4H | 22 | 36% | +$38 | 1.03 | 6.4% |
| EUR/USD 1H | 57 | 42% | +$93 | 1.02 | 11.9% |
| EUR/USD 1D | 5 | 60% | +$202 | 4.22 | 0.6% |
| BTC 4H | 11 | 36% | +$115 | 1.18 | 4.9% |
| BTC 1H | 11 | 45% | +$234 | 1.52 | 2.6% |
| **COMBINED** | **301** | — | **+$5,348** | — | — |

## Walk-Forward Validation (Post-Fix)

### Gold Daily (5Y, 8 windows) — VALIDATED
- Consistency: **88%** (7/8 profitable)
- Combined PnL: +$3,031
- Edge degradation: +$63/window (improving)
- W8 (most recent): +$1,569, 86% WR, Sharpe 2.23
- **Unchanged from pre-fix — daily was already excluding momentum from BE**

### Gold 4H (2Y, 6 windows) — IMPROVED
- Consistency: **50%** (3/6) — was 33% (2/6) before fix
- Combined PnL: -$341 — was -$661 before fix (+$320 improvement)
- Edge degradation: +$195/window (improving)
- W4-W6 (recent year): all 3 windows profitable (+$849, +$36, +$472)
- W1-W3 (early 2024): 3 losing windows (lower Gold vol, ranging market)
- **Edge is real but concentrated in current volatile Gold regime**

## Elite Benchmark Status (Post-Fix)

| Benchmark | Target | Gold 4H | Status |
|-----------|--------|---------|--------|
| Sharpe | >= 1.5 | **1.49** | 0.01 away |
| Profit Factor | >= 1.5 | **1.71** | **PASS** |
| Annual Return | >= 20% | **25.73%** | **PASS** |
| Max Drawdown | <= 15% | **3.14%** | **PASS** |
| Expectancy > 0 | positive | **$35.24** | **PASS** |
| 500 trades | per strategy | 73 | MISS (needs time + markets) |
| Walk-forward 5Y | consistency | 50% (4H) | PARTIAL |

## Key Insight

The breakeven stop is fundamentally a regime-dependent tool:
- **Gold** = asymmetric edge → rare big winners → **disable BE stop**
- **Forex** = symmetric edge → frequent small moves → **enable BE stop**
- **Crypto** = TBD (small sample, keep BE for now)

This is exactly what Mark Douglas teaches: every market regime has its own statistical profile. Applying one-size-fits-all exit management destroys the edge.
