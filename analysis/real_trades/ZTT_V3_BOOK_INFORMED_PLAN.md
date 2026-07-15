# ZTT v3 — Book-Informed Improvement Plan

**Date:** 2026-06-14
**Inputs:** Two new "trading bibles" added to `strategy_pipeline/books/`:
1. **Ernest P. Chan — *Algorithmic Trading: Winning Strategies and Their Rationale*** (2013)
2. **Perry J. Kaufman — *Trading Systems and Methods*, 5th ed.** (2013)

**Method:** Both books were extracted to `analysis/book_extracts/` and decoded by a 27-agent
multi-council workflow — **15 readers** (full chapter coverage of both books) → **264 principles**
→ **6 theme-correlators** → **35 proposals** → **6 adversarial council seats** (red-team, falsifier,
cost-skeptic, gold, regime, socrates) → **210 verdicts**. Full record:
`tasks/wxj25a2xk.output` (562 KB JSON), survivor digest in this conversation's tool-results.

**Hard constraint (unchanged):** keep the core — **price action, 10-minute timeframe, break-&-retest of
a respected level.** This plan *improves* selection discipline, exits, regime-handling, and validation.
It does **not** invent a new strategy and does **not** touch the sacred geometry.

---

## 0. The headline the books delivered

> **ZTT's wall is a measurement & sample-size problem, not a missing filter.**

This is the single most important finding, and it is *convergent* across both authors and all six
council seats. The evidence:

- **The council demoted every "add another selection filter" proposal.** SEL-2 (Efficiency-Ratio gate),
  SEL-3 (round-number/MTF level-confluence), SEL-5 (range-contraction), VOL-1 (noise-floor break),
  VOL-4 (low-vol filter) all scored **6–7 of 12** (mostly "modify", several "kill"). EX-4
  (volatility-spike re-entry) was **killed outright (−2)**. The reason, stated by Kaufman directly
  (the *"integrated trap"*, ch. 21): *a filter can look profitable only because the base system loses
  on its own* — which is **exactly ZTT's situation** (raw geometry PF ~0.90). Another filter on a
  losing base is curve-fitting one regime.
- **The council unanimously elevated the discipline layer.** Nine proposals scored a perfect
  **12/12 (6 keeps, 0 kills)** — all of them are *measurement, regime-instrumentation, or
  label-corpus* work, **none** of them change the entry logic.
- Chan (ch. 1) + Kaufman (ch. 21–22): the failure mode that *already voided SBRS canon* (the phantom-fill
  artifact) is the same failure mode that makes any "PF improvement" untrustworthy. Fix the scoreboard
  **first**, then nothing downstream can launder a phantom edge.
- Kaufman (ch. 16, Day Trading): **over-selection is free intraday.** At ~250+ setups/yr you can reject
  95%+ and still never miss the day's one clean break-retest. The ~6-of-178/mo (~3%) take rate is
  *normal selectivity*, not a discrimination failure — which means **balanced AUC≥0.65 was the wrong
  yardstick.** The right one is **precision at a fixed ~3% take-rate** + **net-R vs a permutation null**.

**Implication for the autonomy question (the binding question, per Socrates):** the path to autonomy is
**not** a cleverer filter. It is **(a)** an honest, leakage-proof scoreboard, **(b)** a regime-balanced
label corpus at ~500 scale, and **(c)** auto-labeling the 10Y history for *outcome* features. Until those
exist, **screener + human-in-the-loop is the correct, book-endorsed design — not a concession.**

---

## 1. What survived the council (ranked)

