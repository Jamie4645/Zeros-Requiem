# ZTT Phase 3 — Per-Trade Replay Results (for council adjudication)

**Date:** 2026-06-09. **Spec:** `docs/ztt_spec.md` (FROZEN). **Falsifiers:** `knowledge-base/90-Pre-Registered-Falsifier-ZTT.md`.
**Harness:** `analysis/real_trades/phase3/replay.py`. **Data:** 10Y M10 Gold.

## Method
For each of the 25 real trades: run `generate_setups` over a 45-day-warmup window; anchor the
match by **entry PRICE** (timestamps drift — Phase 0 finding) within ±10d; pick the same-direction
algo setup whose entry price is closest to the user's fill. Score per Falsifier F1 (ENTRY/SKIP only,
never exits): `reproduced = same direction AND |Δentry| ≤ 0.3R AND |ΔSL| ≤ 0.3R`, R = |entry − SL|.

## Sanctioned changes used
- **Re-tune #1 (SL anchor)** — chart-confirmed by 4 independent agents: SL anchors to the last
  confirmed swing (lower-high shorts / higher-low longs) **preceding the break** ("the previous lower
  high before price broke the support"), not the local post-break extreme. 1 of 2 re-tunes used.
- **Harness fix (not a re-tune):** anchor matches by price within ±10d (corrects mis-dated Tr11/17/25).

## Results
| Metric | Arm A (continuation-only) | Arm B (cont + reversal) | F1 threshold |
|---|---|---|---|
| Setups SEEN (geometry) | **19/19** | **19/19** | kill if <60% (11) → PASS |
| Entry within 0.3R | 22/25 | 22/25 | — |
| Exact entry AND SL within 0.3R (wins) | **6/19** | **7/19** | ≥15 PASS · 12-14 ITERATE · <12 HALT |
| SL within 0.3R | ~9/25 | ~10/25 | — |
| Flagged mistakes correctly skipped | 3/4 (Tr12/14/22 ok; **Tr20 leaks**) | 3/4 | ≥4/5 |

## Diagnosis
- **The edge is mechanizable at the setup+entry level:** the algo identifies EVERY winning setup
  (19/19) and matches the entry price within 0.3R on 22/25. Level→break→retest→direction logic works.
- **The SOLE strict-F1 blocker is the STOP.** The user's stop is genuinely discretionary — they pick
  "the right" prior swing, sometimes the nearest lower-high, sometimes a more significant one further
  back. The chart-validated "swing-before-break" rule is *principled and directionally correct* but
  does not pin to ±0.3R (only ~9/25). Remaining entry misses: Tr17 (algo finds a different setup, +91),
  Tr25 (mis-dated; no algo setup near 5471), Tr11 (just over tol).
- **Tr20 leak:** trend classifier called a user-described downtrend "range", so the counter-trend block
  didn't fire. (Candidate for the 2nd re-tune: trend classification leniency.)

## THE QUESTION FOR THE COUNCIL
Strict F1 = 6–7/19 reproduced ⇒ formally **HALT**. BUT: geometry-floor (60%) is smashed (100% seen),
entries match 22/25, mistakes mostly skipped, and the only failure axis is the **discretionary stop** —
which Socrates' pre-registered "fidelity ≠ profitability" clause says is a *valid non-failure* outcome
(a faithful mechanization can have a principled stop and still be judged on Phase-4 profitability).

**Rule on:** Does this constitute "edge IS mechanizable → proceed to Phase 4 (profitability is the real
test)", OR a genuine HALT? Critically: is invoking the fidelity≠profitability clause here legitimate, or
is it goalpost-moving around a pre-registered falsifier? Is 1 remaining re-tune best spent on the trend
classifier (skip Tr20 cleanly) — or reserved? Do NOT rubber-stamp; the falsifiers exist to stop self-deception.
