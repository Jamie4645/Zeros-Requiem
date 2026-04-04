---
tags: [pipeline, strategy-cluster, risk-management, position-sizing]
aliases: [Risk Cluster, Risk Management Frameworks, Position Sizing]
---

# Risk Management / Position Sizing Frameworks Cluster

> **Confidence:** Very High | **Books:** 8/13 | **Traders:** 8+ | **Strategies:** 0 (frameworks, not entry systems)

---

## Overview

The single most agreed-upon principle across ALL 13 books: risk management determines survival. This cluster spans the most books of any cluster because every successful trader — regardless of strategy type — emphasizes risk management as the primary determinant of long-term success. Specific frameworks: Turtle N-system (2% risk per unit, ATR-based sizing, drawdown reduction rules), Chan's Kelly criterion (f = mean/variance, use half-Kelly), O'Neil's 7-8% hard stop, Trout's tiered limits (1.5% per trade, 4% per day, 10% per month), Hite's 1% max per trade across 60+ markets, Taleb's barbell (90% safe + 10% speculative), Dalio's 100+ uncorrelated streams.

---

## Supporting Traders

| Trader | Book | Framework | Key Contribution |
|--------|------|-----------|-----------------|
| Richard Dennis | [[Complete Turtle Trader - Book Analysis]] / [[Market Wizards - Book Analysis]] | Turtle N-System | 2% risk per unit, ATR-based sizing, 20% reduction per 10% drawdown |
| Larry Hite | [[Market Wizards - Book Analysis]] | 1% Max Risk | Never risk >1% per trade across 60+ diversified markets |
| Ernest Chan | [[Algorithmic Trading - Book Analysis]] | Kelly Criterion | f = mean/variance; use half-Kelly for safety; CPPI for drawdown protection |
| Monroe Trout | [[New Market Wizards - Book Analysis]] | Tiered Limits | 1.5% per trade, 4% per day, 10% per month — cascading safety net |
| William O'Neil | [[How to Make Money in Stocks - Book Analysis]] | 7-8% Hard Stop | Non-negotiable max loss per position; sell rules as important as buy rules |
| Nassim Taleb | [[Fooled by Randomness - Book Analysis]] | Barbell Strategy | 90% safe (bonds) + 10% speculative (OTM options); survive to exploit rare events |
| Ray Dalio | [[Hedge Fund Market Wizards - Book Analysis]] | 100+ Streams | Extreme diversification across uncorrelated return streams; Holy Grail of investing |
| Tom Basso | [[New Market Wizards - Book Analysis]] | Volatility Normalization | ATR-based position sizing for smooth equity curve across all markets |

---

## Strategy Files

No strategy `.py` files — risk management is a framework applied across all strategies, not an entry system. However, `trout_risk_rules.py` implements Trout's tiered risk limit framework.

| File | Source | Description |
|------|--------|-------------|
| `trout_risk_rules.py` | [[New Market Wizards - Book Analysis]] | Trout's tiered risk limits: per-trade, per-day, per-month caps |

---

## Core Frameworks

### 1. Turtle N-System (Dennis/Eckhardt)
- Risk = 2% per unit (up to 4 correlated units = 8% max)
- Position size = (2% of equity) / (ATR × dollar-per-point)
- Drawdown rule: reduce risk by 20% for every 10% portfolio drawdown
- Scale back in as equity recovers

### 2. Kelly Criterion (Chan/Thorp)
- Optimal leverage: f = mean return / variance of return
- Use half-Kelly in practice (full Kelly has too much variance)
- Requires stationary return distribution (unrealistic for most markets)
- CPPI (Constant Proportion Portfolio Insurance) provides drawdown protection floor

### 3. Tiered Limits (Trout)
- Per trade: 1.5% max risk
- Per day: 4% max drawdown → stop trading for the day
- Per month: 10% max drawdown → review and reduce size
- Creates cascading safety net

### 4. Simple Fixed Stop (O'Neil/Hite)
- O'Neil: sell at 7-8% loss, no exceptions
- Hite: 1% risk per trade, maximum diversification
- Simplicity is the feature — no optimization required

### 5. Barbell (Taleb)
- 90% in ultra-safe assets (short-term government bonds)
- 10% in highly speculative, asymmetric bets (OTM options, venture)
- Survives black swans while profiting from them
- Portfolio-level risk management, not trade-level

### 6. Holy Grail (Dalio)
- 100+ uncorrelated return streams
- Each stream has positive expected value
- Diversification reduces portfolio volatility dramatically
- Requires massive infrastructure but is mathematically optimal

---

## Consensus Rules (across all 8 traders)

1. **Never risk more than 1-2% per trade.** Dennis (2%), Hite (1%), Trout (1.5%), Chan (half-Kelly ≈ 1-3%), O'Neil (7-8% stop ≈ 1-2% position-adjusted).
2. **Reduce exposure during drawdowns.** Dennis (20% per 10% DD), Jones, Schwartz, Marcus, Trout — all reduce size when losing.
3. **Diversify across uncorrelated markets/strategies.** Hite (60+ markets), Dalio (100+ streams), Parker (30-65 markets), Basso (multi-market).
4. **ATR/volatility-based sizing beats fixed-lot sizing.** Turtle N-system, Basso, Chan all adjust for current volatility.
5. **Half-Kelly or less for leverage.** Chan, Taleb, and Thorp all advocate conservative leverage below mathematical optimum.

---

## SBRS Relevance

> **Rating: CRITICAL — Foundation of SBRS risk approach**

| Framework | SBRS Implementation | Alignment |
|-----------|---------------------|-----------|
| 1-2% risk per trade | 1% per trade | Direct match |
| ATR-based sizing | ATR-based stop loss and position sizing | Direct match |
| Breakeven management | Move SL to entry + 0.1R at 1.5R profit | Aligned with loss-limiting philosophy |
| Drawdown reduction | Not yet implemented | **Gap — consider Turtle 20% reduction rule** |
| Tiered limits (daily/monthly) | Not yet implemented | **Gap — consider Trout's cascading limits** |
| Multi-strategy diversification | Gold only (indices in progress) | In progress |

**Assessment:** SBRS's risk management is well-aligned with the consensus across 8/13 books. The 1% per trade and ATR-based stops match the most widely endorsed framework. Two gaps exist: (1) drawdown-based position reduction (Turtle rule), and (2) tiered daily/monthly limits (Trout). Both are potential enhancements that don't require changing entry logic.

---

## Links

- [[Trend Following Cluster]] — Related: Turtle risk system
- [[Statistical Systems Cluster]] — Related: Kelly criterion
- [[Market Psychology Cluster]] — Related: discipline to follow risk rules
- [[Complete Turtle Trader - Book Analysis]]
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Hedge Fund Market Wizards - Book Analysis]]
- [[Algorithmic Trading - Book Analysis]]
- [[How to Make Money in Stocks - Book Analysis]]
- [[Fooled by Randomness - Book Analysis]]
- [[Trading in the Zone - Book Analysis]]
- [[Strategy Comparison Overview]] — All clusters
- [[Master Report]] — Full pipeline output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