| Score | ID | Theme | One-line |
|---|---|---|---|
| **12** | V9 | validation | Headline metric: PF → **information ratio + Calmar/Sortino/Ulcer**, gated vs **Gold buy-&-hold** |
| **12** | V7 | validation | **One-codebase backtest=screener** path: next-bar fills, phantom-fill assert, outlier scrub, model "unables" |
| **12** | V6 | validation | **Plateau-not-peak** geometric robustness for every tunable (incl. the 1.5% TP cap) |
| **12** | V5 | validation | Pre-register the **time-ordered single-shot OOS** protocol + conditional-entropy / χ² / t gates for the 500-label model |
| **12** | V3 | validation | **Vertical (standalone-first)** %-of-profitable-configs gate; cap autonomous layer at ≤4 features |
| **12** | REG-1 | regime | **Tag every decision + setup** with trend-dir / ER / ADX / vol-bucket (tag only, no gate) |
| **12** | REG-2 | regime | **Regime-stratified, time-ordered CV** as the gate for *any* future autonomous filter (every fold, not pooled) |
| **12** | EX-5 | exits | Honest exit eval: info-ratio/Sortino/Calmar + R-distribution + **cap-MFE audit** (test fat-tail amputation) |
| **12** | SIZE-6 | sizing | **Enrich `decisions.csv`** with ATR/vol/regime/realized-R/MFE/MAE so future labels can validate anything |
| 11 | V8 | validation | Regime drift monitors + the **symmetry test** (re-run any down-month long finding on up-trend data) |
| 11 | V2 | validation | **Trade-shuffle permutation null** (block bootstrap): does +8.72R beat random placement in Gold? |
| 11 | SIZE-5 | sizing | **Fat-tailed Kelly as a CEILING** (¼-Kelly ∩ 5% ∩ 6–8% vol-target), dormant until edge validated |
| 11 | SEL-4 | selection | **Auto-label the 10Y** by outcome → mine features with large-N, regime-balanced CV (the real unlock) |
| 11 | SEL-1 | selection | Reframe selection as **precision-at-3%-take-rate**, retire balanced-AUC as the bar |
| 10 | SIZE-4 | sizing | Forward exposure cap + **Prob(DD)/loss-run kill-switch** (pre-registered, t(4)-MC primary) |
| 10 | EX-3 | exits | **Measured time-stop**: derive N_TIMESTOP from the 10Y +1R-hit-time / half-life, frozen before A/B |

**Council-flagged duplicates to collapse into one build each:**
- Auto-label harness: **SEL-4 ≡ REG-4 ≡ V1** → build **once**.
- Regime monitors: **V8 ≡ REG-1 + REG-2 + REG-5** → implement tagging once (REG-1), CV once (REG-2),
  keep only V8's unique **symmetry test**.

**Explicitly NOT doing (council demoted/killed):** SEL-2, SEL-3, SEL-5, VOL-1, VOL-2 (killed), VOL-3,
VOL-4, REG-3, EX-1, EX-2, EX-4 (killed). Rationale: all are "another filter / another exit knob" on a
losing base = the integrated trap. *They may be revisited only as logged features inside the auto-label
study (Workstream C), never as gates fit to the 60 labels.*

---

## 2. The plan — five workstreams, sequenced

### WORKSTREAM A — Validation backbone *(do FIRST; everything depends on it)*
Nothing downstream is trustworthy until the scoreboard is honest. This is the anti-SBRS-phantom layer.

