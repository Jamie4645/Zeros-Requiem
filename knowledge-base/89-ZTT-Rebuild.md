---
tags: [ztt, zeros-true-trade, rebuild, gold, intraday, 10m, price-action, active]
aliases: [ZTT, Zeros True Trade, Gold Intraday Rebuild, Active Phase]
related: [[87-Supervised-Rebuild]], [[84-Realistic-Fill-No-Edge]], [[81-Audit-2026-06-01-Phantom-Fill]], [[88-Audit-Harness-Index]]
---

# 89 — ZTT (Zero's True Trade): Clean-Slate Intraday Gold Rebuild

**This is the active phase.** Supersedes SBRS entirely. Built clean-slate from the
user's documentation of **25 real annotated Gold trades** (`analysis/real_trades/Zeros True Trade 5m - 15m.docx`).
Does NOT inherit SBRS 2.0 logic (confluence scoring, FVG/liquidity, reversal injection).
Gold-only; all other instruments PAUSED. Full plan: `analysis/real_trades/ZTT_PLAN.md`.

## Decoded strategy
- **Indicators:** WMA(144, close) = slow trend baseline (≈24h on 10m); SMMA(5, close) = fast (≈50m).
  Bullish = SMMA>WMA; bearish = WMA>SMMA. (Opposite labeling to old canon, physically correct given periods.)
- **Timeframe:** 10m primary (5m/15m later). Intraday — NOT 1H.
- **Setup:** with-trend (or confirmed-reversal) **break & retest of a respected horizontal level** (2–5 clean touches) → enter on retest of the flipped level.
- **SL:** beyond the most recent opposing swing (structural invalidation).
- **TP:** 3R default, capped at the nearest prior significant level.
- **Discipline (refined w/ user 2026-06-09):** two valid modes — *continuation* and *confirmed reversal* (break of a strong opposing swing, e.g. Tr9/23/24/25). *Blind* counter-trend is the mistake (Tr12/20/22). Level quality = **clean respect** (wick rejections, no closes-through), not raw touch count (Tr8 lost on a disrespected level).

## Locked decisions
10m primary · MA cross = confluence (not gate) · counter-trend A/B (continuation-only vs +confirmed-reversal; both block blind counter-trend) · TP 3R + structural cap · WF 10Y · calibration = the 25 trades only (survivorship caveat accepted, WF carries the proof).

## Dual-council verdict (2026-06-09) — both PROCEED-WITH-CHANGES
Arbiter (data, cost-skeptic, execution, falsifier, red-team, socrates) + Philosophical (Popper, Munger, Taleb, Feynman, Kahneman). Mandates folded in:
- Entry = **candle-close-rejection, never limit-at-level** (phantom-fill antidote), frozen before replay.
- **Phantom-fill tripwire** on every fill (`low ≤ fill ≤ high` + level actually traded).
- Phase 3 scores **entry/skip only, not exits** (TP narration is hindsight-contaminated — Tr16).
- Thresholds **frozen by rule** before replay; ≤2 re-tunes (overfit guard).
- **Fidelity ≠ profitability** — separate verdict branches (Socrates).
- 6 pre-registered falsifiers (F1 replay fidelity judged most likely to trip).
- Survivorship: 25 curated trades over one Jan–Jun 2026 bull ramp → WF must show edge in chop/down regimes.

## Phase 0 results (2026-06-09) — COMPLETE ✅
- **Non-Gold paused:** runner `SYMBOLS_CONFIG`→Gold-only; `SYMBOL_RISK_CAP` non-Gold→0. `risk_manager.py` sacred lock lifted.
- **M10 native** via OANDA; `oanda_fetcher.py` wired (`'10m'→'M10'`, 144 bars/day).
- **Data:** 1Y (35,468 bars) + **10Y M10 (354,110 bars, 2016→2026)** cached. 10Y WF feasible.
- **Timezone resolved:** platform = London time → BST (UTC+1) on/after 2026-03-29, GMT (UTC+0) before. Doc's "UTC+1" only right in summer.
- **⚠️ Timestamps drift, prices are reliable.** Tr11 stated on a market-closed Sunday; Tr25 off by ~2 days; Tr2 off by hours — all locate cleanly by price. **Phase 3 anchors setups by PRICE+STRUCTURE in a ±3-day window, not timestamp.**
- **Cost model** (`src/regimes/ztt_costs.py`, session-gated): vs 25 trades median cost 5.2% of risk, max 15.5%; only Tr18 hits rollover block (and won) → rollover gate is **configurable + A/B**, not hard exclusion. No trade < 10pt SL floor.

