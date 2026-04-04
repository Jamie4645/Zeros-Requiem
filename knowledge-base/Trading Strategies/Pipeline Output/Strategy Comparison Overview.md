# Strategy Comparison Overview

#trading #pipeline #overview

## What This Is

This is the central hub for all strategies extracted from trading books by the pipeline. It connects every [[Master Report|book analysis]], [[Pipeline Documentation|strategy cluster]], and consensus finding into a single reference point. Use this as your starting page when exploring extracted strategies and their relevance to SBRS.

---

## Quick Reference

| Cluster | Confidence | Traders | Books | Python File | SBRS Relevance |
|---------|-----------|---------|-------|-------------|----------------|
| [[Trend Following Cluster]] | Very High | 5 | Both | `turtle_breakout.py` + `ema_trend_following.py` | Direct alignment (WMA/SMMA cross, ATR stops) |
| [[Breakout Systems Cluster]] | High | 6 | Both | `turtle_breakout.py` | Core to SBRS (structure break detection) |
| [[Moving Average Systems Cluster]] | Very High | 5+ | Both | `schwartz_ma_pullback.py` | Validates SBRS MA confirmation step |
| [[Growth Momentum Cluster]] | Very High | 3 | Both | `driehaus_momentum.py` | Philosophy aligned (few big winners), equity-only |
| [[Statistical Systems Cluster]] | High | 2 | Book 2 | `trout_risk_rules.py` | Validates walk-forward methodology |
| Market Age/Reversal | High | 1 | Book 2 | `sperandeo_age_reversal.py` | Potential future filter for SBRS |
| Swing/Pattern Trading | High | 1 | Book 2 | (in Raschke analysis) | Time stop concept aligns with MAX_HOLD_BARS |
| Options Strategies | Medium | 3 | Book 1 | (not implemented) | Not applicable to SBRS |

---

## Books Analysed

| Book | Year | Traders | Strategies Extracted |
|------|------|---------|---------------------|
| [[Market Wizards - Book Analysis]] | 1989 | 16 | 8 |
| [[New Market Wizards - Book Analysis]] | 1992 | 17 | 10 |

**Total:** 33 traders interviewed, 18 strategies extracted across 8 clusters.

---

## Strategy Clusters (8 Total)

Strategies grouped by similarity across books. Higher overlap = higher confidence that a strategy concept is battle-tested.

### 1. [[Trend Following Cluster]] — Very High Confidence

- **Traders:** 5 across both books
- **Python:** `turtle_breakout.py` + `ema_trend_following.py`
- **SBRS Relevance:** Direct alignment — WMA/SMMA cross is a trend-following signal, ATR-based stops mirror classic trend-following risk management. This is the backbone of SBRS entry logic (Step 1: Trend Context, Step 4: MA Cross Confirmation).

### 2. [[Breakout Systems Cluster]] — High Confidence

- **Traders:** 6 across both books
- **Python:** `turtle_breakout.py`
- **SBRS Relevance:** Core to SBRS — structure break detection (Step 2) is a breakout signal. The Turtle system's channel breakout concept directly maps to SBRS swing high/low breaks. SBRS adds retest confirmation on top, which most pure breakout traders skip.

### 3. [[Moving Average Systems Cluster]] — Very High Confidence

- **Traders:** 5+ across both books
- **Python:** `schwartz_ma_pullback.py`
- **SBRS Relevance:** Validates the MA confirmation step — multiple Market Wizards rely on moving averages as their primary trend filter. SBRS uses WMA(9)/SMMA(7) cross as a required gate (Step 4), consistent with this cluster's findings that MAs are the most reliable indicator class.

### 4. [[Growth Momentum Cluster]] — Very High Confidence

- **Traders:** 3 across both books
- **Python:** `driehaus_momentum.py`
- **SBRS Relevance:** Philosophy aligned — Driehaus and similar traders prove that you can win with sub-50% win rates if your winners are significantly larger than your losers. SBRS targets 3R minimum, same principle. However, this cluster is equity-only and not directly applicable to Gold/Forex.

### 5. [[Statistical Systems Cluster]] — High Confidence

- **Traders:** 2 from Book 2
- **Python:** `trout_risk_rules.py`
- **SBRS Relevance:** Validates the walk-forward methodology and Monte Carlo testing approach. Trout's insistence on statistical validation over curve-fitting aligns with SBRS's 500-trade minimum and 75% walk-forward consistency requirement.

### 6. Market Age/Reversal — High Confidence

- **Traders:** 1 from Book 2
- **Python:** `sperandeo_age_reversal.py`
- **SBRS Relevance:** Sperandeo's trend age concept could serve as a future filter for SBRS — avoiding breakouts late in a trend's lifecycle. Not currently implemented but worth investigating as an additional filter (Step 5 candidate).

### 7. Swing/Pattern Trading — High Confidence

