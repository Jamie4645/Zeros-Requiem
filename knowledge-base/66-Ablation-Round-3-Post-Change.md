---
tags: [ablation, sbrs-v2, validation, round-3, canon]
aliases: [Round 3 Ablation, Post-Change Ablation, Ablation 2026-04-16]
related: [[62-Ablation-Round-2-Results]], [[63-FVG-Downshift-Change]], [[64-Risk-Manager-Gold-Cap-Fix]], [[49-MA-Convention-Discovery]], [[arbiters/shared-findings]]
date: 2026-04-16
---

# Ablation Round 3 — Post-Change Validation

> *"A finding that survives two rounds is canon. A single reversal is a hypothesis."*

Ran after applying: FVG 1.0→0.5, dead filters deleted, Gold DD cap → 20%, main.py default → sbrs_v2. Purpose: verify post-change code still holds Round 2's canon and surface any regressions.

**Data:** 10Y Gold (GC=F), OANDA, 59,085 1H bars (2016-04-18 → 2026-04-16)

## Results Table

| # | Variant | Trades | WR | PF | PnL | Sharpe | MaxDD | Δ vs Base |
|---|---------|-------:|---:|---:|-----:|------:|------:|----------:|
| 0 | **Baseline (full v2.0 post-change)** | **643** | **43.9%** | **1.88** | **$33,912.65** | **1.25** | **11.9%** | BASE |
| 1 | No FVG | 327 | 43.7% | 2.11 | $20,809.77 | 1.15 | 7.5% | **-38.6%** |
| 2 | No Liquidity Sweep | 460 | 42.6% | 1.22 | $6,348.12 | 0.44 | 17.0% | **-81.3%** |
| 3 | No FVG + No Liquidity | 162 | 39.5% | 1.13 | $1,339.18 | 0.18 | 17.6% | **-96.1%** |
| 4 | No MA Cross Score | 435 | 43.5% | 1.49 | $12,313.17 | 0.75 | 13.1% | -63.7% |
| 5 | MA Cross ONLY | 0 | — | inf | $0.00 | 0.00 | 0.0% | -100% |
| 6 | No Level Gate (0 touches) | 657 | 44.4% | 1.96 | $36,939.84 | 1.28 | 12.5% | +8.9% |
| 7 | No Counter-Trend | 561 | 43.0% | 1.41 | $13,968.36 | 0.76 | 13.7% | -58.8% |
| 8 | No Session Filter | 737 | 44.0% | 2.14 | $50,355.71 | 1.50 | 10.6% | **+48.5%** |
| 9 | No Squeeze Filter | 643 | 43.9% | 1.88 | $33,912.65 | 1.25 | 11.9% | 0.0% (dead) |
| 10 | No Whipsaw Detection | 643 | 43.9% | 1.88 | $33,912.65 | 1.25 | 11.9% | 0.0% (dead) |
| **11** | **Old MA Convention (SMMA>WMA=bull)** | **735** | **46.1%** | **5.23** | **$206,367.74** | **2.33** | **5.2%** | **+508.5% ⚠️** |
| 12 | Higher Threshold (1.5) | 246 | 42.3% | 1.88 | $12,165.99 | 0.88 | 10.4% | -64.1% |
| 13 | Kitchen Sink OFF | 0 | — | inf | $0.00 | 0.00 | 0.0% | -100% |
| 14 | Tight Retest (0.3 ATR all) | 575 | 44.0% | 1.85 | $28,981.73 | 1.17 | 11.3% | -14.5% |
| 15 | Wide Retest (0.8 ATR all) | 686 | 42.0% | 1.55 | $23,241.27 | 0.93 | 15.6% | -31.5% |
| 16 | No False Breakout Filter | 284 | 40.5% | 1.09 | $1,695.39 | 0.21 | 20.3% | **-95.0%** |
| 17 | No Chop Filter | 643 | 43.9% | 1.88 | $33,912.65 | 1.25 | 11.9% | 0.0% (dead) |

## Verdict — Components Re-Confirmed (Round 2 canon held)

| Component | Round 2 | Round 3 | Canon? |
|---|---|---|---|
| FVG (at weight 0.5) | downshifted 1.0→0.5 | -38.6% if removed | ✅ now net-positive at 0.5 |
| Liquidity Sweep | critical | -81.3% if removed | ✅ CRITICAL |
| False Breakout Filter | critical | -95.0% if removed | ✅ CRITICAL |
| Counter-Trend permission | needed | -58.8% if removed | ✅ needed |
| MA Cross scoring | valuable | -63.7% if removed | ✅ valuable |
| Squeeze / Chop / Whipsaw | 0.0% (dead) | 0.0% (dead, code deleted) | ✅ confirmed dead |
| Level Gate (2-touch min) | needed | +8.9% if removed | ⚠️ MILD — may be removable |

