---
tags: [ztt, falsifier, pre-registered, kill-switch, governance, active]
aliases: [ZTT Falsifiers, Kill Switches ZTT]
related: [[89-ZTT-Rebuild]], [[75-Pre-Registered-Falsifier-R8]], [[81-Audit-2026-06-01-Phantom-Fill]]
---

# 90 — Pre-Registered Falsifiers: ZTT

**Locked 2026-06-09, before any Phase 2 strategy code** (council pre-commitment gate).
These are the kill-switches that halt the build or block deployment if tripped. They
exist so Phase 3/4 cannot be quietly tuned to "pass". Source: arbiter-falsifier
plan-stage registration + dual-council mandates. See [[89-ZTT-Rebuild]], `docs/ztt_spec.md`.

## F1 — Phase 3 replay fidelity (MAKE-OR-BREAK)
"Reproduce" = same DIRECTION and entry within **0.3R** of the user's fill, located by
PRICE+STRUCTURE in a ±3-day window (timestamps drift). **Entry/skip ONLY — NOT exits**
(TP narration is hindsight-contaminated).
- ≥15 of 19 winning entries reproduced (≥79%) = **PASS**
- 12–14 = ITERATE (logic only; ≤2 threshold re-tunes total)
- <12 = **HALT** (do not build Phase 4)
- Must also correctly **SKIP ≥4/5 flagged mistakes** (Tr8, Tr12, Tr14-miss, Tr20, Tr22). Reproducing a flagged loss as a *win* = FAIL, not credit.
- **Geometry-only entry replay <60% = KILL immediately** (edge is non-mechanizable).

## F2 — Phantom-fill tripwire (every backtest fill)
- Assert `bar.low ≤ fill_price ≤ bar.high` on the fill bar AND the level was actually traded. **Any violation = HALT.**
- Win rate >80% OR any single setup-type >60% of total PnL = forced fill-log audit before proceeding. (This is the exact failure mode that voided SBRS — see [[81-Audit-2026-06-01-Phantom-Fill]].)

## F3 — Phase 4 realistic-cost gates (1Y M10, session-gated spread + slip)
- PASS: PF ≥1.5 AND Sharpe ≥1.0 AND expectancy >0 net of cost AND ≥80 trades.
- PF <1.3 OR negative net expectancy at realistic cost = **KILL**.
- Slip sweep {0.5, 1.0, 2.0 pt}: >50% PF drop across the range = COST-CLIFF → demote to probe.
- Cost-model check: flat-0.75pt vs session-gated PF must differ ≤0.10 (else session gate is load-bearing and must be measured before any live claim).

## F4 — Overfit tripwire
- Out-of-sample (data outside the 25-trade dates) PF ≥1.3.
- In-sample − OOS PF gap >0.7 = overfit → HALT.
- No mechanization threshold (touches, tolerances, lookbacks, windows) may be tuned more than **twice** against the 25 trades.

## F5 — Walk-forward / Monte Carlo
- WF (10Y M10) ≥75% windows profitable.
- MC t(4) Prob(20% DD) <5% base / <10% stress.

## F6 — Demo → live realized slip
- Rolling 50-fill mean |actual − expected fill| ≤0.9pt = CONTINUE; >1.2pt = HALT.
- Live blocked until ≥30 demo fills clear F6 AND F1–F5 all hold.

## F8 — The discretionary-selection premise itself (registered 2026-07-02)
> Source: 2026-07-02 blank-slate books review + dual-workflow audit. "The user IS the
> selection layer" was being treated as an axiom; Eckhardt/Dennis (Turtle experiment)
> prove even elite traders misjudge exactly this. F8 converts it to a falsifiable claim.
> Prior evidence FOR: label-permutation null on the 60 labels (2026-07-02,
> `logs/audit/label_permutation.log`) — take-subset +10.29R, p<0.0001 overall,
> p=0.0001 direction-stratified. Retrospective, single-regime; supportive, not proof.

- **Forward gate:** after **≥300 paired forward take/skip decisions** from the screener
  (`logs/ztt_screener/decisions.csv`, 27-col schema) spanning **≥1 up-month and ≥1
  range-month** for Gold: if user-take expectancy (R, at realistic session-gated cost)
  ≤ take-everything baseline over the same alerts → **the discretionary-edge premise is
  REFUTED and intraday Gold closes** (screener retired, effort moves off 10m Gold).
- **Self-consistency arm:** blind re-label ~30 of the original 60 setups (shuffled,
  future bars masked) ≥3 months after first labeling. Take/skip agreement <80% →
  the "irreducibly discretionary 73%" is partly noise; the 500-label plan is re-scoped.
- **Review date (hard):** first F8 review at **300 decisions or 2026-12-31, whichever
  comes first**. Zero labels/week is itself a decision — an empty decisions.csv at
  review date counts as an F8 process failure and forces a strategic re-plan.
- Thresholds frozen at registration; amendments require arbiter-falsifier review
  BEFORE any new data is seen.

---
**Most likely to trip: F1.** Mechanizing "respected level" + correct skips of the user's own
mistakes is the hardest single gate; the plan flags fidelity (R3) + overfit (R4) as primary risks.
A faithful mechanization that nonetheless fails F3 is a valid, honest outcome (fidelity ≠ profitability).