- **Traders:** 1 from Book 2
- **Python:** (in Raschke analysis)
- **SBRS Relevance:** The time stop concept (exit if trade hasn't worked within X bars) directly aligns with SBRS's MAX_HOLD_BARS = 40. Validates that holding losing trades indefinitely is a known edge-destroyer.

### 8. Options Strategies — Medium Confidence

- **Traders:** 3 from Book 1
- **Python:** (not implemented)
- **SBRS Relevance:** Not applicable. Options strategies require fundamentally different execution logic and are outside the scope of SBRS's breakout-retest approach on Gold and indices.

---

## Consensus Rules (7 Total)

Rules that multiple authors agree on — these are your safest bets. The more traders who independently arrived at the same conclusion, the higher the confidence.

| # | Rule | Supporters | SBRS Alignment |
|---|------|-----------|----------------|
| 1 | Risk 1-2% max per trade | 11 traders | 1% per trade ✅ |
| 2 | Cut losses fast | 13 traders | ATR-based stops ✅ |
| 3 | Let winners run | 9 traders | 3R targets ⚠️ (fixed TP may limit upside) |
| 4 | MAs are the reliable indicator | 6 traders | WMA/SMMA cross ✅ |
| 5 | RSI/stochastics/Fibonacci worthless | 2 traders | Not used ✅ |
| 6 | Mechanical > discretionary | 7 traders | Fully mechanical ✅ |
| 7 | Buy strength not weakness | 5 traders | Retest divergence ⚠️ (justified — see below) |

### SBRS Alignment Notes

**Rule 3 — Let winners run ⚠️:** SBRS uses a fixed 3R take profit, which guarantees a known expectancy but may leave money on the table in strong trends. The Market Wizards consensus suggests trailing stops instead. This is a deliberate SBRS design choice — fixed TP provides more consistent walk-forward results and simpler position management. Worth monitoring whether a trailing component would improve Sharpe without harming consistency.

**Rule 7 — Buy strength not weakness ⚠️:** Most Market Wizards advocate buying breakouts (strength). SBRS buys the retest after a breakout — technically buying a pullback into strength, not pure strength itself. This is justified by Gold's tendency to trap breakout entries with false breaks. The retest filter is what gives SBRS its edge on Gold specifically.

---

## Contradictions (3 Total)

Where the Market Wizards disagree with each other — and the design decisions SBRS made.

### 1. Breakout vs Retest Entry

- **Breakout camp:** Enter immediately on the break (Turtle traders, Eckhardt, Dennis). Captures the initial move, higher win rate on strong trends.
- **Retest camp:** Wait for price to return to the broken level (SBRS approach). Better risk:reward, tighter stops, fewer false signals.
- **SBRS decision:** Retest. Gold-specific edge — false breakouts on Gold are frequent, and the retest filter eliminates the majority of them. Validated over 10Y walk-forward.

### 2. Fundamentals vs Technicals

- **Fundamentals camp:** Druckenmiller, Rogers, Lipschutz. Use macro analysis to determine direction, technicals for timing.
- **Technicals camp:** Seykota, Dennis, Eckhardt. Price contains all information, fundamentals are noise.
- **SBRS decision:** Pure technicals. Required for algorithmic execution — fundamental analysis cannot be reliably codified. SBRS philosophy is to codify discretionary edge, and Jamie's discretionary edge is technical.

### 3. Fixed vs Mental Stops

- **Fixed stops camp:** Place hard stop orders in the market. Removes emotion, guarantees execution.
- **Mental stops camp:** Monitor price and exit manually. Avoids stop hunting, allows flexibility.
- **SBRS decision:** Fixed stops with ATR buffer. Algo requirement — there is no "mental" option for a mechanical system. The ATR buffer (0.3 ATR beyond structure) provides non-obvious placement that reduces stop hunting impact.

---

## SBRS Validation Summary

Based on the analysis of 33 Market Wizards across 2 books:

- **5 of 7** consensus rules fully aligned with SBRS ✅
- **2 of 7** have justified divergences (fixed TP, retest entry) ⚠️
- **3 of 8** strategy clusters directly validate SBRS components (Trend Following, Breakout, MA Systems)
- **1 of 8** validates SBRS methodology (Statistical Systems / walk-forward)
- **All 3** contradictions have documented SBRS design decisions with rationale

**Conclusion:** SBRS is well-aligned with the consensus wisdom of elite traders. The two divergences (fixed TP and retest entry) are deliberate, Gold-specific design choices with walk-forward evidence supporting them.

---

## Related Project Notes

- [[00-MOC-Zeros-Requiem]] — Main project map of content
- [[19-Priority-1-Signal-Generation]] — SBRS signal generation context
- [[CLAUDE]] — Master strategy specification and sacred parameters

---

## Links

- [[Pipeline Documentation]] — How the extraction pipeline works
- [[Master Report]] — Full cross-book analysis output
- [[Market Wizards - Book Analysis]] — Book 1 detailed analysis
- [[New Market Wizards - Book Analysis]] — Book 2 detailed analysis
- [[Trend Following Cluster]] — Cluster detail
- [[Breakout Systems Cluster]] — Cluster detail
- [[Moving Average Systems Cluster]] — Cluster detail
- [[Growth Momentum Cluster]] — Cluster detail
- [[Statistical Systems Cluster]] — Cluster detail