## Phase 1 (2026-06-09) — spec drafted, falsifiers locked, awaiting threshold sign-off
- **Spec:** `docs/ztt_spec.md` v1.0 (FROZEN draft). **Falsifiers:** [[90-Pre-Registered-Falsifier-ZTT]] (F1–F6, locked).
- **Geometry finding (`phase0/trade_geometry.py`, 24/25 located):** R:R clusters at 3.00 (fixed 3R confirmed); SL = 1.5–6.7 ATR (median 3.0 → structural, not fixed multiple); MA-confluence present in 75% (→ confluence not gate); **price on WMA-144 trend-side only 67% → WMA-144 is context/momentum, NOT the trend filter. Trend comes from swing STRUCTURE.**
- **Design correction:** trend classification = structure (HH/HL vs LH/LL via fractal swings); WMA-144/SMMA-5 = confluence only.
- **Awaiting:** user sign-off on the §9 threshold table (SACRED: WMA144/SMMA5/ATR14/MIN_RR3.0; + 11 frozen mechanization params) before Phase 2.

## Phase 2 (2026-06-09) — COMPLETE ✅
- Built `src/regimes/ztt.py` clean-slate (no SBRS imports): `ZTTParams` (frozen SACRED+mechanization), `compute_indicators`, `_trend_state` (structure-based), `_Level`+clean-touch scoring, causal `generate_setups`, `ZTTSetup`. Entry = candle-close rejection; phantom-fill invariant enforced.
- Tests `tests/test_ztt_primitives.py` (12) — SACRED pins, helpers, phantom-fill guard, SL/TP geometry, Arm A/B. **Full suite 199 passed, 2 skipped** (SBRS untouched).
- **⚠️ Early signal:** generator fires ~**1,294 setups/yr (~108/mo)** vs the user's ~5-6/mo — ~46% are 'range' mode. Confirms the council's core thesis: the edge is *selectivity*. Not a Phase-2 failure (primitives correct, invariants hold); Phase 3 tests fidelity to the 25, Phase 4 tests whether the noise bleeds under realistic cost.
- Structural-TP cap deferred to Phase 4 (`struct_cap_tp` flag present; geometry shows it rarely binds).

## Phase 3 (2026-06-09) — replay run; council ruling = **HALT (re-enter at ITERATE)**
- Harness `phase3/replay.py`, results `phase3/PHASE3_RESULTS.md`. Re-tune #1 (SL anchor → swing-before-break, chart-confirmed by 4 agents) used (1 of 2).
- Raw replay: setups SEEN 19/19; entry within 0.3R 22/25; strict F1 (entry AND SL) 6/19 (A) / 7/19 (B) = **HALT (<12)**; skip gate **3/4 < 4/5 FAIL** (Tr20 leaks).
- **Dual-council (Falsifier/Red-Team/Socrates + Philosophical) ruled HALT.** Findings (legitimate, accepted):
  1. **Protocol breach:** the match window was widened ±3d→±10d (Phase-0 drift motivated, but a frozen-falsifier goalpost move). Must revert or pre-commit a principled price-anchor.
  2. **Base-rate:** at ~108 setups/mo, "19/19 seen" is ~expected by chance (≈53%+/trade) — recall measured, **precision + null-shuffle baseline NOT measured**. Geometry floor tests nothing at this fire rate.
  3. **Stop = the risk, unmechanized:** entry fidelity w/o SL fidelity = half a trade; R undefined ⇒ 3R/sizing/expectancy unvalidated. "fidelity≠profitability" mis-invoked (Popper immunization).
  4. **Selectivity is the real edge:** discrimination (why ~5-6/mo not ~108) is the unmodeled discretionary judgment.
