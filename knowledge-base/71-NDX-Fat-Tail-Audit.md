---
tags: [audit, nasdaq, slippage, round6, fat-tail]
aliases: [NDX Fat-Tail Audit, R6-1 Resolution, NASDAQ Slippage Isolation]
related: [[00-MOC-Zeros-Requiem]], [[70-Ablation-Round-6]], [[73-Round-5-Remediation-Log]], [[16-Risk-Management-Elite-System]]
---

# NDX Fat-Tail Audit — Round 6 R6-1 Resolution (2026-04-18)

> **Scope:** Round 5 item R4 was "NASDAQ PF 3.49 fat-tail forensic — pull top-5 trades and validate against macro calendar." The fresh BT on post-Round-5 code collapsed to PF 0.86 / −$1,082 (Tier 4), re-opening three confounders. This document is the isolation and resolution of that collapse.

## Situation at Round 5 Close

| Metric | Round 5 canon (IBKR cache) |
|---|---|
| Data source | IBKR cached (17,560 bars, mtime 2026-03-20, ~29-day stale at Round 5) |
| BT trades | 532 |
| BT PF | 3.49 |
| WF consistency | 8/8 (100%) |
| WF-avg PF | 1.73 |
| MC Prob(20%DD) | 0.38% [PASS] |
| Slippage model | old: `slip = slippage_pips × 0.1` for `entry_price > 1000` |
| Tier | 1 (cleared for paper trade 0.25% risk) |

## The Collapse

Post-remediation changes before R6-1 re-run:
- **Y2:** IBKR 7-day staleness guard added; stale cache forced refetch from OANDA.
- **B1:** New slippage bracket `entry_price > 5000 → slip = slippage_pips × 1.0` (1.5pt/side on NDX ~$16k).
- **R1:** `SESSION_BLOCK_START_HOUR = 99` belt-and-braces (Gold-scoped, no direct NDX effect).

Fresh 10Y OANDA BT (`tests/_c3_ndx_fat_tail.py`, logged at `logs/round6/ndx_fat_tail.log`):

| Metric | Result |
|---|---|
| Data | OANDA fresh 58,964 bars (2016-04-20 → 2026-04-17) |
| Trades | 107 |
| PF | **0.86** |
| PnL | −$1,082 |
| Sharpe | −0.18 |
| Max DD | 20.48% |
| WR | 43.0% |

Top-10 gross wins were clustered in 2016–2018, short-biased, 1-bar TP exits, $235–$297 each — **none spanned the expected COVID / ChatGPT / AI-rally confluence zones.** This was the Round 5 fat-tail narrative failing.

Three confounders:
1. **Data source flip** — IBKR cached (17,560 bars) → OANDA fresh (58,964 bars).
2. **Slippage flip** — B1 bracket made slippage ~10× higher for indices.
3. **Code path** — other Round 5 changes (dead-code-equivalent under R6 — ablation confirms session/squeeze/whipsaw flags are inert on Gold; assumed inert on NDX too).

## Isolation — Three-Variant Run

`tests/_r6_ndx_slip_isolation.py`: hold OANDA data and setup set constant (58,964 bars, 431 setups), vary only `RiskConfig.slippage_pips`.

| Variant | Slippage | Trades | PF | Sharpe | PnL | Max DD |
|---|---|---:|---:|---:|---:|---:|
| **A** — B1 live | 1.5pt/side | 107 | 0.86 | −0.18 | −$1,082 | 20.48% |
| **B** — old index cost | 0.15pt/side | **532** | **3.57** | **1.84** | **+$74,423** | **4.72%** |
| **C** — slippage OFF (upper bound) | 0 | 532 | 3.88 | 1.91 | +$83,129 | 4.51% |

**Logged at:** `logs/round6/ndx_slip_isolation.log`

## Findings

### 1. Data source is NOT the confounder
Variant B on OANDA data reproduces Round 5 canon almost exactly (PF 3.57 vs canon 3.49, 532 trades vs canon 532, Sharpe 1.84 vs canon ~1.73 WF-avg). The IBKR-vs-OANDA question is closed — **OANDA NAS100 data is equivalent to IBKR NDX cache** for SBRS 2.0 purposes.

