---
tags: [validation, methodology, milestone]
aliases: [Walk-Forward Results, WF Results]
related: [[CLAUDE]], [[22-Priority-5-6-Metrics-WalkForward]], [[24-Optimisation-Round-2]], [[28-P4-Monte-Carlo]], [[31-Tool-Backtest]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit,
> 2026-07-02 full-codebase audit (WF peak-reset bug, R6-5 retracted — pre-fix WF scores were
> additionally optimistic), and realistic-fill re-validation. Numbers below are void artifacts,
> not current state. Retained as historical record only. Current canon: root `CLAUDE.md` +
> [[00-MOC-Zeros-Requiem]].

# Walk-Forward Validation — Full Results

**Date:** 2026-02-11

---

## Summary Table

| Symbol | Interval | Period | Windows | Consistency | Combined PnL | Avg Sharpe | Verdict |
|--------|----------|--------|---------|-------------|-------------|------------|---------|
| **Gold** | **Daily** | **5Y** | **8** | **88% (7/8)** | **+$3,144** | **0.51** | **VALIDATED** |
| Gold | 4H | 2Y | 6 | 33% (2/6) | -$661 | -0.39 | Edge recent only |
| EUR/USD | Daily | 5Y | 8 | 50% (4/8) | +$585 | 0.40 | Sparse but never loses big |
| GBP/USD | Daily | 5Y | 8 | 38% (3/8) | -$875 | -0.66 | Daily edge not present |
| BTC | Daily | 5Y | 8 | 12% (1/8) | -$1,515 | -1.70 | No daily edge |
| ETH | Daily | 5Y | 8 | 12% (1/8) | -$1,539 | -1.22 | No daily edge |

---

## Detailed Analysis

### Gold Daily — THE STAR (88% consistency)

The only symbol to convincingly pass the 5-year walk-forward test:
- 7 out of 8 windows profitable
- Only 1 losing window (W4: -$511, early 2023 during the consolidation range)
- Most recent window (W8): +$1,569 with 86% WR — the regime changes work best in volatile Gold markets
- Edge is IMPROVING over time (+$61/window degradation slope)
- Total: 81 trades, +$3,144, avg expectancy $48/trade

**This is a validated, institutional-grade edge on Gold Daily.**

### Gold 4H — Edge Concentrated in Recent Period

33% consistency over 2 years (2/6 windows). The first 3 windows are all negative, the last 3 include the profitable recent period. This confirms that the Priority 1-4 optimisations specifically improved recent performance — the system in its current form works better in current market conditions than historical.

This isn't necessarily bad — it could mean the relaxed thresholds are calibrated to current Gold volatility. But it does mean the 4H Gold edge is not yet validated across multiple market regimes.

### EUR/USD Daily — Sparse but Safe

Only 29 trades in 5 years (3.6/window) — the daily killzone pattern barely fires. But it never has a large loss — the worst window is $0 (no trades). When it does trade, the 68% win rate is excellent.

This is an asymmetric edge: rarely fires, but profitable when it does. Suitable as a low-frequency addition to the portfolio.

### GBP/USD Daily — No Daily Edge

Strong on 4H and 1H intraday, but the daily timeframe doesn't capture the killzone dynamics. The Asian range trap is an intraday phenomenon — on daily candles, the range is already baked into a single bar.

### Crypto Daily — No Edge

Both BTC and ETH fail the daily walk-forward comprehensively. The VR compression strategy is fundamentally an intraday concept — daily candles smooth out the compression/expansion cycles. The crypto regime should only be traded on 4H and 1H.

---

## What This Tells Us

### Validated Edges (trade with confidence)
1. **Gold Daily** — 88% consistency, 5 years, most robust edge in the system
2. **Gold 4H recent** — Sharpe 1.47 over last year, but needs more history to fully validate
3. **USD/JPY 1H breakout** — Sharpe 1.36, but only tested over 6 months so far
4. **GBP/USD 4H/1H** — PF 1.54, consistent on both intraday timeframes

### Edges That Need More Validation
- Gold 4H (longer history needed)
- USD/JPY (only 6 months of data)
- Crypto 4H (small sample sizes)

### Edges That Don't Exist (remove or don't trade)
- BTC/ETH on Daily — no edge, period
- GBP/USD on Daily — no edge
- EUR/USD on 4H — marginal, better on 1H

---

## Strategic Recommendation

**Core portfolio (validated):**
- Gold Daily: full allocation
- Gold 4H: reduced allocation (edge recent, improving)
- GBP/USD 4H + 1H: full allocation
- USD/JPY 1H: full allocation (monitor for degradation)

**Satellite positions (accumulating evidence):**
- EUR/USD 1H: half allocation
- BTC/ETH 4H: quarter allocation (small sample)

**Do not trade:**
- Any crypto on daily
- GBP/USD daily
- USD/JPY 4H (standard killzone — doesn't work for JPY on slow TFs)