- **Re-entry conditions (before any Phase 4):** (a) re-score with pre-committed anchoring + **null-baseline + precision**; (b) add a **selectivity filter** to cut the fire rate toward the user's; (c) re-score F1 with the **mechanized** stop, reach ≥12/19; (d) skip gate ≥4/5. Re-tune budget: **1 left**.

## Phase 3 HONEST RE-SCORE (2026-06-09, `phase3/rescore.py`) — DECISIVE
- **Fire rate 178/mo** vs user 5.9/mo over the trade span; **precision proxy 3.3%** (25 of 750 algo setups).
- **Null-baseline test (K=300 random-date sets, identical rules):** REAL matched 17/25 (±3d) / 21/25 (±10d); NULL matched **17.5 / 21.1** — **z≈0, p≈0.67. The user's real trades are STATISTICALLY INDISTINGUISHABLE from random dates.** "19/19 seen" was selection-on-the-dependent-variable / overfiring, not signal.
- **CONCLUSION:** the break-retest GEOMETRY is not the edge — it fires constantly. The edge is **discrimination** (which ~6 of ~178/mo to take), i.e. the discretionary judgment (level significance, "clean" PA, context). A stop/trend re-tune cannot create selectivity. This independently reconfirms the SBRS post-mortem ([[84-Realistic-Fill-No-Edge]]): the edge is discretionary.
- **Mechanizing it needs NEGATIVE examples** (the setups the user SKIPPED + why) — unlearnable from 25 positives alone.

