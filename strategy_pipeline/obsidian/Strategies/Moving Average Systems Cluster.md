---
tags: [pipeline, strategy-cluster, moving-averages]
aliases: [MA Cluster, Moving Average Systems]
---

# Moving Average Systems Cluster

> **Confidence:** Very High | **Books:** 4/13 | **Traders:** 5 | **Strategies:** 2

---

## Overview

Moving averages are the single most agreed-upon useful indicator across all Market Wizards interviews and Lien's forex books. While no two traders use identical MA configurations, the consensus is clear: MA crossovers and price-relative-to-MA signals provide a reliable, objective trend filter. Schwartz uses 10-day EMA pullbacks for entry. Seykota uses EMA crossovers for trend detection. Eckhardt states MAs "work if you add risk management" while dismissing RSI/stochastics/Fibonacci. Lien's Perfect Order strategy (10>20>50>100>200 SMA alignment) is the most complex MA-based system. All agree: MA cross direction = trend direction.

---

## Supporting Traders

| Trader | Book | MA Usage | Key Detail |
|--------|------|----------|-----------|
| Marty Schwartz | [[Market Wizards - Book Analysis]] | 10-day EMA pullback | Primary entry/exit signal; "the 10-day MA is the single best tool" |
| Ed Seykota | [[Market Wizards - Book Analysis]] | EMA crossover system | Multiple EMA periods for trend and timing |
| William Eckhardt | [[New Market Wizards - Book Analysis]] | MA systems as core | Defends MA systems mathematically; warns against curve-fitting periods |
| Monroe Trout | [[New Market Wizards - Book Analysis]] | MA as filter | MAs useful but warns against placing stops at obvious MA levels |
| Kathy Lien | [[Day Trading Currency Market 1st Ed - Book Analysis]] / [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]] | Perfect Order (10>20>50>100>200 SMA) | Higher-timeframe MA alignment for trend confirmation |
| Larry Hite | [[Market Wizards - Book Analysis]] | MA as trend filter | Long only above MA, short only below |
| Thomas Basso | [[New Market Wizards - Book Analysis]] | MA slope as trend | Trend direction defined by MA slope, not crossover |
| Linda Raschke | [[New Market Wizards - Book Analysis]] | Short-term MA for swing | Uses faster MAs for swing entry timing |

---

## Strategy Files

| File | Source | Description |
|------|--------|-------------|
| `ema_trend_following.py` | [[Market Wizards - Book Analysis]] | Seykota-inspired EMA crossover trend system |
| `schwartz_ma_pullback.py` | [[Market Wizards - Book Analysis]] | Schwartz 10-day EMA pullback entry in trend |

---

## Core Rules Consensus

1. **MAs work as trend filters.** All traders agree: being on the right side of the MA is the baseline requirement.
2. **MA crossovers generate reliable (if slow) signals.** Schwartz, Seykota, Eckhardt, and Lien all use crossovers. The trade-off is lag vs. reliability.
3. **Shorter MAs = more signals, more whipsaws.** Schwartz (10-day) gets many signals. Hite (longer) gets fewer but higher quality.
4. **Don't over-optimize MA periods.** Eckhardt specifically warns that optimizing MA lengths leads to curve-fitting. The edge is in the concept, not the exact period.
5. **Confirm MA signals with other filters.** No trader uses MAs alone — all combine with risk management, trend context, or breakout confirmation.
6. **Higher timeframe MA alignment improves direction.** Lien's Perfect Order requires 5 MAs aligned across timeframes. SBRS uses 4H WMA for trend context.

---

## Key Differences

- **Schwartz buys pullbacks TO the MA (mean reversion within trend); Eckhardt explicitly says don't buy retracements**
- **Seykota uses exponential MAs; Lien uses simple MAs; SBRS uses weighted and smoothed MAs**
- **Period lengths vary widely:** Schwartz (10/20 EMA), Seykota (proprietary ~10/30), Lien (10/20/50/100/200 SMA)
- **Trout notes MAs are useful but warns against placing stops at obvious MA levels**
- **Basso defines trend by MA slope rather than crossover — a subtly different approach**

---

## SBRS Relevance

> **Rating: CRITICAL — Core SBRS signal mechanism**

| Cluster Rule | SBRS Implementation | Alignment |
|-------------|---------------------|-----------|
| MA as trend filter | WMA(9) above/below SMMA(7) on 4H | Direct match |
| MA crossover signal | WMA(9) crosses SMMA(7) within 10 bars | Direct match |
| Don't over-optimize periods | Sacred parameters: WMA=9, SMMA=7 (from discretionary) | Direct match |
| Combine with other filters | Breakout + retest + trend context + session | Direct match |
| Confirm on candle close | SBRS waits for candle close on MA cross | Direct match |
| Higher TF alignment | 4H trend context check before 1H entry | Direct match — mirrors Lien's Perfect Order concept |

**Assessment:** SBRS's MA implementation is strongly supported by this cluster. The use of WMA/SMMA rather than simple EMAs is a deliberate choice from discretionary experience, which Eckhardt would endorse — the specific MA type matters less than consistent application. Lien's Perfect Order work validates the multi-timeframe MA alignment that SBRS uses.

---

## Links

- [[Trend Following Cluster]] — Related: MAs as trend tool
- [[Breakout Systems Cluster]] — Related: MA as breakout confirmation
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Day Trading Currency Market 1st Ed - Book Analysis]]
- [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]]
- [[Strategy Comparison Overview]] — All clusters
- [[Master Report]] — Full pipeline output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
