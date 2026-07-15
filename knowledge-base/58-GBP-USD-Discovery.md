--
tags: [expansion, research, forex, discovery]
aliases: [GBP USD Discovery, Cable SBRS, Forex Expansion]
related: [[55-Multi-Asset-Expansion]], [[56-Risk-Manager-Calibration]]
date: 2026-04-05
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the GBP/USD PF/Sharpe/walk-forward figures below are void
> artifacts, not current state. Retained as historical record only. Current canon: root `CLAUDE.md`
> + [[00-MOC-Zeros-Requiem]].

# 58 — GBP/USD Discovery: Highest PF, Needs Walk-Forward Tuning

## The Surprise

GBP/USD produced the **highest single-backtest Profit Factor** of any asset tested:

| Metric | GBP/USD | Gold (reference) |
|--------|---------|-----------------|
| Profit Factor | **2.69** | 1.97 |
| Sharpe Ratio | **2.00** | 1.77 |
| Max Drawdown | **7.84%** | 9.17% |
| Total Trades | 1,323 | 2,252 |
| Avg Win | $513.67 | $338.57 |
| Avg Loss | $106.22 | $109.25 |
| Payoff Ratio | **4.84:1** | 3.10:1 |

**Why GBP/USD works well:**
- Strong directional trends (Brexit aftermath, BoE rate cycles, UK politics)
- Clean breakout-retest structure on 1H — textbook institutional order flow
- London/NY session filter (07-16 GMT) perfectly captures the liquid trading hours
- 2.5R minimum target (forex R:R) matches GBP's typical move amplitude

---

## Walk-Forward Results: 62% (5/8) — FAILS 75% Target

```
W1 2016-04→2017-07: $7,373  PF 1.77  ✅  ← Brexit aftermath, strong trends
W2 2017-07→2018-10: $2,288  PF 1.22  ✅
W3 2018-10→2020-01: $712    PF 1.08  ✅  ← Tight range, edge thinner
W4 2020-01→2021-04: -$1     PF 1.00  ❌  ← COVID chaos, breakeven
W5 2021-04→2022-07: $3,404  PF 1.31  ✅  ← Rate hike trends
W6 2022-07→2023-10: -$281   PF 0.98  ❌  ← Range-bound consolidation
W7 2023-10→2025-01: -$2,012 PF 0.59  ❌  ← SEVERE underperformance
W8 2025-01→2026-04: $1,810  PF 1.21  ✅  ← Recovery
```

**W7 is the problem window:** 65 trades, 21.5% WR, -$2,012. This was a period of low GBP volatility and unclear BoE direction. The strategy generated few setups (65 vs avg 151) and those it took had poor hit rates.

---

## Analysis: Why W7 Failed

Possible causes to investigate:
1. **Low volatility regime** — GBP/USD was in a tight 300-pip range (1.21-1.24) for much of this period
2. **Session filter too wide** — The 07-16 GMT window may capture too much dead zone in quiet periods
3. **Confluence threshold too low** — With-trend score of 1.0 may be too permissive for forex
4. **Retest tolerance** — 0.3 ATR may be too tight when ATR contracts in low-vol periods

---

## Next Steps

1. **Investigate W7 trades** — Pull individual trades, check what confluence signals fired
2. **Test tighter confluence** — Raise forex min score from 1.0 to 1.5 (require 2 boosters)
3. **Consider volatility filter** — Skip entries when 20-day ATR percentile < 25th
4. **Session refinement** — Test London-only (07-12 GMT) vs full London+NY (07-16)
5. **Re-run walk-forward** after tuning

**If W7 can be fixed:** GBP/USD becomes a Tier 1 asset with the best single-backtest metrics of any instrument.

---

## Current Status: Tier 2 — Promising

GBP/USD has clear edge (combined WF PnL: $13,293, positive in 5/8 windows) but doesn't meet the 75% consistency threshold. Needs targeted tuning, NOT parameter optimisation.

---

## Related

- [[55-Multi-Asset-Expansion]] — Full multi-asset results
- [[56-Risk-Manager-Calibration]] — Risk manager changes
- [[47-SBRS-2.0-Upgrade]] — SBRS 2.0 baseline

---

*Created: 2026-04-05 | Status: Under Investigation*