## Phase 3 v1.1 selectivity layer + ablation (2026-06-09)
- **KEY REFRAME:** user's real trade rate is **~100/mo** (the 25 were a sample; the ~100/mo broker account is closed). So algo 178/mo vs ~100/mo ≈ **1.8:1**, not 30:1 — the overfiring critique largely dissolves, BUT it also means the null-separation test is **UNDERPOWERED** (can't detect a 1.8:1 edge from 25 positives).
- Built v1.1 gates in `ztt.py` (spec extension): G3 respect, G4 structure/no-chop, G5 HTF(1h/3h EMA), G6 volume + ablatable shift signals {momentum, FVG, sweep}. Harness `phase3/ablation_v11.py`.
- **Ablation result:** base gates cut 178→68/mo; **NO shift combo separates real trades from random** (p≥0.33; FVG weakly best, real 5 vs null 3.9 p=0.33). Sweep detector returned 0 (too strict / mis-fit). Base-gated real(8)≈null(9) ⇒ the HTF/vol/structure gates reject real trades ~as often as random ⇒ not aligned with the user's actual selection.
- **CONCLUSION:** fidelity-matching is **data-limited & inconclusive** (need negatives we don't have). Pivoted to profitability (user choice).

## Phase 4 — profitability backtest (2026-06-09) — NO EDGE
- `phase4/backtest_ztt.py`: honest realistic-cost (session-gated spread+slip), phantom-guarded (exits only on actual SL/TP touch), 1-position-at-a-time, 1% risk.
- **1Y M10, all configs KILL:** raw PF 0.97 (−$722) · **base-gated PF 1.10 (+$1,323, Sharpe 0.05, DD 20%) = best** · base+FVG 0.97 · base+momentum 1.00 · full v1.1 0.93. Every smart-money shift signal made it WORSE than plain base-gating (echoes SBRS audit).
- **10Y M10 multi-regime (DECISIVE, even worse):** ALL configs net-NEGATIVE — raw PF 0.88 (−$6,342, 66% DD) · base-gated PF 0.93 (−$2,855, 42% DD) · base+FVG 0.93 (−$2,046) · base+momentum 0.89 · full v1.1 0.90. The 1Y base-gated +$1,323 was pure 2025-26 gold-bull regime luck → flips to −$2,855 across the cycle. **No config survives out of sample; the strategy is net-negative across a full cycle.**
- **TRIPLE-CONFIRMED VERDICT: the ZTT edge is discretionary, not mechanizable from this data.** (1) geometry fires everywhere; (2) selection unvalidatable (underpowered, no negatives); (3) mechanical PF ceiling ~1.10, fails all elite gates. Same wall as [[84-Realistic-Fill-No-Edge]], now rigorously established.
- **Genuinely constructive paths left:** (A) build ZTT as a **setup SCREENER/alerter** (high recall — it sees all break-retests; user applies the judgment) rather than an auto-trader; (B) **forward-log take/skip decisions** to accumulate the negatives needed to learn discrimination over time.

## DELIVERED (2026-06-09): ZTT Screener + Labeling Loop (user chose A+B)
- `src/screener/ztt_screener.py` — `run_screener(config='base'|'raw')`: fetches latest Gold 10m, runs ZTT, logs NEW setups (dedup by entry_time) to `analysis/real_trades/ztt_screener_log.csv` with full features (mode, entry/SL/TP, RR, level touches/disrespect, momentum/FVG/sweep flags, htf_up, struct_eff, vol_ratio, ATR) + **blank `decision`/`reason`/`outcome` columns** for the user to label. Prints recent setups as alerts.
- This is the honest product: high-recall screener (the algo's one strength) + the labeling tool that accumulates the **negatives** (skips) needed to eventually learn discrimination. Tested on cached data (38 setups / 14-day window logged). Full suite 199 green.
- **Bottom line:** ZTT is NOT a deployable auto-strategy (PF ~1.10). It IS a useful human-in-the-loop screener + a data-collection path toward mechanizing the discretionary edge. Gold live auto-size = 0.

## Dual-council ADVISORY on what next (2026-06-09)
Both councils convened on the final verdict. Convergent guidance:
- **Reframe (Socrates):** stop asking "can the geometry be auto-traded" (answered NO ×3). Binding question: **is full autonomy a hard requirement, or is human-in-the-loop acceptable as "top-1% algo"?** Answer this BEFORE more weeks.
- **STOP (Munger/Feynman/Red-Team):** (1) re-tuning/backtesting from the 25 positives (well dry, PF~1.10); (2) adding smart-money signals (FVG/sweep/momentum each made PF WORSE).
- **The real falsifiable experiment (Feynman/Popper):** H: "on flagged setups, the user's TAKEN trades beat SKIPPED ones (matched, OOS)." Kill: after ≥300 paired decisions, takes ≤ skips (p<0.05) → discretionary edge also unteachable, STOP. Skips finally supply negatives.
- **Screener hardening REQUIRED before labeling (Red-Team + Data):** throttle the 178/mo alerter (iatrogenic alert-fatigue/anchoring risk to the user's only proven edge); ideally passive take/skip capture from broker feed. Fix 4 schema gaps: add `label_time`+`label_lag_flag`, closed `REASON_CODES`, `regime_tag`, perceptual features (break_candle_body_atr, break_candle_close_pct, retest_bars_to_level, touch_quality_ratio, htf_dist_to_level_atr). Pre-registered model bar: time-ordered 70/30, AUC≥0.65, null-shuffle<0.55, ≥150 test/class, regime-balanced (~500 labels / 6-8mo).
- **Two cheap closing tests (Gold + Regime arbiters; expect failure, but bring closure):** (1) long-only base-gated 10Y (pass PF≥1.3); (2) ER(20)≥0.30 regime gate, frozen threshold, one shot (pass: trending PF≥1.5, ≥200 tr, ≥4 WF). If both <1.1 → formally close mechanical Gold.
- **Bias (Kahneman):** sunk-cost escalation risk → pre-commit kill criterion + decision date in writing; reframe "make it profitable" → "is the judgment teachable".

*Session 2026-06-09 complete through Phases 0–4 + screener + dual-council advisory. Awaiting user: autonomy-vs-HITL decision + whether to run the 2 closing Gold tests; then harden screener per Data/Red-Team before any labeling.*

## ZTT v2 — labeling experiment executed + engine built (2026-06-14)

The 2026-06-09 advisory's falsifiable experiment was run. The user labelled **60 algo setups**
(TradingView overlay, `analysis/real_trades/tv_review/`) **30 take / 30 skip** with written reasons —
the negatives the 25-trade calibration set never had. Spec: `analysis/real_trades/ZTT_V2_SPEC.md`.
Engine: `src/regimes/ztt_v2.py` (reuses frozen `ztt.py` primitives; 199 tests untouched).

**H ("takes beat skips") — CONFIRMED on the labelled data:** take-subset **+10.29R** vs skip-subset
**−24.75R** (zero skip wins), independently verified. The discretionary edge is real. BUT:

**Two-layer build outcome (council: red-team/falsifier/cost-skeptic/gold/socrates):**
1. **EXIT redesign — VALIDATED, adopted.** Fixed-3R → structural + **%-capped TP** (1.5% best). F3 re-exit
   transfer PASS: user's takes net **+8.72R**, **WR 17%→40%** (timeouts convert to wins), edge
   **de-concentrates** (survives removing top-2 winners — kills red-team's "5 lucky shorts" attack).
2. **AUTONOMOUS selection filter — FALSIFIED.** Filter ablation (`tv_review/v2_ablate.py`): only
   **false-breakout + session** discriminate (keep 93% takes, reject 27% skips). Significance-pivot &
   momentum are non-discriminating (reject takes≈skips); opposing-level-cap over-rejects to n=0. Four
   mechanizations of the user's core judgment all fail → **~73% of skips are irreducibly discretionary**;
   the advisory's AUC≥0.65 bar is not met by these mechanical features on this sample. Standalone
   mechanical backtest **PF 0.90, negative** (loses traded blind).

**SHIPPED:** `ZTTV2Params` defaults = **high-recall SCREENER** (base geometry + false-bo + session +
%-cap exits) — keeps ~93% of the user's takes, surfaces ~335 setups/yr for the user to judge. **The user
is the selection layer** (his +10.29R), the engine supplies clean setups + improved exits. This realizes
advisory path A (screener) and answers H (judgment IS the edge; the *features* don't yet capture it).

**Next (toward autonomy):** the 30 takes were ONE down-trend month, short-biased (gold arbiter: regime-
contaminated). Collect labelled take/skip across MORE months & an UP-trend, then re-test discrimination on
a fatter multi-regime sample (advisory's ~500 labels / 6–8mo bar). Diagnostics:
`tv_review/{f3_reexit_transfer,v2_validate,v2_ablate,v2_screener_characterize}.py`.

## ZTT v3 — Book-informed rebuild (2026-06-14)

User added two trading bibles (**Ernest Chan, *Algorithmic Trading*** + **Perry Kaufman, *Trading Systems
and Methods* 5th ed**). Decoded via a 27-agent council workflow (15 readers → 264 principles → 6
correlators → 35 proposals → 6 adversarial seats → 210 verdicts). Extracts: `analysis/book_extracts/`.
Plan: `analysis/real_trades/ZTT_V3_BOOK_INFORMED_PLAN.md` (+ plan file `.claude/plans/`).

**Headline (convergent, both authors + all 6 seats):** ZTT's wall is a **measurement + sample-size
problem, NOT a missing selection filter.** Council *demoted every "add a filter" proposal* (Kaufman's
"integrated trap": a filter looks good only because the base loses — ZTT's exact PF~0.90 case) and
*unanimously elevated* the discipline layer. Path to autonomy = honest scoreboard + ~500 regime-balanced
labels (esp. an UP-trend month) + 10Y auto-label study — not a cleverer filter. Screener-only stays a
legitimate, book-endorsed outcome.

### Phase 1 COMPLETE (2026-06-14) — validation backbone + regime instrumentation
- **A2 metric stack** (`analysis/real_trades/metrics.py`): info-ratio (headline, replaces PF) +
  Sortino/Calmar/Ulcer + R-percentile distribution + excess-kurtosis leak flag (>7) + **cap-MFE audit** +
  **beat-Gold-buy-&-hold** gate + worst-sequence + live≈½-backtest. PF demoted to secondary diagnostic.
- **B1 regime tagger** (`src/regimes/ztt_regime.py`): causal `compute_regime`/`regime_tags` →
  trend_dir / ER (continuous) / Wilder ADX(14) / lagged-non-overlapping vol_bucket. **Tag only, never
  gated; thresholds descriptive.** Wired into `src/live/ztt_screener.py` `DEC_COLS`.
- **A1 honest backtest** (`phase4/backtest_ztt.py`, V7): one-codebase, **next-bar-open fills**,
  **phantom-fill assert** (F7, caught a real gap artifact → fixed with gap-aware fills), outlier/"unable"
  model. Headline = info-ratio.
- **Tests:** `tests/test_ztt_v3_metrics_regime.py` (13). Full suite **212 passed, 2 skipped** (no regressions).

**Phase-1 1Y honest result (decisive, as predicted):** honest fills **lowered** performance (A1 kill #1
satisfied → look-ahead removed). v2 screener traded blind = **net −$1,360, info-ratio −0.38, PF 0.92, WR
32.7%**, and **does NOT beat Gold buy-&-hold (IR 0.88)** → the mechanical long-biased "edge" is just Gold
beta / discretionary, confirmed on the honest scoreboard. **cap-MFE audit (D1): median left-on-table 0.26R
(<0.5R) → the 1.5% TP cap is NOT amputating the tail; reject trailing-runner variants (D2 unneeded).**
kurtosis −0.4 (no leak).

**Phase-1 10Y full-cycle honest result (DECISIVE, confirms across all regimes):** v2 screener traded blind
= **net −$4,807, info-ratio −0.31, PF 0.90, WR 36.6%, maxDD 58.8%, net_R −54.4** over 1,281 trades; raw
geometry worse (−$6,793, PF 0.86, maxDD 70%). **Neither beats Gold buy-&-hold (IR 0.69).** So the 1Y
down-month picture HOLDS across the full cycle — the mechanical long-biased strategy has no edge traded
blind, in every regime. **cap-MFE audit now regime-broken-out (43 capped): median left-on-table 0.26R
overall — down 0.26R, range 0.24R, up 0.38R, ALL < 0.5R → the 1.5% TP cap is not amputating the tail even
in up-trends. D1 SETTLED: certify the cap, no trailing runner (D2 dropped).** No kurtosis leak. Auto-size
remains **0.00%**. The honest scoreboard now rigorously establishes (not just asserts) that the value of
ZTT is the **screener + human selection**, and the path forward is the label-corpus + auto-label study
(Phase 2/3), not another filter.

### Phase 2 COMPLETE (2026-06-14) — falsifiers, auto-label, robustness (all on the ONE honest engine)
Architecture: extracted the honest fill/exit engine into `analysis/real_trades/ztt_sim.py` (one-codebase
V7 principle) — backtest, auto-label, permutation null all import it. Full suite **215 passed, 2 skipped**.

- **C1 auto-label (`phase4/auto_label.py`) — DECISIVE.** Labelled **8,426** raw-geometry setups over 10Y by
  honest OUTCOME (good = TP/cap or ≥1.5R). good-rate **15.8%** (no leak). **Every numeric feature AUC ≈ 0.50
  in EVERY regime fold** (er 0.49, adx 0.50, vol 0.48, rr 0.49, touches 0.49, sl/tp% 0.49); categorical
  good-rates flat (trend down15/range16/up17; long17/short15). **No feature predicts good outcomes anywhere,
  at N=8,426 across the full cycle.** Large-N proof that the geometry has no mechanizable OUTCOME edge (WALL 4).
  Corpus: `logs/ztt_autolabel/corpus_10y.csv`. (1Y mirror: 1,714 setups, same AUC≈0.50.)
- **A3 permutation null (`phase4/permutation_null.py`).** Block/adjacency-preserving "shift" null + IID null,
  same %-cap exit+cost. 1Y: actual net_R −11.6 at the **45th percentile** of the shift null (p=0.55) → the
  strategy's TIMING is indistinguishable from random placement. Pre-registered gate (95th pct) ready for any
  future discriminator / the user's take-subset.
- **B2 regime-CV (`tests/_ztt_regime_cv.py`).** Regime-stratified, time-ordered, **every-fold (never "most")**
  gate (AUC≥0.65 + positive take net-R per fold + χ²>3.84). Dry-run on the 60 labels **correctly REFUSES**
  (folds under-powered, <10/class). Useful nuance: the structural tagger spreads the 60 labels up22/down16/
  range22 — they are NOT all "down"; but each fold is under-powered → quantifies the ~500-label need.
- **A4 plateau + A5 vertical gate (`phase4/robustness.py`).** 1Y: TP-cap sweep 1.0–2.5% → **0% profitable
  configs, no plateau** (robustly no edge); IR improves as the cap WIDENS on blind trades (the tight 1.5% cap
  is a *selection-dependent* benefit — helps the user's takes, not blind population; consistent w/ D1). **A5
  vertical gate: base geometry 67% profitable-configs → +false-bo 0% (Δ−67) → autonomous filtering REJECTED**
  (Kaufman integrated-trap; false-bo is a WALL-1 user-rule, not a WALL-4 profit filter).
- **C3 sizing columns** added to screener `DEC_COLS` (atr_at_entry, sl_dist_atr, price_level + post-hoc
  realized_R/MFE_R/MAE_R/bars_held), fenced to sizing/regime validation (not selection-mined).

**Ablation + combo OOS (2026-06-14, `phase4/ablate_ztt.py` + `phase4/combo_oos.py`).** Full 1Y M10 ablation
(every active + legacy method, honest engine): STRUCTURAL keepers = G4 efficiency, level-anchored SL (beats
legacy swing SL), reversal mode, level-quality (MIN_TOUCHES monotone). INERT (prune candidates) = G3 respect,
G5 HTF-EMA, G6 volume, session gate, momentum-continuation. DEAD = liquidity-sweep signal (0 trades). HARMFUL
= opposing-level TP cap (PF 0.66). The 1Y-strongest levers — **MIN_TOUCHES=3, significance(S1), momentum(S2),
each ~+15-20 net_R on 1Y** — were stacked and tested OOS on 10Y through the pre-registered gates:
**KILL on all three** (IR −0.29 vs B&H 0.69; net_R NEGATIVE in every regime fold up/down/range; permutation
p=0.27 = random). Per-trade mean_R was actually WORSE than baseline (−0.069 vs −0.042) → the 1Y gain was
regime-luck, not discrimination. Confirms the AUC≈0.50 finding; documented so the dead-end isn't re-run.

**PRUNE (2026-06-14):** shipped `ZTTV2Params` simplified — **G3 (enable_respect) + G5 (enable_htf) turned
OFF** (truly inert: 1Y reproduces exactly n=266/IR−0.38; 10Y within 1 trade, n 1281→1282, IR −0.31→−0.28).
**G6 (enable_volume) KEPT** — the 1Y ablation labelled it inert but the 10Y re-run caught it filtering ~200
net-negative trades (removing it: IR −0.31→−0.43, maxDD 59%→66%), so it stays ON. G4 kept (pulls weight).
Lesson: 1Y "inert" ≠ 10Y inert — the re-verify caught a false-inert. Suite 215 passed, behaviour unchanged
(still KILL/screener-only); screener surface is now 2 always-on gates lighter.

**Phase-2 verdict:** three independent attacks (per-feature AUC at N=8,426, permutation null, vertical filter
gate) converge — **no mechanizable selection/outcome edge exists in this data, in any regime.** This is the
rigorous form of the books' thesis. The path to autonomy is the regime-balanced ~500-label corpus (esp. an
up-trend month) + the take/skip experiment (WALL 1), NOT another filter. ZTT stays a high-recall screener +
human selection; auto-size **0.00%**. Exits SETTLED (cap certified). Remaining plan: Phase 3 (collect labels,
C2 precision-at-take-rate once N≥~500, A6 single-shot OOS) + Phase 4 sizing (dormant until an edge validates).

*Created 2026-06-09. Hub note — append per phase.*
