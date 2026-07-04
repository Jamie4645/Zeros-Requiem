# 93 — Fresh Gold Strategy Candidates: MPB + VTC (pre-registration)

**Date:** 2026-07-04
**Status:** PRE-REGISTERED — this note was written and committed BEFORE any backtest of either
candidate ran. Thresholds below are frozen-by-rule; they may not be revised after seeing results
(only a documented amendment BEFORE the corresponding phase runs, per `arbiter-falsifier` protocol).
**Provenance:** 5-reader ideation workflow (Kaufman / Chan / user-docx / review-labels / kill-list),
run 2026-07-04, journal `wf_a8b012bf-196`. Triage criteria: grounded in a book AND in the user's
observed behavior; entry trigger independent of break-retest-of-a-horizontal-level; testable on
on-disk data; falsifiable; not on the do-not-re-propose list (KB 89–92).

---

## Why these two (and what was rejected)

Three independent readers converged on the **trend-pullback-to-dynamic-MA** family and the
**volatility-thrust continuation** family. Both use NO horizontal level, NO break, NO retest —
the specific geometry falsified in ZTT (PF ceiling ~1.10) stays dead.

Rejected at triage: Opening-Range-Breakout family (PARTIAL overlap — still a break-of-a-level;
adjacent to the falsified family and to the user's explicit false-breakout aversion); all fade /
mean-reversion candidates (counter-trend; weakest grounding in the user's behavior); round-number
fade (surface-similar to level-rejection geometry).

**The integrated-trap guard (Kaufman ch. 21, KB-92):** these are new BASE systems, not filters on
a losing base. Each is validated STANDALONE-FIRST (V3 vertical gate). The pyramid overlay the user
visibly uses (6 stacked shorts down the Jun-2026 run) is tested only as an A/B on TOP of a base
that has already passed N3 — never as a rescue for a failing base.

---

## Candidate 1 — MPB (MA Pullback-Bounce)

**One line:** In an established WMA(144) trend with efficient price movement, enter on a pullback
that touches SMMA(5) and is rejected by the next candle close; structural stop; %-capped TP.

**Mechanism (10m XAUUSD, all values frozen here):**
- Trend context: price on trend side of WMA(144) AND sign(WMA144[t] − WMA144[t−20]) matches trade
  direction. (WMA144/SMMA5 = the user's own two indicators, `document_text.txt` lines 8–9;
  20-bar slope window = frozen mechanization.)
- Efficiency gate: ER(10) > 0.30 (Kaufman ch. 1 noise/ER; same 0.30 already frozen as
  `MIN_EFFICIENCY` in `ZTTParams` — reused, not re-fit).
- Entry trigger: bar t touches/pierces SMMA(5) against the trend; bar t+1 CLOSES back on the trend
  side of SMMA(5). Setup entry_index = t+1; fill at open of t+2 via `ztt_sim` (honest next-bar-open
  fill, phantom-fill assert active).
- Stop: pullback swing extreme ± 0.10×ATR(14) buffer. REJECT setup if SL distance > 0.45% of entry
  (user's observed band, KB memory + ZTT_REVIEW_ANALYSIS) or < 0.15% (cost-realism floor).
- TP: 1.8 × SL distance (midpoint of user's accepted R:R 1.7–2.0), capped at 2.0% of entry (user's
  hard ceiling; "toooo wideeee" at 4–5%). Skip if cap forces R:R < 1.7.
- One position at a time; max hold 72 bars (12h) — timeout exit (frozen).

**Sources:** Kaufman 5e ch. 1 (ER) + ch. 17 (KAMA/adaptive trend); Chan ch. 6 p. 140 (pullback-in-
trend dual-lookback, "buy the dip inside an intact longer trend"); user's trades 2,4,5,6,9,10,19
(MA-relation cited as standalone confirmation); user geometry: SL 0.3–0.45%, TP 1–2%, R:R ≥ 1.7.

## Candidate 2 — VTC (Volatility-Thrust Continuation)

**One line:** A single decisive range-expansion bar closing in its outer 20%, aligned with the 1H
trend, continues; enter next bar; structural stop; %-capped TP.

**Mechanism (10m XAUUSD entries, 1H trend filter, all values frozen here):**
- Trend context (1H, resampled from 10m): close > SMA(20) and SMA(20) slope over last 5 1H-bars
  positive → long-bias only (mirror for short).
- Thrust trigger: (high−low) ≥ 1.5 × ATR(14,10m) AND CLV in outer 20% of its own range in the bias
  direction (CLV = (close−low)/(high−low) ≥ 0.80 long / ≤ 0.20 short). Kaufman ch. 14 event-shock
  + "Trading the Event Lag" close-location continuation; user's momentum-quality reads (review #8).
- Entry: setup at thrust bar; fill next-bar open via `ztt_sim`.
- Stop: most recent 3-bar swing extreme against position, hard-capped at 0.45% of entry; floor 0.15%.
- TP: 1.8 × SL distance, capped at 2.0% of entry. Skip if R:R < 1.7 after caps.
- Cooldown: no new entry within 6 bars of the previous entry (frozen; prevents thrust-cluster
  stacking in the base variant). Max hold 72 bars.

**Sources:** Kaufman 5e ch. 14 (VolRatio shock + CLV continuation) + ch. 3 (wide-ranging days);
Chan ch. 6 (time-series momentum: entry after the move has already happened); user: "never
predicts", separates momentum-present from structure-present (ZTT_REVIEW_ANALYSIS #8).

---

## Pre-registered parameter grids (NO other configs may be run)

Plateau-not-peak rule (V6): a candidate passes N3 only if ≥70% of its grid is PF > 1.0 AND the
reported headline is the grid AVERAGE, not the best cell.

- MPB grid (9 cells): ER_MIN ∈ {0.25, 0.30, 0.35} × RR_TARGET ∈ {1.7, 1.8, 2.0}. Everything else frozen.
- VTC grid (9 cells): THRUST_ATR ∈ {1.25, 1.5, 2.0} × CLV_BAND ∈ {0.75, 0.80, 0.85}. Everything else frozen.

## Pre-registered falsifiers (N1–N8, per candidate, in gauntlet order)

| ID | Gate | KILL condition (frozen) |
|---|---|---|
| **N1** | Phantom-fill assert | Any `ztt_sim` phantom-fill assertion trip → HALT, audit before anything else |
| **N2** | Sample sanity | 10Y trade count < 150 (untestable) or > 6,000 (cost-death frequency) |
| **N3** | Realistic-cost backtest | Grid-average PF < 1.10 at session-gated cost → KILL. Plateau: <70% of grid cells PF>1.0 → KILL. (PF ≥ 1.2 avg = strong pass) |
| **N4** | Walk-forward | 8 sequential windows, equity/peak carried across windows (post-R6-5-fix method). <5/8 profitable → KILL; ≥6/8 = pass |
| **N5** | Monte Carlo | Block-bootstrap (never IID) Prob(20% DD at 1% risk) ≥ 5% → KILL |
| **N6** | Permutation null | Net R ≤ 95th percentile of ≥1,000 time-shuffled same-count/same-duration entry placements → KILL |
| **N7** | Red-flag inversion | WR > 70% or PF > 3.0 or WF Sharpe > 3.0 → HALT + leakage investigation (not a pass) |
| **N8** | Buy-and-hold gate | If long-side PnL share > 70%: information ratio must exceed Gold buy-and-hold IR over the same 10Y, else the "edge" is beta → KILL long stream |

**Verdict space (council, Step 9):** PROMOTE-TO-SCREENER / SCREENER-ONLY / KILL.
**Regardless of verdict: live size stays 0.00% — `src/live/deploy_gate.py` invariant is untouchable.
Nothing here authorizes deployment.** Best case = a second screener lane beside ZTT for forward
labels under F8.

## Pyramid overlay A/B (only if base passes N3+N4)

Add 1 unit per new 10-bar extreme in trade direction while trend gate still true, max 3 adds,
per-unit stop trails to the add bar's swing. KILL overlay if risk-adjusted (Sortino) worse than base.

## Data + engine (frozen)

- `data/cache/oanda_gold_10y_10m.csv` (primary), `oanda_gold_10y_1h.csv` (VTC trend cross-check).
- Engine: `analysis/real_trades/ztt_sim.py::simulate` (one_position=True for portfolio runs,
  False for label-style runs), `src/regimes/ztt_costs.DEFAULT_COST`, `metrics.py` scoreboard
  (IR/Sortino/Calmar/Ulcer + PF), `ztt_regime.py` tags on every trade (REG-1: tag, never gate).
- New code additive-only: `src/regimes/mpb.py`, `src/regimes/vtc.py`, `analysis/fresh_strategy/*`,
  `tests/test_mpb_primitives.py`, `tests/test_vtc_primitives.py`. No edits to deploy gate, risk
  manager, or any SACRED parameter block.
