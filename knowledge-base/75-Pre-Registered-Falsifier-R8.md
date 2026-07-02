# 75 — Pre-Registered Falsifier (Round 8)

**Status:** ACTIVE — committed 2026-04-19, BEFORE first paper-trade fill.
**Commitment basis:** Philosophical Council + Arbiter Council convergent mandate (Kahneman pre-registration, Musashi ±0.5pt threshold, Meadows balancing loop, Taleb barbell).
**Authority:** This document is the ex-ante falsification contract. Any attempt to amend it AFTER live data arrives is an admission of rationalization and must be flagged in the canon.

---

## Why this exists

The 2026-04-18 slippage recalibration (1.5pt → 0.75pt/side on index B1 bracket) is load-bearing for 3 of 5 Tier-1 verdicts:
- NDX: PF 0.86 → 2.63 (full reversal)
- DAX: WF 75% → 88% (borderline → elite)
- USDJPY: PF 1.27 → 3.18 (Tier 3 → Tier 2 promotion)

One unverified parameter is doing this much work. The 60–90 day paper-trade gate must not become a loop that rationalizes slip drift. This document locks the thresholds before the data arrives.

---

## Falsifier #1 — Realized Slip vs Modeled Slip (PRIMARY)

**Hypothesis under test:** The post-R7 assumption of 0.75pt/side slippage on indices holds in live OANDA CFD execution.

**Measurement:**
- For every fill on NDX, DAX (and DAX futures equivalent if applicable), compute `realized_slip = |actual_fill_price − backtest_expected_entry|` per side.
- Accumulate a rolling 100-fill average per instrument.

**Thresholds:**
| Band | Action |
|------|--------|
| rolling_mean_slip ≤ 1.0 pt/side | CONTINUE — model is conservative or accurate |
| 1.0 < rolling_mean_slip ≤ 1.25 pt/side | WARN — log but continue; escalate if 2 consecutive windows exceed |
| rolling_mean_slip > 1.25 pt/side | HALT — freeze new entries on that instrument. Re-run BT+WF+MC at empirical slip. Tier labels re-derived. |

**Evaluation window:** First 100 fills per instrument (expected ~30-45 days at paper volume).

**No retroactive amendment:** These bands are the contract. If realized slip is 1.3pt/side on fill #100, the answer is halt-and-recalibrate, not "let's see fill #150."

---

## Falsifier #2 — Slip-Sensitivity Sweep (PRE-PAPER)

**Blocking condition for paper-trade start:** Before first fill, run BT+WF+MC on NDX and DAX at slip_pips ∈ {0.50, 0.75, 1.00, 1.25}.

**Verdict thresholds:**
| Shape | Interpretation | Action |
|-------|----------------|--------|
| PLATEAU — PF variation <30% across range | Edge is robust to cost model | PROCEED with documented sizing |
| CLIFF — PF drops >50% between 0.75 and 1.00 | Edge is cost-model-contingent | REDUCE sizing to probes (0.10% non-Gold) per Taleb barbell |
| KNIFE-EDGE — cliff between 0.75 and 0.85 | Tier labels are fictional | HALT non-Gold paper entirely; run only Gold 0.5% |

---

## Falsifier #3 — Portfolio Student-t ν=4 MC (PRE-PAPER)

**Blocking condition for paper-trade start:** Run correlated Student-t ν=4 portfolio MC at documented sizing (Gold 0.5% + 4× 0.25% = 1.50% total) with empirical correlation matrix perturbed +0.2 (crisis stress).

**Verdict thresholds:**
| Prob(20% portfolio DD) | Action |
|------------------------|--------|
| < 5% base AND < 10% stressed | PASS — documented sizing is elite-compatible |
| 5–10% base OR 10–15% stressed | WARN — reduce non-Gold sizing to 0.15% each |
| ≥ 10% base OR ≥ 15% stressed | FAIL — reduce to probe sizing (Gold 0.5% + 4× 0.10%) |

---

## Falsifier #4 — USDJPY Trade Count

**Hypothesis under test:** USDJPY 161 trades (BT PF 3.18) represents real edge, not clustering artefact.

**Thresholds:**
- Until cumulative trade count (BT + paper) reaches 500, USDJPY remains capped at 0.25% via `SYMBOL_RISK_CAP['USDJPY']=0.0025`.
- At trade count ≥ 500, re-examine BT-vs-WF PF gap (3.18 vs 2.58). If gap closes to <0.3 and cumulative PF > 2.0, promote to Tier 1 at 0.25%. If gap persists, hold at Tier 2.
- If paper PF falls below 1.3 over any rolling 50-fill window on USDJPY, suspend pending review (consistent with the weakest trade-count floor).

---

## Falsifier #5 — Gold Per-Direction Integrity

**Hypothesis under test:** Gold long/short symmetry survives SBRS 2.0 confluence scoring.

**Thresholds (applied to Round 7 artefacts + paper fills combined):**
- Longs PF ≥ 1.5 AND Shorts PF ≥ 1.2 → symmetric enough; Gold 0.5% sizing justified.
- Shorts PF ∈ [1.0, 1.2) → asymmetric; size Gold at 0.3% and flag.
- Shorts PF < 1.0 → Gold is effectively long-only; reduce to 0.25% and rewrite strategy scope to long-only in CLAUDE.md.

---

## Governance

- **Amendment rule:** No threshold in this document may be moved AFTER live data begins arriving. If circumstances demand renegotiation, the amendment must be proposed BEFORE the relevant data is observed, timestamped, and logged in `knowledge-base/arbiters/shared-findings.md`.
- **Rationalization check:** Before accepting any "the threshold should have been X instead" argument, ask: *would I have agreed to X before seeing the data?* If no, the argument is motivated reasoning.
- **Canon update rule:** When any falsifier fires, CLAUDE.md must be updated in the same commit. The tier table is not allowed to drift from reality.

---

## What this document deliberately does NOT say

- It does not promise the strategies work. It says how we will know they don't.
- It does not promise 0.75pt/side is correct. It says 1.25pt/side is the line at which we admit it isn't.
- It does not promise a 10/10 portfolio score will exist at the end of paper. It says what would prevent us from awarding one.

---

*Committed 2026-04-19. No amendments permitted without timestamped justification before relevant data arrival.*
