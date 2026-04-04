---
tags: [pipeline, strategy-cluster, momentum, growth]
aliases: [Momentum Cluster, Growth Momentum Systems, CANSLIM Cluster]
---

# Momentum / Growth Stock Systems Cluster

> **Confidence:** High | **Books:** 4/13 | **Traders:** 5 | **Strategies:** 2

---

## Overview

Growth momentum investing — buying stocks already making new highs with strong earnings acceleration — is a distinct edge from trend following in futures. O'Neil's CAN SLIM is the most complete growth stock momentum system: 7-factor screening (earnings, sales, relative strength, institutional ownership, market direction) + chart pattern breakouts (cup-with-handle, double bottom) on heavy volume. Driehaus runs a more aggressive version — buying on gap-up days with accelerating earnings. Minervini uses a refined screen with strict stage analysis. Ryan won the US Investing Championship 3 years running using refined CAN SLIM. All agree: buy strength, buy leaders, cut losses at 7-8%, and let winners run.

---

## Supporting Traders

| Trader | Book | System | Key Contribution |
|--------|------|--------|-----------------|
| William O'Neil | [[How to Make Money in Stocks - Book Analysis]] / [[Market Wizards - Book Analysis]] | CAN SLIM Growth Stock System | 7 codified criteria for stock selection; most mechanical growth system |
| David Ryan | [[Market Wizards - Book Analysis]] | Refined CAN SLIM | O'Neil protege; validated with 3 consecutive US Investing Championship wins |
| Richard Driehaus | [[New Market Wizards - Book Analysis]] | Aggressive Momentum | "Buy high, sell higher"; earnings acceleration + gap-up entries |
| Mark Minervini | [[Stock Market Wizards - Book Analysis]] | Stage Analysis + CAN SLIM | Refined screen with strict base/stage analysis; only 1st-2nd stage bases |
| Stuart Walton | [[Stock Market Wizards - Book Analysis]] | Growth Momentum | Catalyst-driven momentum with tight loss cutting |

---

## Strategy Files

| File | Source | Description |
|------|--------|-------------|
| `oneil_canslim_breakout.py` | [[How to Make Money in Stocks - Book Analysis]] | CAN SLIM cup-with-handle breakout system on heavy volume |
| `driehaus_momentum.py` | [[New Market Wizards - Book Analysis]] | Driehaus aggressive momentum: earnings acceleration + gap-up entries |

---

## Core Rules Consensus

1. **Buy strength, not weakness.** All five reject "buy low, sell high." Strong stocks get stronger. New highs are bullish signals, not overbought warnings.
2. **Earnings acceleration is the fundamental driver.** O'Neil and Driehaus both require accelerating quarterly earnings growth. Minervini adds revenue acceleration.
3. **Price must confirm fundamentals.** New price highs or breakouts from bases required before entry. No buying on value alone.
4. **Cut losses at 7-8%.** O'Neil's max loss rule is non-negotiable. Driehaus uses similar but slightly wider stops. Minervini uses 5-8%.
5. **Let winners run with trailing stops.** Hold as long as momentum persists. Sell on momentum deceleration, not price targets.
6. **Volume confirms breakouts.** O'Neil requires 50%+ above-average volume on breakout day. Driehaus wants institutional buying visible.

---

## Key Differences

- **O'Neil requires 7 factors aligned (very selective); Driehaus is more aggressive with fewer filters**
- **O'Neil waits for base pattern breakouts; Driehaus buys on gap-up days (more aggressive entry)**
- **O'Neil uses 7-8% hard stop; Driehaus has no fixed stop percentage**
- **Minervini adds tighter stage analysis (only 1st-2nd stage bases); O'Neil is more flexible on base count**
- **All are equity-only strategies — not directly applicable to Gold/Forex**

---

## SBRS Relevance

> **Rating: LOW for direct overlap, MEDIUM for principles**

| Cluster Rule | SBRS Implementation | Alignment |
|-------------|---------------------|-----------|
| Buy strength (momentum) | Breakout above swing high = momentum signal | Conceptual match |
| Cut losses fast | ATR-based stop loss | Aligned principle |
| Let winners run | 3R+ TP with breakeven management | Aligned principle |
| Price confirmation | Retest + MA cross confirmation | Aligned principle |
| Volume on breakouts | Not implemented (no volume in Gold CFD) | N/A for current markets |
| Breakout from base | Swing structure break after consolidation | Conceptual match |

**Assessment:** SBRS is not a momentum strategy per se, but shares the core philosophy: enter in the direction of strength, cut losers fast, ride winners. The breakout-from-base concept parallels SBRS swing high/low breaks. O'Neil's loss-cutting discipline (7-8% max) aligns with SBRS risk management. However, CAN SLIM's fundamental filters (earnings, institutional sponsorship) are equity-specific and have no SBRS equivalent.

---

## Links

- [[Trend Following Cluster]] — Related: momentum is trend following on shorter timeframes
- [[Breakout Systems Cluster]] — Related: breakout as momentum entry
- [[Time-Series Momentum Cluster]] — Related: momentum across asset classes
- [[How to Make Money in Stocks - Book Analysis]]
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Stock Market Wizards - Book Analysis]]
- [[Strategy Comparison Overview]] — All clusters
- [[Master Report]] — Full pipeline output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
