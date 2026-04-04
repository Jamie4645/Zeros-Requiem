---
tags: [pipeline, strategy-cluster, breakout, retest]
aliases: [Breakout Cluster, Breakout Retest Cluster, False Breakout Filtering]
---

# Breakout + Retest / False Breakout Filtering Cluster

> **Confidence:** High | **Books:** 4/13 | **Traders:** 3+ | **Strategies:** 3

---

## Overview

This cluster focuses specifically on breakout strategies that incorporate retest confirmation or false breakout filtering — the closest published strategies to SBRS logic. Lien's "Filtering False Breakouts" requires a 20-day high/low break, followed by a 2-day reversal, then a re-break within 3 days — almost exactly the SBRS breakout-retest pattern. Her "Waiting for the Real Deal" exploits London session stop hunts followed by the real directional move. Kovner's congestion breakout waits for tight range compression then enters the breakout. All these strategies filter for quality breakouts rather than entering every channel break.

---

## Supporting Traders

| Trader | Book | System | Key Contribution |
|--------|------|--------|-----------------|
| Kathy Lien | [[Day Trading Currency Market 1st Ed - Book Analysis]] / [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]] | False Breakout Filter / London Open Fake-Out | 20-day break → 2-day reversal → re-break; session-based stop hunt filtering |
| Bruce Kovner | [[Market Wizards - Book Analysis]] | Congestion Breakout | Enter on breakout from tight consolidation; retest preferred; adds fundamental backdrop |
| Richard Dennis | [[Market Wizards - Book Analysis]] | Turtle Channel Breakout | 20/55-day channel breakouts — the pure breakout approach (no retest) |
| Paul Tudor Jones | [[Market Wizards - Book Analysis]] | Range Expansion | Breakouts from narrow ranges with volatility expansion confirmation |
| Victor Sperandeo | [[New Market Wizards - Book Analysis]] | Age of Trend Analysis | Measure trend duration; breakouts after typical correction lengths |
| Linda Raschke | [[New Market Wizards - Book Analysis]] | Swing Pattern Breakout | Short-term breakout + pullback entries; opening range breakouts |

---

## Strategy Files

| File | Source | Description |
|------|--------|-------------|
| `lien_london_breakout.py` | [[Day Trading Currency Market 1st Ed - Book Analysis]] | London session open breakout with fake-out filter |
| `lien_inside_day_breakout.py` | [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]] | Inside day compression → range expansion breakout |
| `lien_asian_range_breakout.py` | [[Day Trading Currency Market 1st Ed - Book Analysis]] | Asian session range breakout on London open |

---

## Core Rules Consensus

1. **Breakouts from consolidation are high-probability entries.** Kovner, Dennis, Jones, and Lien all target tight-range breakouts as optimal entry signals.
2. **Retests and re-breaks improve reliability.** Kovner explicitly prefers re-entry after initial breakout pullback. Lien's false breakout filter requires a reversal then re-break. Raschke's pullback entries align.
3. **False breakouts are tradeable signals.** Lien's "London Open Fake-Out" trades the real move after the initial stop hunt. Kovner and McKay use failed breakouts as counter-signals.
4. **Time matters — stale breakouts lose edge.** Sperandeo's age analysis, Raschke's time-limited setups, and Lien's 3-day re-break window all support expiring stale signals.
5. **Session context matters for breakout timing.** Lien documents that London open triggers breakouts (often with initial fake-outs as dealers hunt stops), while the US session provides follow-through.

---

## Key Differences

- **SBRS requires MA cross confirmation on top of breakout-retest; Lien and Kovner do not**
- **Lien uses fixed pip stops (20-30 pips); SBRS uses ATR-based stops**
- **Lien's time windows are very specific (3 days for reversal, 3 days for re-break); SBRS uses bar counts (10 bars max retest wait)**
- **Kovner adds fundamental backdrop as a directional filter; SBRS is pure technicals**
- **Lien's strategies are forex-specific; SBRS targets Gold**

---

## SBRS Relevance

> **Rating: VERY HIGH — Closest cluster to SBRS logic**

| Cluster Rule | SBRS Implementation | Alignment |
|-------------|---------------------|-----------|
| Breakout from consolidation | Swing high/low break (20-bar lookback) | Direct match |
| Retest improves reliability | Retest within 0.5 ATR of broken level | Direct match — Lien's "Filtering False Breakouts" is near-identical |
| Stale breakouts expire | MAX_RETEST_WAIT = 10 bars | Direct match — Lien uses 3-day window |
| Failed breakout as signal | Not implemented | Potential enhancement |
| Session context | Skip 16-20 GMT session filter | Partial match — Lien's session work supports this |
| MA confirmation on breakout | WMA(9) crosses SMMA(7) within 10 bars | SBRS adds this layer that Lien/Kovner lack |

**Assessment:** Lien's "Filtering False Breakouts" and "London Open Fake-Out" are the closest published strategies to SBRS. The breakout → retest → continuation framework is shared. SBRS adds the MA cross confirmation layer that these strategies lack, creating a higher-quality filter at the cost of fewer trades.

---

## Links

- [[Trend Following Cluster]] — Related: trend context for breakouts
- [[Moving Average Systems Cluster]] — Related: MA confirmation layer
- [[Volatility Breakout Cluster]] — Related: volatility compression → expansion
- [[Forex Session Strategies Cluster]] — Related: session timing of breakouts
- [[Day Trading Currency Market 1st Ed - Book Analysis]]
- [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]]
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Strategy Comparison Overview]] — All clusters
- [[Master Report]] — Full pipeline output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
