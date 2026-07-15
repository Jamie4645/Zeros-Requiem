# EXECUTIVE BRIEF — Fresh-Strategy Ultrareview (MPB / VTC)
**2026-07-04 | Council: arbiter-gold, arbiter-regime, arbiter-cost-skeptic, arbiter-risk, arbiter-falsifier, arbiter-socrates, arbiter-red-team**

## Verdicts

| Candidate | Verdict | Decisive evidence |
|---|---|---|
| **MPB** | **KILL** | N3 grid-avg PF **0.439** (kill <1.10), plateau **0/9** cells PF>1.0 (need ≥70%), mean R **-0.298/trade**, n=3,753 (N2 PASS). Structural — not a bad window: negative in every vol/trend/ADX bucket tested and 11/11 calendar years negative (2016–2026, post-hoc diagnostic, not pre-registered). |
| **VTC** | **KILL** | N3 grid-avg PF **0.409**, plateau **0/9**, mean R **-0.294/trade**, n=3,225 (N2 PASS). Same uniform-negative profile; sole positive year (+$9.8/144 trades, partial 2026) is a flat-$-cost-vs-3.7x-nominal-price artifact, not edge. |

Both candidates died at the pre-registered **N3** gate, ~2.5x below the kill line on PF and 0% vs required 70% on plateau. This is not borderline — no rescue path exists (session, direction, regime, or cost-model relaxation all checked and closed).

## What would change the verdict
Nothing plausible. The gap (PF 0.41–0.44 vs 1.10 required) is too large for any single fix to close:
- **Cost-skeptic's own zero-cost sweep**: even with cost stripped entirely, raw mechanism is only ~breakeven (PF 1.01 MPB / 0.99 VTC) — the tight 0.15–0.45%-of-entry SL band makes modeled cost ~27–29% of one R on every trade, but removing cost doesn't manufacture edge that isn't there.
- **Red-team's harness-defect fix** (below) moves MPB's mean R from -0.298 to ~-0.279 (estimated, not yet re-run) — nowhere near breakeven.
- Falsifiable next step, if anyone wants to close the loop rather than move on: patch `ztt_sim.simulate` to re-validate the SL-band against realized (not signal-time) fill price, re-run N2/N3, publish the corrected grid. This will not flip either KILL.

## Process defects found (fix before next candidate, don't block this verdict)
1. **Confirmed harness bug** (red-team, reproduced): MPB's SL-band sanity gate (0.15–0.45% of entry) is checked at signal time against nominal entry price, never re-checked against the realized post-fill price. One trade (2023-10-13→15, 49h weekend gap) filled with realized risk_dist collapsed to $0.046 (100x below floor), producing r=-73.91 and driving excess_kurtosis to **1037** — 148x the project's own leak-flag threshold (>7). No upstream seat (gold/regime/cost-skeptic/risk) surfaced this; it's in the JSON (`kurtosis_leak_flag: true`) but absent from the human-readable log. VTC shows no equivalent defect (kurtosis -1.2, flag false) — magnitude is too small to affect either verdict, but the defect is real and must be patched before a candidate closer to the N3 line relies on this engine.
2. **N7 gate is dead code**: KB-93 specifies three N7 kill legs (WR>70% OR PF>3.0 OR **WF Sharpe>3.0**); `gauntlet.py` only implements the first two — zero `grep` hits for Sharpe in N7. N7 also runs before N4 (walk-forward), so no WF Sharpe value exists yet even if coded. Moot this run (both died at N3, before N7 executes) but must be fixed before any future candidate that survives N3.
3. **Regime/calendar breakdowns are post-hoc, not pre-registered**: N4–N6 (walk-forward, block-bootstrap MC, permutation null) never ran — `gauntlet.py` returns immediately on N3 KILL. The per-vol/trend/ADX/calendar-year uniformity cited by arbiter-regime and arbiter-cost-skeptic is real and corroborating (independently spot-checked, matches JSON), but was computed after the outcome was known, with bucket boundaries chosen post-hoc. KB-93 scopes regime tags as "tag, never gate" (REG-1), so no pre-registration was owed — but it should be cited as supporting narrative, not evidence with N1-N8's weight.
4. **KB-93's rollover hard-gate** is documented but not wired into the gauntlet's `simulate()` call (cost-skeptic finding, non-blocking here).

## Pre-registration integrity: CLEAN
Git timestamps confirm KB-93 (007bee7) committed before the MPB/VTC code + harness (f0ec075), which predates both result artifacts. No post-hoc edits to KB-93, gauntlet.py, mpb.py, or vtc.py after commit. Grids, center cells, and all frozen mechanization constants match KB-93 text and JSON output exactly, cell-for-cell. No threshold was moved after seeing results.

## Open strategic question (arbiter-socrates, flagged RED, not adjudicated by any seat)
Three independent mechanization attempts sourced from books/discretionary trades (SBRS → ZTT → MPB/VTC) have now all collapsed below viability, each at a different but still-decisive gate. Whether "book/theory → frozen-grid mechanism" is itself a falsified discovery method for this user's edge — versus these being three unrelated bad candidates — is unmeasured and unanswered. This does not change today's KILL verdicts but should inform whether a candidate #4 is worth generating the same way.

## Non-negotiable
**Live size stays 0.00% regardless of any verdict above.** `src/live/deploy_gate.py::require_live_authorization()` still requires `ZR_LIVE_TRADING_ENABLE=I-UNDERSTAND-NO-VALIDATED-EDGE` and `sys.exit(3)`s otherwise — confirmed unchanged by this review. This gauntlet does not touch it.

---

Relevant files: `knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md`, `logs/fresh_strategy/gauntlet_mpb.json`, `logs/fresh_strategy/gauntlet_vtc.json`, `analysis/fresh_strategy/gauntlet.py` (lines 163-281, N3/N7 gate logic), `analysis/real_trades/ztt_sim.py` (SL-band/fill-timing defect), `src/regimes/mpb.py` (lines 188-189, SL_MIN_PCT/SL_MAX_PCT), `src/live/deploy_gate.py` (lines 17, 29, 38, 59).