## Verdict — Two Round 2 Conclusions REVERSED

### 1. Session Filter: from dominant → reversed (+48.5%)

**Round 2 said:** Session filter -52% if removed — the dominant component.
**Round 3 says:** No Session Filter = +48.5% PnL ($50,355 vs $33,912).

**Probable cause:** Round 2 was on pre-FVG-downshift code. Session filter was masking FVG over-fire in 16-20 GMT. With FVG weight reduced, the session filter now BLOCKS good trades.

**Status:** Hypothesis, NOT canon. Requires walk-forward before acting.
**Owner:** arbiter-execution (session sub-hour hypothesis in queue is adjacent).

### 2. MA Convention: current "new" (WMA>SMMA=bull) DECIMATED by "old" (SMMA>WMA=bull)

**Round 1 claim (from [[49-MA-Convention-Discovery]]):** New convention produced +$3,300 vs old.
**Round 3 corrected-patch test:** OLD convention (SMMA>WMA=bull) produces **$206,367.74, PF 5.23, Sharpe 2.33** vs baseline $33,912.

**Reality check:**
- Reversal magnitude is +$172,455 — implausibly large without a test artefact
- PF 5.23 is WAY above the CLAUDE.md red-flag threshold of 3.0
- Sharpe 2.33 is also red-flag territory (CLAUDE.md says >3.0 walk-forward is suspicious; 2.33 on single backtest still warrants deep scrutiny)
- Max DD 5.2% with 735 trades and $280 expectancy-per-trade is too clean — either a major rediscovery OR a data-leak / patch-bug

**Possible explanations:**
1. **Data leak in the patched test** — the patch only replaces `check_ma_cross` but the rest of the strategy still uses the "new" convention internally. If partial inversion creates an asymmetric filter that removes losing trades specifically, this is a leak, not an edge.
2. **Genuine convention inversion on OANDA 10Y** — the original +$3,300 finding in [[49-MA-Convention-Discovery]] was on Yahoo 10Y. Data-source drift could explain a real reversal.
3. **Interaction with FVG downshift + session filter + false BO filter** — these Round 3 changes created a code state where the old convention re-dominates.

**Status:** HIGH-PRIORITY HYPOTHESIS. Do NOT revert the production MA convention based on this single ablation. Walk-forward on both conventions required before any code change.
**Owner:** arbiter-ablation (already has the MA-convention re-test hypothesis in queue) + arbiter-risk (red-flag investigation) + arbiter-data (source-drift hypothesis).

## Immediate Actions (do not bypass the charter)

1. Walk-forward the OLD convention on the same 10Y OANDA data — 8 windows, 75% threshold
2. Walk-forward the OLD convention on DAX, NASDAQ, GBP/USD — convention findings must generalize
3. Run ablation on just `[baseline, old_convention]` with DIFFERENT period seeds to check for overfit-to-2016-2026 regime
4. `arbiter-data` to check whether the +$172k result reproduces on Yahoo 10Y
5. If all three of {Gold WF, DAX WF, NASDAQ WF} confirm the reversal → bring to council for sacred-param change discussion (user approval required — this touches core SBRS identity)

## What's Stable (unchanged from Round 2)

- Session filter was validated in ROUND 2 but REVERSED in ROUND 3 — neither round is canon yet
- FVG at weight 0.5 is stable Round 3 canon
- Squeeze/chop/whipsaw remain dead (code deleted)
- Liquidity Sweep + False Breakout + MA Cross + Counter-Trend remain load-bearing

## Links

- [[62-Ablation-Round-2-Results]] — the findings Round 3 tests
- [[63-FVG-Downshift-Change]] — the code change between rounds
- [[64-Risk-Manager-Gold-Cap-Fix]] — the other code change between rounds
- [[49-MA-Convention-Discovery]] — the original MA-convention finding now in doubt
- [[arbiters/shared-findings]] — canonical finding log
- [[arbiters/next-hypotheses]] — open queue

## Raw log

`/tmp/post/ablation_post.log` — full run output (command exit 1 on final unicode print, but all 18 tests completed and captured in summary table above).
