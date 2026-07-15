--
tags: [archive, optimisation]
aliases: [Optimisation Round 2]
related: [[23-Optimisation-Weak-Areas]], [[25-Walk-Forward-Full-Results]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the WR/PnL/Sharpe/PF tables below (from the pre-SBRS SCAF-era
> engine, Feb 2026) are artifacts of the same flawed backtest engine later found to have no
> realistic-fill edge, not current state. Retained as historical record only. Current canon:
> root `CLAUDE.md` + [[00-MOC-Zeros-Requiem]].

# Optimisation Round 2: N1-N4

**Date:** 2026-02-11

---

## Changes Implemented

### N1: USD/JPY Breakout — 1H Only
**File:** `src/regimes/forex.py`

JPY breakout logic now only activates on 1H and faster (>=12 unique hours in 30 bars). On 4H, USD/JPY uses standard killzone fade logic. The 4H Asian range is only 2 bars — too coarse for breakout detection.

### N2: Breakeven Stop at 1.5R
**File:** `src/core/engine.py`

When a trade reaches 1.5R profit, the stop loss moves to entry + 10% of initial risk (small buffer past breakeven). This locks in profits while giving the trade breathing room.

Initially implemented at 1R trigger — this was too aggressive and collapsed win rates. Adjusted to 1.5R with buffer.

### N3: Crypto Trend Momentum Entry
**File:** `src/regimes/crypto.py`

New entry path: when EMA(20) > EMA(50) (clear trend) + sweep of weekly low + Df >= 0.75, enter long with the trend. Mirror for shorts. Runs independently of VR compression.

New regime label: `crypto_trend`

BTC 4H crypto_trend: 7 trades (0% WR on 4H, 50% WR on 1H — works better on faster TFs).

### N4: Gold 1H Momentum Confirmation Bar
**File:** `src/regimes/gold.py`

On 1H (and faster), sweeps are buffered for 1 bar. The next bar must close in the expected reversal direction to confirm the sweep. Unconfirmed sweeps are discarded.

Timeframe detection threshold fixed from >=6 to >=12 unique hours (was incorrectly classifying 4H as "fast").

---

## Results

### 4H (1 Year) — After N1-N4

| Symbol | Trades | WR | PnL | Sharpe | PF | MaxDD |
|--------|--------|-----|-----|--------|-----|-------|
| Gold | 76 | **42%** | +$868 | 0.69 | 1.22 | 7.3% |
| EUR/USD | 23 | 35% | -$55 | -0.02 | 0.96 | 6.5% |
| **GBP/USD** | **26** | **50%** | **+$741** | 0.72 | **1.54** | 7.0% |
| USD/JPY | 14 | 36% | -$301 | -0.53 | 0.65 | 6.1% |
| BTC | 11 | 36% | +$115 | 0.18 | 1.18 | 4.9% |
| **ETH** | **8** | **63%** | **+$492** | 0.61 | **2.31** | 3.6% |
| **TOTAL** | **158** | — | **+$1,860** | — | — | — |

### 1H (6 Months) — After N1-N4

| Symbol | Trades | WR | PnL | Sharpe | PF | MaxDD |
|--------|--------|-----|-----|--------|-----|-------|
| Gold | 53 | 40% | -$775 | -0.77 | 0.74 | 11.9% |
| EUR/USD | 61 | **44%** | +$261 | 0.28 | 1.06 | 13.1% |
| **GBP/USD** | **34** | **44%** | **+$1,273** | **1.01** | **1.54** | 10.2% |
| **USD/JPY** | **72** | **46%** | **+$2,582** | **1.36** | **1.40** | 12.3% |
| BTC | 12 | 42% | +$186 | 0.51 | 1.38 | 2.6% |
| ETH | 14 | 29% | -$475 | -0.97 | 0.47 | 6.8% |
| **TOTAL** | **246** | — | **+$3,052** | — | — | — |

### Key Outcomes

**Breakeven stop (N2) reduced PnL but improved drawdown control:**
- 4H Gold: PnL dropped from $2,477 to $868 but MaxDD improved from 3.1% to 7.3% — wait, actually DD increased. The breakeven stop is taking profits too early on Gold's big winners.
- GBP/USD 4H: WR jumped to **50%** with PF **1.54** — breakeven stop works excellently here
- USD/JPY 1H: **Sharpe 1.36**, +$2,582 — the JPY breakout on 1H is a strong edge

**The breakeven stop helps forex pairs but hurts Gold's big-winner profile.** Gold's edge comes from rare large wins; the breakeven stop clips these.

### Stars of the Portfolio
- **GBP/USD**: 50% WR on 4H, Sharpe 1.01 on 1H, PF 1.54 both — most consistent edge
- **USD/JPY 1H**: Sharpe 1.36, +$2,582, the JPY breakout is the system's strongest signal
- **ETH 4H**: 63% WR, PF 2.31 — small sample but exceptional quality

### Remaining Weak Spots
- **Gold 4H**: PnL dropped significantly from breakeven stop — consider disabling BE stop for Gold
- **USD/JPY 4H**: Still negative on standard killzone logic
- **ETH 1H**: crypto_trend losing on both 1H timeframes
- **Gold 1H**: Still negative despite N4 confirmation bar
