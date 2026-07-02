---
tags: [books, strategy-review, ztt, synthesis, active]
aliases: [Books Blank Slate Review, Books Re-Read 2026-07]
related: [[89-ZTT-Rebuild]], [[90-Pre-Registered-Falsifier-ZTT]], [[91-Full-Codebase-Audit-2026-07]], [[87-Supervised-Rebuild]]
---

# 92 — Blank-Slate Strategy + Books Review (2026-07-02)

**Trigger:** user-requested fresh re-read of all 13 strategy books (from the full
extracted texts in `strategy_pipeline/output/*_text.txt` — the PDFs are deleted) plus a
blank-slate strategy review. 17-agent workflow; full synthesis in the session task output;
this note is the durable record.

## Verdict on the current path
**Screener + human selection + label collection: RIGHT ARCHITECTURE, FAILING EXECUTION.**
- The architecture is independently converged on by the strongest traders in the corpus
  (Thorp's blackjack decomposition; Schwager's finding that every high-return/low-risk
  wizard was discretionary or hybrid; Trout's ~half-of-returns-from-selection).
- The mechanical falsification (PF ceiling ~1.10 at 10m Gold cost) is the project's
  highest-confidence knowledge and was PREDICTED by the books (Eckhardt, Lescarbeau,
  Shaw: failing to reject efficiency is the modal outcome of honest research).
  **Stop re-litigating it.**
- But the loop validating the human half had run ZERO cycles: screener idle since
  ship-day 2026-06-14, 0/16 decisions filled, schema-corruption pending, files untracked.
  (All repaired 2026-07-02 — see [[91-Full-Codebase-Audit-2026-07]].)

## Permutation result (books-review action #2, EXECUTED 2026-07-02)
`analysis/real_trades/tv_review/label_permutation_null.py` → `logs/audit/label_permutation.log`
- Take-subset **+10.29R** vs overall null (any 30-of-60): mean −7.25R, p95 +0.70 →
  **p < 0.0001**.
- **Direction-stratified** null (short-bias/down-month removed): **p = 0.0001**.
  Within shorts: takes +11.00R vs all-shorts +0.37R. Within longs: takes −0.71R vs
  all-longs −14.83R (avoided the worst).
- Take-everything baseline: **−14.46R** (selection is the entire edge on this sample).
- Correction: **3/30 skips won**, not zero — canon's "zero skip wins" was wrong, and
  the corrected number *weakens* the hindsight-leakage red flag.
- **Status upgrade:** "the user IS the selection layer" moves from *narrative* to
  *statistically supported on retrospective single-regime data*. F8 forward test
  ([[90-Pre-Registered-Falsifier-ZTT]]) remains mandatory — retrospective labels
  cannot prove it.

## Book consensus (13/13 agree on this exact situation)
1. Generic geometry carries no edge; context/selection does. ~178 setups/mo is expected.
2. Costs kill short-holding-period strategies first; the remedy is NEVER "one more filter"
   — fewer/better trades, longer holds, or don't trade it.
3. Small samples cannot validate selection skill arithmetically (Chan critical values,
   Taleb, Woodriff). Derive the label target from n ≥ (2.326·σ/μ)² — don't folklore "500".
4. Discretion→rules runs through WRITTEN self-observation mined for predicates (Dennis,
   Cook, McKay, O'Neil). Bare take/skip flags are the weakest possible encoding —
   reason-codes + pre-registered target/invalidation at decision time.
5. Re-using labels to both discover and confirm filters is the cardinal sin. The
   false-bo+session finding stays a HYPOTHESIS until it survives labels collected after
   it was frozen.
6. 0.00% size while unvalidated is unanimously correct.

## Where the books conflict (open tensions, pre-registered not ignored)
- **Discretion real vs self-delusion:** Schwager corpus vs Eckhardt/Dennis (rules beat
  the rules' own creator). Resolution = F8 forward parallel-track, not assumption.
- **Capped vs uncapped winners:** F3 validated the 1.5% cap, but Turtles/Taleb warn the
  cap amputates the right tail that funds breakout trading. Pre-register a skew audit
  (partial-uncapped arm) before the cap hardens into sacred.
- **Timeframe:** the wall may be the move/cost ratio at 10m, not the idea — one cheap
  diagnostic pass of the same geometry at 1H/4H is book-endorsed (Covel/Trout/Eckhardt).
- **High-recall vs selectivity:** tier alerts A/B rather than suppressing; watch
  take-rate drift.

## Kill list (stop doing)
- Mining the existing 60 labels for more selection filters (OOS-contamination trap).
- Stating "the edge is discretionary" as established fact — correct status: mechanical
  edge falsified at high confidence; discretionary edge statistically supported
  retrospectively (p<0.0001), UNTESTED forward.
- Threshold changes outside version control (the 1.5%→2.0% cap drift; now reverted +
  everything committed).
- Treating the 13 old Book Analysis notes as canon — every fresh read found the same
  defect: strategy-extraction catalogs, several with fabricated content (the Natenberg
  note admits it never read the book; two Hedge Fund Market Wizards quotes don't exist;
  the Taleb note invented parameters). All 13 marked SUPERSEDED.
- "The 10Y auto-label will find the filter" hopes — it ran (n=8,426, AUC≈0.50 in every
  regime fold, permutation p=0.55). It is a null-baseline and feature-tagging substrate.

## Ranked actions (as of 2026-07-02)
1. ✅ DONE — repair + restart the label pipeline (schema migration, cap revert, git).
2. ✅ DONE — permutation null on the 60 labels (result above).
3. ⏳ Bar-replay retrospective labeling, future bars masked, starting with the prepared
   Jan–Feb up-trend batch (`tv_review/ztt_review_2026-01-01_to_2026-02-28_v2.csv`,
   87 setups) → target ~500 regime-balanced labels in 2–3 months, not 23.
4. ⏳ Reason-codes + pre-registered forecast per decision (conviction, frozen taxonomy,
   target/invalidation/horizon, regime stamp, news proximity) — the 27-col schema holds
   most of this; enforce 100% alert coverage.
5. ⏳ Two mechanical-side null baselines to close entry research permanently:
   random-entry ablation through the exact ZTT exit/cost stack, and a 1H/4H diagnostic
   pass of the geometry.
6. 📌 F8 registered with a hard review date ([[90-Pre-Registered-Falsifier-ZTT]]).

## New candidate FEATURES to log now, test only on fresh labels
Response-to-context/failure-to-follow-through (Marcus/Kovner/Hite), cross-market context
(DXY/real yields/silver — Ramsey), news-calendar proximity (Lien), stop-density/
round-number context (Chan/Osler: $xx00/$xx50 magnetism), level *obviousness inverse*
(Kovner: "the less observed, the better" — contradicts SBRS "more touches = better"),
time-stops (the most consistently endorsed untested exit: Dennis, PTJ, Cook, Saliba).
