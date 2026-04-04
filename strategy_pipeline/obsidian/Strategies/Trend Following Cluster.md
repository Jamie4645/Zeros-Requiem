---
tags: [pipeline, strategy-cluster, trend-following]
aliases: [Trend Cluster, Trend Following Systems, Channel Breakout Systems]
---

# Trend Following / Channel Breakout Cluster

> **Confidence:** Very High | **Books:** 5/13 | **Traders:** 9 | **Strategies:** 3

---

## Overview

Trend following is the most universally endorsed strategy type across all 13 books analyzed. From Dennis/Eckhardt's Turtle system (20/55-day channel breakouts) to Seykota's EMA trend system, Hite's multi-market diversified approach, Basso's volatility-normalized trend system, and Parker's reduced-leverage adaptation — all share the same core thesis: buy strength, sell weakness, ride trends, cut losses. The Turtle system is the most codified version with exact entry/exit/sizing rules. Chan's time-series momentum strategies are the academic formalization of the same concept.

---

## Supporting Traders

| Trader | Book | System | Key Contribution |
|--------|------|--------|-----------------|
| Richard Dennis | [[Complete Turtle Trader - Book Analysis]] / [[Market Wizards - Book Analysis]] | Turtle Breakout (20/55-day channels) | Proved trend following can be taught; 2% risk per unit, 4 units max |
| William Eckhardt | [[Complete Turtle Trader - Book Analysis]] / [[Market Wizards - Book Analysis]] | Statistical trend following | Mathematical defense of trend following; never buy retracements |
| Ed Seykota | [[Market Wizards - Book Analysis]] | EMA crossover trend system | Pioneer of computerized trend following; 250,000% return over 16 years |
| Larry Hite | [[Market Wizards - Book Analysis]] | Diversified trend + strict risk | Never risk >1% per trade, diversify across 60+ markets |
| Jerry Parker | [[Complete Turtle Trader - Book Analysis]] | Chesapeake Capital adaptation | Reduced-leverage Turtle for institutional money; 30-65 markets |
| Tom Basso | [[New Market Wizards - Book Analysis]] | Volatility-normalized trend | ATR-based position sizing; smooth equity curve |
| Salem Abraham | [[Complete Turtle Trader - Book Analysis]] | Multi-market Turtle variant | Applied Turtle principles from rural Texas; decades of profitability |
| Liz Cheval | [[Complete Turtle Trader - Book Analysis]] | Original Turtle | One of the most successful original Turtles |
| Paul Rabar | [[Complete Turtle Trader - Book Analysis]] | Original Turtle | Long-term Turtle practitioner |

---

## Strategy Files

| File | Source | Description |
|------|--------|-------------|
| `turtle_breakout.py` | [[Complete Turtle Trader - Book Analysis]] | Turtle System 1: 20-day channel breakout with 10-day exit |
| `turtle_s2_55day.py` | [[Complete Turtle Trader - Book Analysis]] | Turtle System 2: 55-day channel breakout with 20-day exit |
| `ema_trend_following.py` | [[Market Wizards - Book Analysis]] | Seykota-inspired EMA crossover trend system |

---

## Core Rules Consensus

These rules appear across 3+ traders in the cluster:

1. **Follow the trend, never fight it.** All 9 traders agree: identify the prevailing direction and trade with it. Dennis: "The trend is your friend until the end."
2. **Use channel breakouts or MA crossovers as entry signals.** Dennis uses Donchian channels (20/55-day); Seykota uses EMA crossovers; Basso uses MA slope. All capture the same phenomenon.
3. **Cut losses fast, let winners run.** Universal rule. Dennis: "The worst thing you can do is miss a big move." A few huge winners pay for all losses.
4. **Risk no more than 1-2% per trade.** Hite: exactly 1%. Dennis: 2% per unit (up to 4 units = 8% correlated max). Basso: volatility-adjusted fraction.
5. **Normalize position sizing by volatility.** Basso and the Turtle N-system both use ATR to size positions. Higher volatility = smaller position.
6. **Diversify across uncorrelated markets.** Hite (60+ markets), Parker (30-65 markets), Dennis (multi-asset). Trend following works best with broad diversification.
7. **Reduce exposure during drawdowns.** Turtle rule: reduce position size by 20% for every 10% portfolio drawdown.

---

## Key Differences

- **Lookback periods vary widely:** 20-day Turtle vs 55-day Turtle S2 vs 250-day academic momentum
- **Breakout vs crossover entry:** Dennis uses channel breakouts; Seykota uses EMA crossovers
- **Concentration vs diversification:** Dennis allows 4 units per market (2% each = 8%); Hite caps at 1% per trade across 60+ markets
- **Leverage levels:** Dennis aggressive; Parker specifically reduced leverage for institutional capital
- **Retracement handling:** Eckhardt explicitly says never buy retracements; some implementations wait for pullbacks

---

## SBRS Relevance

> **Rating: HIGH**

| Cluster Rule | SBRS Implementation | Alignment |
|-------------|---------------------|-----------|
| Follow the trend | 4H trend context filter (WMA > SMMA) | Direct match |
| Channel breakout entry | Swing high/low break (20-bar lookback) | Direct match — analogous to Donchian channel |
| MA as trend signal | WMA(9) / SMMA(7) cross | Direct match — aligns with Seykota's EMA philosophy |
| Cut losses fast | ATR-based stop loss | Direct match |
| 1-2% risk per trade | 1% risk per trade | Direct match |
| Volatility normalization | ATR-based SL and retest tolerance | Direct match |
| Diversify across markets | Gold + Indices (in progress) | Partial match |
| Drawdown reduction | Not yet implemented | Gap — consider Turtle 20% reduction rule |

**Assessment:** SBRS is fundamentally a trend following system with breakout-retest entry timing. The channel breakout concept (new swing high/low) is directly analogous to Donchian channel breakouts. SBRS adds MA confirmation which aligns with Seykota's EMA philosophy. This cluster provides the strongest theoretical backing for the core SBRS approach.

---

## Links

- [[Breakout Retest Cluster]] — Related: breakout + retest entry filtering
- [[Moving Average Systems Cluster]] — Related: MA signal mechanics
- [[Time-Series Momentum Cluster]] — Related: academic formalization of trend following
- [[Risk Management Cluster]] — Related: position sizing frameworks
- [[Complete Turtle Trader - Book Analysis]]
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Hedge Fund Market Wizards - Book Analysis]]
- [[Algorithmic Trading - Book Analysis]]
- [[Strategy Comparison Overview]] — All clusters
- [[Master Report]] — Full pipeline output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