- **A1 (V7) — One-codebase backtest = screener path.** Make `phase4/backtest_ztt.py` run the *screener*
  code bar-by-bar so high/low look-ahead is structurally impossible. Fills at **next-bar open** (never
  the signal candle's close). Keep the **F7 phantom-fill assert** (`low ≤ fill ≤ high`) on every fill.
  Add an **outlier/bad-tick scrub** (tag-and-review, *not* blind-delete — Gold news spikes are real).
  Model **missed orders / "unables"** on fast moves, not just slippage.
  *Falsifier:* zero fills outside `[low,high]`; re-running with vs without scrub/next-bar-fill **must**
  drop PF (honest direction); any config with WR>70% or near-zero DD is presumed buggy.
- **A2 (V9 + EX-5) — New headline metric stack.** Replace closed-trade PF with **information ratio**
  (primary) + **Calmar / Sortino / Ulcer** + the **full per-trade R-multiple percentile distribution**
  + **per-trade kurtosis** (>7 = leak flag). Add the **cap-MFE audit** (for every %-cap exit, record
  MFE within MAX_HOLD after the cap → quantify R "left on the table"). Re-express +8.72R as
  **compounded equity + worst-sequence**.
  *Gate (Gold-specific, load-bearing):* a long-biased Gold system **must beat Gold buy-&-hold's
  information ratio over the same window, and per regime sub-period** — else the "edge" is just long-Gold beta.
- **A3 (V2) — Trade-shuffle permutation null.** Hold trade-count, long/short ratio, and hold-time
  distribution constant; **block/stationary bootstrap** (preserve trade adjacency — Chan warns naive IID
  is too severe) the entries across 10Y Gold 10k×, apply the identical %-cap exit + cost model. Report
  where +8.72R (and any mechanized variant) lands.
  *Gate:* net-R must exceed the **95th percentile** of the null, **and not only in the down-trend bucket**
  (regime seat). Runs on existing data now — no new labels needed.
- **A4 (V6) — Plateau-not-peak robustness.** Geometric sweep of every tunable (TP cap 1.0/1.25/1.5/1.75/2.0%,
  SL buffer, retest tol). Require a **contiguous band where ≥70% of configs are profitable**; report
  **average−1SD**, never the best config. This validates whether the "best, validated" 1.5% cap is a real
  plateau or a lucky point on 30 takes. *Caveat (stated in canon):* a plateau on a PF~1.0 base just means
  it *robustly* has no edge — pair with A3/A5.
- **A5 (V3) — Vertical / standalone-first gate.** Score filters by **% of profitable parameter-configs**
  vs the base; a filter passes only if %-profitable rises AND (avg↑, SD flat) or (SD↓, avg flat). Cap the
  autonomous layer at **≤4 features**. This is the test that may *correctly kill* the autonomy ambition.
- **A6 (V5) — Pre-register the OOS protocol NOW (before labels exist).** Encode as a runnable spec +
  falsifier-doc entry: time-ordered **70/20/10** split, fit on train, model-select on test, **consume the
  10% OOS exactly once**; gates = conditional-entropy/MI (primary, AUC fragile at small N) + χ²>3.84 vs
  trade-everything + df-correct t-stat + positive post-cost net-R, **in every regime fold**.
  Writing this before the data exists removes the temptation to invent the bar after seeing results.

### WORKSTREAM B — Regime instrumentation *(parallel with A; cheap, enabling)*
Turns WALL 3 (down-month/short contamination) from a narrative caveat into a measurable contingency table.

- **B1 (REG-1) — `regime_tags(df, i, p)`.** Pure causal function at each break bar: `trend_dir`
  (reuse `_trend_state`), **ER** over a frozen 20-bar window (export the existing G4 net/path math as a
  *continuous* value), **ADX(14)** (add to `compute_indicators`), **vol_bucket** (ATR/median-ATR over a
  *lagged, non-overlapping* 200-bar window). Append to `DEC_COLS` in `ztt_screener.py`. **Tag only — never
  gate; thresholds descriptive, never tuned to the 60 labels.**
  *Acceptance = the contingency table:* running over the 60 labels must **reproduce the known bias**
  (~all takes in down-trend cells). If it doesn't, the tagger is broken.
- **B2 (REG-2) — `tests/_ztt_regime_cv.py`.** Regime-stratified, time-ordered folds; any candidate
  discriminator must clear its bar (precision/net-R, see SEL-1) **in EVERY fold, not pooled**; flat
  slope-of-monthly-R; χ²>3.84. **Dry-run now** on the 60 labels — it *should* refuse to certify (only the
  down/short fold is populated). That correct refusal is the PASS. **Hard rule: never relax "every fold"
  to "most folds."**
- **B3 (V8 symmetry test) — only the unique part of V8.** Any Gold long-only finding from the down-month
  **must be re-run on up-trend data**; if the asymmetry breaks, it was a regime artifact → rejected.
  Plus live drift monitors (consolidated here, fed by REG-1): monthly-R slope, 2-sample t (early vs
  recent), loss-run kill. **Detect divergence, never predict regime.**

### WORKSTREAM C — Label corpus + outcome learning *(the actual unlock for autonomy)*
This is where the 73%-discretionary wall is genuinely attacked — by **more data**, not more knobs.

- **C1 (SEL-4 / REG-4 / V1, built ONCE) — Auto-label the 10Y.** Run `generate_setups_v2(apply_gates=False)`
  over the full 10Y, simulate each setup under the **A1 honest fills + %-cap exits**, label
  **good** (≥1.5R / TP before SL) vs **bad**, tag with B1 regime. Then test candidate features for
  discrimination on the **auto-labels** with time-ordered, regime-balanced CV (every fold) + the A3 null.
  *Epistemics (keep sharp — Socrates):* auto-labels answer **WALL 4** ("does the feature predict a
  profitable *outcome*?", large-N), **not WALL 1** ("does it predict the *user's take*?"). The
  **agreement vs divergence** between auto-label and 60-user-label feature importances **is the measured
  discretionary residual** — report it, don't bury it.
  *Mandatory dependency:* A1 must be live first; if auto-good-rate returns 95–100%, **halt** — that's the
  SBRS fill leak again.
- **C2 (SEL-1) — Precision-at-take-rate evaluator.** Add `precision_at_takerate(score, labels, target_rate)`;
  report precision + taken-subset net-R at 3% / 6% / 10% take-rates (per regime, never pooled). Retire
  balanced-AUC as the bar (keep as secondary diagnostic).
  *Honest caveat:* at 60 labels a 3% take-rate ≈ 2 setups → **diagnostic-only; must not gate anything**
  until ≥~500 regime-balanced labels.
- **C3 (SIZE-6) — Enrich `decisions.csv`.** Add scale-invariant columns: `atr_at_entry`, `sl_dist_atr`,
  `realized_vol_20bar`, `vol_regime_bucket`, `price_level`, and post-hoc `realized_R`, `MFE_R`, `MAE_R`,
  `bars_held`. **Fenced: these feed SIZING/regime validation only — not mined for selection** until the
  500-label OOS bar is met (snoop guard).
- **C4 — Keep collecting user take/skip labels toward ~500, regime-balanced.** The 30 takes were ONE
  down-trend month. **Priority = capture an up-trend month** (the long-side edge is *untested data, not
  weak data*). Harden the screener first (throttle the 178/mo alerter to avoid alert-fatigue/anchoring on
  the user's only proven edge).

### WORKSTREAM D — Exits *(already SOLVED; verify, then at most one refinement)*
- **D1 (EX-5 cap-MFE audit) gates whether D2 even ships.** If the audit shows median "left-on-table"
  >~0.5R **concentrated in trending months**, the fixed cap is amputating the fat right tail → test a
  trailing/structural runner. Otherwise **certify the 1.5% cap and reject all runner variants.**
- **D2 (EX-3, conditional on D1) — Measured time-stop.** Compute the 10Y bars-to-+1R distribution +
  continuation half-life; set `N_TIMESTOP` = small multiple, **frozen before any PnL A/B** (derive from a
  series property, not optimized to PnL). A/B vs `MAX_HOLD=144`. *Accept only if* net-R/info-ratio not
  worse AND max-DD-duration improves AND stable across the N-neighborhood AND it doesn't clip capped winners.

### WORKSTREAM E — Sizing *(dormant until an edge is validated by A+C; spec now, fire later)*
- **E1 (SIZE-5) — Fat-tailed Kelly as a CEILING, never a target.** When (and only when) a selection edge
  clears the A6/B2 OOS gate: Monte-Carlo the **validated, fat-tailed** R-distribution (not the Gaussian
  formula) → deployable risk = `min(¼-Kelly, 5% hard cap, 6–8% vol-target size)`, require Risk-of-Ruin <1%.
  **Falsify-by-design:** if the implied safe size rounds to ~0, that *confirms nothing is deployable.*
  No Kelly number may be quoted before validation (overconfidence trap).
- **E2 (SIZE-4) — Forward exposure cap + Prob(DD)/loss-run kill-switch.** Pre-registered from the math
  *before* touching live data; **t(4) MC is the primary tail estimate**, the normal closed-form is a coarse
  alarm only. Dry-run must NOT fire on labelled history but MUST fire on an injected synthetic regime break.

---

## 3. Sequencing & dependency graph

```
A1 (honest backtest) ──┬─► A2 metrics ─► A4 plateau ─► A5 vertical gate
                       ├─► A3 permutation null
                       └─► C1 auto-label 10Y ──► C2 precision-at-take-rate
B1 regime tags ────────┴─► B2 regime CV ─► B3 symmetry           │
                                                                 ▼
C3 enrich log + C4 collect up-trend labels ─► (≥500 regime-balanced)
                                                                 │
                                       A6 OOS protocol (pre-registered) gates ▼
                                              ── edge validated? ──┬─ YES ─► E1 Kelly ceiling + E2 kill-switch ─► move off 0.00%
                                                                   └─ NO  ─► screener-only confirmed (book-endorsed)
D1 cap-MFE audit ─► (conditional) D2 time-stop
```

**Phase 1 (now → ~1 wk):** A1, A2, B1 — the honest scoreboard + regime tags. Re-baseline *all* existing
ZTT numbers under honest fills + info-ratio. Expect the headline numbers to **drop** (that's the point).
**Phase 2 (~1–2 wk):** A3, A4, A5, B2, C1, C3, D1 — run the cheap-on-existing-data falsifiers and the
10Y auto-label study. This either surfaces a real outcome-feature edge candidate or confirms screener-only.
**Phase 3 (ongoing, months):** C2, C4, A6 — accumulate the ~500 regime-balanced labels (esp. an up-trend
month), then run the single-shot OOS once.
**Phase 4 (gated):** D2, E1, E2 — only if an edge clears OOS.

---

## 4. Pre-registered kill criteria (so we can't sunk-cost ourselves)

1. **A1:** if the honest-fill re-baseline does **not** lower PF vs the old numbers → look-ahead still present, halt.
2. **A2:** if ZTT info-ratio does **not** beat Gold buy-&-hold **per regime** → the "edge" is long-Gold beta, not skill.
3. **A3:** if +8.72R sits **below** the 95th percentile of block-bootstrap random placement → timing/selection adds nothing.
4. **C1:** if a feature discriminates **only in the down/short fold** → regime-bound discretion, not edge. If auto-good-rate is 95–100% → fill leak, void the run.
5. **A6/B2:** OOS AUC<0.65 (per-fold) OR χ²<3.84 OR OOS net-R≤0 after cost in any regime fold → **screener-only, permanently, no re-tune.**
6. **E1:** if validated-edge ¼-Kelly rounds to ~0 → nothing deployable; ZTT stays a screener.

The binding question (Socrates) is **"is the discretionary judgment teachable from labels?"** — *not*
"can we add another filter." This plan is built to answer that question honestly, and to accept
"no, it's a screener" as a legitimate, book-endorsed outcome rather than escalating sunk cost.

---

## 5. Net effect on the strategy

- **Core geometry:** unchanged (price action, 10m, break-retest — sacred).
- **What improves:** the *honesty* of every number (A), the *visibility* of regime contamination (B), the
  *size* of the learning corpus (C), the *robustness* of the already-good exits (D), and a *rule-based*
  path off 0.00% if and only if an edge survives (E).
- **What we stop doing:** bolting more selection filters onto a losing base (the integrated trap).
- **Honest current state, unchanged by this plan until executed:** ZTT is a **high-recall screener +
  human selection** (the user's +10.29R is the edge). Auto-size remains **0.00%** until A+C+OOS prove otherwise.

---

## EXECUTION LOG — Phases 1 & 2 complete (2026-06-14)

**Phase 1 (validation backbone + regime instrumentation) — DONE.**
- A2 `analysis/real_trades/metrics.py` (info-ratio headline + Sortino/Calmar/Ulcer + R-dist + cap-MFE + beat-B&H).
- B1 `src/regimes/ztt_regime.py` (causal trend_dir/ER/ADX/vol_bucket), wired into screener `DEC_COLS`.
- A1 `phase4/backtest_ztt.py` honest fills (next-bar open, phantom-fill assert, gap-aware exits, outlier/unable).
- Result: honest fills **lowered** performance (look-ahead removed). v2 screener traded blind —
  **1Y:** net −$1,360, IR −0.38, PF 0.92; **10Y:** net −$4,807, IR −0.31, PF 0.90, maxDD 58.8%.
  **Neither beats Gold buy-&-hold (1Y 0.88 / 10Y 0.69)** → mechanical edge is just Gold beta.
- **D1 SETTLED:** cap-MFE median left-on-table 0.26R (10Y: up 0.38 / down 0.26 / range 0.24, all <0.5R)
  → 1.5% TP cap does NOT amputate the tail; **certify the cap, drop D2 (no trailing runner).**

**Phase 2 (falsifiers, auto-label, robustness) — DONE.** Shared engine extracted to `ztt_sim.py` (V7 one-codebase).
- **C1** `phase4/auto_label.py`: 10Y, **8,426** labelled, good-rate 15.8% — **every feature AUC ≈ 0.50 in every
  regime fold**; no outcome edge at scale. Corpus `logs/ztt_autolabel/corpus_10y.csv`.
- **A3** `phase4/permutation_null.py`: actual timing at the **45th pct** of the shift null (p=0.55) = random.
- **B2** `tests/_ztt_regime_cv.py`: every-fold gate; **correctly REFUSES** the under-powered 60-label sample.
- **A4/A5** `phase4/robustness.py`: **no profitable plateau** (0% configs); vertical gate **rejects autonomous
  filtering** (base 67% → +false-bo 0%). false-bo is a WALL-1 user-rule, not a WALL-4 profit filter.
- **C3** sizing columns added to screener (fenced to sizing/regime validation).
- Tests: `tests/test_ztt_v3_metrics_regime.py` (16). Full suite **215 passed, 2 skipped**.

**Combined verdict:** three independent attacks converge — **no mechanizable selection/outcome edge exists in
this data, in any regime.** Confirms the books' thesis rigorously. ZTT = high-recall screener + human; auto-size
**0.00%**. Exits settled. **Remaining: Phase 3** (collect regime-balanced ~500 labels incl. an up-trend month;
C2 precision-at-take-rate once N≥500; A6 single-shot OOS) + **Phase 4** sizing (dormant until an edge validates).
