---
tags: [audit, ablation, entry, selectivity, confluence, teardown]
aliases: [Primary Edge Teardown, Confluence Anti-Predictive, Strip-Back Lead]
related: [[84-Realistic-Fill-No-Edge]], [[86-SBRS-3.0-Spec-And-Build]], [[48-Ablation-Study-Results]], [[49-MA-Convention-Discovery]], [[50-Smart-Money-Indicators]], [[51-Confluence-Scoring-System]], [[53-SBRS-2.1-Experiment]]
---

# 85 — Primary Edge Teardown (Entry, Selectivity, Trend, Strip-Back)

Once [[84-Realistic-Fill-No-Edge|the edge was shown to be a phantom artifact]], the
question became: does the *primary* breakout-retest have any real edge, and where
is it lost vs the user's methodology? Every dimension was tested on realistic
fills. **All failed. The single most important finding: the SBRS 2.0 "smart-money"
upgrades are net-NEGATIVE.**

## Hypothesis 1 — Entry timing (RULED OUT)
`tests/_audit_entry_mode_ab.py` — candle-close vs limit-at-retest (the
methodology's "limit orders only"). Gold 10Y realistic:
- close: 159 tr, PF 0.96, −$446
- **limit: 111 tr, PF 0.77, −$1,835 (worse)**
Entry *price* is not the gap. ([[53-SBRS-2.1-Experiment]]'s candle-close choice
was right.)

## Hypothesis 2 — Selectivity (RULED OUT; confluence is ANTI-predictive)
`tests/_audit_selectivity_sweep.py`, Gold 10Y realistic:

| Config | PF | PnL |
|---|---:|---:|
| Baseline | 0.96 | −$446 |
| Level 3+ touches | 0.89 | −$1,214 |
| **Confluence ≥1.5** | **0.53** | −$1,586 |
| **Confluence ≥2.0** | **0.16** | −$2,000 |
| No counter-trend | 0.98 | −$143 |
| No false-BO levels | 0.97 | −$320 |
| Tight retest 0.3 ATR | 0.90 | −$893 |

**More confluence → worse.** The confluence scoring ([[51-Confluence-Scoring-System]],
[[50-Smart-Money-Indicators]]) is negatively correlated with outcomes on realistic
fills. Tightening selectivity does not create an edge.

## Hypothesis 3 — Trend / retest fidelity (RULED OUT)
`causal_4h_trend_series` is correctly causal (no look-ahead; drops the incomplete
4H bar). The trend gate is not the bug. Tighter retest tolerance hurts.

## The strip-back lead (the only positive config)
Removing the 2.0 "upgrades" improves it monotonically:

| Gold config | PF | PnL |
|---|---:|---:|
| Baseline (full v2 machinery) | 0.96 | −$446 |
| No confluence requirement | 0.96 | −$383 |
| + no counter-trend | 0.99 | −$152 |
| **+ no false-BO (bare core)** | **1.07** | **+$1,431** |

**The bare with-trend breakout-retest on clean levels is the best version** — and
the only positive one (PF 1.07, Sharpe 0.16, DD 20.6%, 348 tr). Not elite, but a
direct vindication of CLAUDE.md's "codify, don't invent": the inventions
(confluence, counter-trend, false-BO, FVG/liquidity weighting) destroyed edge.

This PF 1.07 bare core became the baseline for [[86-SBRS-3.0-Spec-And-Build]].
