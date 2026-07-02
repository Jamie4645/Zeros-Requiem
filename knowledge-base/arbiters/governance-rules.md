# Arbiter Council — Governance Rules (Round 8+)

Created 2026-04-19 from the dual-council synthesis (Philosophical Council + Arbiter Council).
Owners: arbiter-canon-audit (U8), arbiter-falsifier (U9), arbiter-council (U10).

These rules are NOT optional. They override any individual arbiter's recommendation.

---

## U8 — Canon anti-drift ratchet

**Rule:** Every numeric claim in `CLAUDE.md` (and anywhere referenced as "canonical") must cite a dated log under `logs/round*/`. A claim is "fresh" for the round in which it was measured plus the next round; after that, it must be re-measured or demoted.

**Owner:** `arbiter-canon-audit` runs before every council session.

**Action on failure:**
- CRITICAL (unsupported claim): block all canon updates until claim is measured or removed.
- RED (>1 round stale): demand re-measurement this council.
- YELLOW (drifted 5%+ from measurement): demand reconciliation at next council.

**Anti-drift principle:** "If we can't cite it, we don't claim it. If we cite a log that was superseded, we re-cite."

---

## U9 — Time-boxed falsifier review

**Rule:** Every falsifier registered in `knowledge-base/75-Pre-Registered-Falsifier-R8.md` has a time-box. At the review date, it must be adjudicated PASS / FAIL / INSUFFICIENT-DATA. Undecided = treated as FAIL and triggers the associated action.

**Owner:** `arbiter-falsifier` runs at every council AND at each falsifier's review deadline.

**The 5 active Round 8 falsifiers and their review boxes:**

| # | Falsifier | Review-by | On FAIL |
|---|---|---|---|
| 1 | Mean realized slip ≤1.0pt (60d paper) | 60d post-paper-start | HALT, re-run council |
| 2 | Slip-sweep PF drop 0.75→1.00 <30% per instrument | Immediate (done R8) | DEMOTE tier |
| 3 | Portfolio t(4) MC base <5%, stress <10% | Every council | DEMOTE sizing 50% |
| 4 | Trade count ≥500 per strategy | Rolling | Keep 0.25% cap; <300 → 0.15% |
| 5 | Gold Long PF ≥1.5 AND Short PF ≥1.2 | Post direction/regime run | Drop Short stream |

**Amendment gate:** A falsifier threshold can only be changed with (a) user approval + (b) a KB entry explaining why + (c) the amendment is dated and versioned (new falsifier file for R9).

---

## U10 — External anchor requirement

**Rule:** No council convergence is accepted as canon unless the brief cites at least ONE external anchor. Anchors are:
- A measured log in `logs/round*/` (primary anchor)
- A git commit hash that closed a prior caveat
- A third-party data source (OANDA fetch timestamp, IBKR snapshot)

**Owner:** `arbiter-council` enforces this in every synthesis.

**Action on failure:** If a convergence has no external anchor, it is recorded as HYPOTHESIS (not canon) and queued to next-hypotheses.md for measurement next round.

**Rationale:** Prevents the council from recycling its own prior opinions as evidence ("we said so last round" ≠ evidence). Every canon update must be rooted in something the user can independently verify.

---

## Philosophical pillar

These three rules together implement the Round 8 dual-council verdict: **"The system can only trust what it has recently measured, what it has pre-committed to falsify, and what a third party can verify."**

Any future council seat, process change, or tier promotion proposal must pass all three gates before it is accepted as canon.