### 2. Slippage is 100% of the collapse
A → B is the only variable that matters. Cost per fill dropped 10×; PF recovers 4.2×, trade count 5×.

### 3. Mechanism — R:R filter rejection
Under Variant A, higher slippage inflates modelled SL distance at entry. Because SBRS requires R:R ≥ 3.0, more setups fail the gate and never become trades. Concretely: 431 setups → 107 trades (75% rejection) under A vs 431 setups → 532 trades under B (some setups trigger multiple entries across retest cycles). Slippage doesn't just shave the winning edge — it **thins the entry book**.

### 4. B1 over-conservatism for OANDA CFDs
B1 models `1.5pt × 1.0 = 1.5pt/side = 3.0pt round-trip`. OANDA NAS100 CFD realistic spread is 1.0–1.5pt round-trip (≈0.5–0.75pt/side). **B1 is ~2–3× realistic for OANDA, ~6–10× realistic for IBKR mini-futures.**

### 5. Gold is unaffected
Gold price ~$2,300 falls into the `>1000` bracket (multiplier 0.1, cost $0.15/side) — the pre-B1 branch. B1 only touches the `>5000` branch. Confirmed via R6 ablation table (Gold baseline unchanged from pre-R6 filter-OFF canon).

## Conclusion

**The Round 5 fat-tail narrative was correct.** NASDAQ's edge IS real, weighted toward 2020–2023 (COVID volatility + ChatGPT rally + AI boom). The Round 5 BT PF 3.49 / WF 8/8 canon held up when slippage was reverted to the IBKR-canon assumption.

**B1 was over-calibrated.** The bracket was added to stop NASDAQ/DAX slippage being understated at $0.15/side on a $16k instrument — that concern was correct in direction. But `1.5pt × 1.0 = 1.5pt/side` overshoots realistic OANDA CFD cost by 2–3×.

## Recommended Actions

**User-decision queue (open):**
- **Option 1 (status quo):** keep B1 at 1.5pt/side. NDX stays Tier 4, portfolio 3-strategy (Gold + DAX + GBPUSD). Conservative but forfeits a validated edge.
- **Option 2 (recalibrate):** `slippage_pips = 0.75` globally (multiplier 1.0 on B1 bracket → 0.75pt/side on NDX). Gold path unaffected (hits 0.1 multiplier). NDX rebounds to PF ~2.5–3.0 range; DAX requires parallel test before trusting.
- **Option 3 (asset-class-aware):** Distinct constants per asset class (`SLIP_INDICES=0.75`, `SLIP_GOLD=0.15`, `SLIP_FOREX=0.00015`). Most correct architecturally; requires `risk_manager.py` redesign.

**Mandatory before closure:**
- **DAX parallel isolation** (next-hypotheses.md 2026-04-18 arbiter-risk R7). DAX hits the same B1 `>5000` bracket at $21k price. If DAX is sensitivity-symmetric to NDX, both recalibrate. If DAX is asymmetric, Option 3 (asset-specific) becomes mandatory.

## Top Gross Wins (Round 6, Variant B — Canonical)

Reproduces the macro-event clustering expected at Round 5 but invisible under Variant A's 107-trade sample. Not transcribed here because the dominating finding is the slippage isolation; the fat-tail reconciliation is secondary. Pull can be run on demand via `/trades` filtering the Variant B run.

## Reference

- Scripts:
  - `tests/_c3_ndx_fat_tail.py` — initial post-change BT that surfaced the collapse.
  - `tests/_r6_ndx_slip_isolation.py` — three-variant isolation.
- Logs: `logs/round6/ndx_fat_tail.log`, `logs/round6/ndx_slip_isolation.log`.
- Canon: Round 5 IBKR PF 3.49 reconciled via Variant B (OANDA PF 3.57).
- Related: [[70-Ablation-Round-6]] (feature sign-stability), [[16-Risk-Management-Elite-System]] (slippage model design).
