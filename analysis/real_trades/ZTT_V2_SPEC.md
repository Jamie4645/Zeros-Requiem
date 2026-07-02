# ZTT v2 — Design Spec (driven by the 60-setup human review)

**Source data:** `tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv` — 60 setups, 10m XAUUSD,
base config. Human labels: **30 take / 30 skip**, each with free-text reason.
**Decode hub:** this file. **Build hub:** `knowledge-base/89-ZTT-Rebuild.md`.

---

## 1. What the labels prove (verified, independent compute)

| Subset | n | Net R (old 3R exits) | Mean R | Wins | Losses | Timeouts |
|---|---:|---:|---:|---:|---:|---:|
| TAKE | 30 | **+10.29** | +0.343 | 5 | 11 | 14 |
| SKIP | 30 | **−24.75** | −0.825 | **0** | 23 | 7 |
| ALL | 60 | −14.46 | −0.241 | 5 | 34 | 21 |

The human take/skip filter separates winners from losers by **1.17 R/trade**. Skips have **zero wins**.
The discretionary edge the Phase-4 audit said couldn't be learned (positives-only, 25 trades) is now
labelled with negatives. **This is the unlock.**

Weak/absent mechanical separators (so the edge is NOT in current features):
- `level_touches`: 2→0.53, 3→0.44, 4+→0.50 take-rate — **no signal**.
- `rr_target`: constant 3.0 — no signal.
- TP-distance%: takes (3.63%) are *larger* than skips (2.59%) — the human does **not** reject on TP width
  at selection time (he took wide-TP setups while criticising the TP). **TP width is an exit problem, not a
  selection problem.**
Mild separators: mode (range 0.59 > continuation 0.47 > reversal 0.33), direction (short 0.59 > long 0.39,
consistent with a down-trending month), session (rollover 0/2, ny_close 0/1 — both skipped).

---

## 2. Current code reality (verified by code map)

- **Break**: already close-confirmed (`close > level + 0.10·ATR`), `ztt.py:262-271`. NOT anticipatory.
  → The human's "you're predicting the break" = engine breaks a **minor** level while a **stronger opposing
  level** sits unbroken between entry and TP. A **significance** problem, not a break-mechanics problem.
- **Levels**: `MIN_TOUCHES=2` clean touches; no daily/weekly-extreme requirement except reversal mode
  (`_significant`, max/min over 30 bars). `ztt.py:110-111, 323-331`.
- **TP**: hard-coded `entry ± MIN_RR·sl_dist` (3R). `struct_cap_tp` param **exists but is never applied**
  in `_try_entry`. `ztt.py:414-419`. → root cause of every "% unrealistic / TP too wide" complaint.
- **SL**: structural — swing-before-break + `0.30·ATR`, fallback to local retest extreme. `ztt.py:398-412`.
- **Filters**: G4 efficiency/anti-chop + G1 momentum exist but are **OFF in `base`**; **no false-breakout /
  long-wick filter exists at all.** `_passes_gates`, `ztt.py:149-187`.

---

## 3. Layer 1 — SELECTION changes (each backed by ≥3 of the human's skips)

| ID | Rule (mechanism) | Backing skips |
|---|---|---|
| **S1** | **Significant-level gate.** Broken level must be a dominant extreme over a long lookback (daily/weekly hi-lo or top/bottom swing), not just 2 touches. AND no stronger *opposing* significant level may sit so close that a realistic TP can't clear it — enforced jointly with E1/E2 (close strong level → TP shrinks → R:R floor rejects). Captures the dominant "don't predict a break of the strong level". | 4,5,13,15,18,19,20,21,25,26,29,30,34,37,38,39,40 |
| **S2** | **Momentum / anti-chop ON by default.** Require G4 displacement-efficiency + a minimum break displacement (G1). No trading dead consolidation / "price not moving". | 7,8,9,16,17 |
| **S3** | **False-breakout filter.** Reject if breakout candle wick pokes >X·ATR beyond the level but closes back inside, OR price closes back across the level within K bars before the retest. (Explicit user rule: "WE DO NOT TRADE FALSE BREAKOUTS".) | 34 (explicit) + protects 25,26,37,38 |
| **S4** | **Session gate.** Trade `london_ny` + `asia`; skip `rollover` + `ny_close`. | 4 (rollover), 7 (ny_close) |
| **S5** | **Stricter reversal confirmation.** Reversal needs break of a *more* significant extreme (longer lookback / higher bar) than continuation/range. Lowest take-rate (0.33). | 20,21,39,40,56,57 |
| **S6** | **No-stacking / freshness.** Don't open a setup correlated with an active one (same direction, overlapping level band, before prior TP/SL resolves). | 3,15 |

## 4. Layer 2 — EXIT redesign (applies to every selected trade)

| ID | Rule |
|---|---|
| **E1** | **Structural + %-capped TP.** `TP = closest-to-entry of { nearest opposing significant level − buffer, entry·(1 ± MAX_MOVE_PCT) }`. `MAX_MOVE_PCT ≈ 2.0%`. R:R becomes an OUTPUT, not a fixed 3.0. |
| **E2** | **R:R floor** (param; grid-tested {1.0, 1.5, 2.0}, ALL reported — not cherry-picked). Rejects trades where a close strong level crushes R:R — this is the mechanism that unifies S1. |
| **E3** | **SL.** Keep structural swing-before-break; add a "respected-level anchor" variant (SL just beyond the traded strong level + buffer) matching the user's explicit tighter stops (#22, #31, #36, #42, #58). |

---

## 5. Validation plan

1. **Replication** — run Layer-1 filter over the 60 labelled setups. Report precision/recall vs human takes.
   Target: reject ≥80% of skips, keep ≥70% of takes.
2. **Re-exit** — recompute realized-R on the kept setups under E1–E3; compare to the +10.29R take-subset.
3. **Out-of-sample** — run v2 (L1+L2) over full 1y and 10y; net-R / PF vs the −14.5R/mo base population, at
   realistic session-gated cost.
4. **Phantom-fill tripwire** on every fill (sacred carryover guard).

## 6. Pre-registered falsifiers (FINALISED by arbiter-falsifier, 2026-06-13 — locked)

- **F1** — Skip-rejection: L1 keeps **>20%** of the 30 skips (>6 survive) → revert L1.
- **F2** — Take-recall (paired w/ F1): L1 recall on takes **<70%** → edge mis-encoded, revert.
- **F3** — Re-exit transfer: kept-take subset re-scored under E1–E3 nets **< +5.0R** OR mean **< +0.15R** OR
  top-2-removed ≤0 → KILL exit redesign. **STATUS: PASS (2026-06-13)** — best cap (1.5%) nets +8.72R,
  mean +0.291R, top-2-removed +1.42R. Evidence: `tv_review/f3_reexit_transfer.py`.
- **F4** — Concentration: removing top-2 winners turns net-R ≤0, OR >70% of net-R from one direction → screener-only.
- **F5** — Regime/temporal hold-out: over a 1y window incl. ≥1 up-trend month, long-side net-R <0 while short
  positive, OR overall 1y net-R ≤0 at cost → KILL or trend-matched deploy only. (THE down-trend trap.)
- **F6** — Cost-survival: 10y realistic-cost PF **<1.2** OR <200 trades → screener-only. (arbiter-cost-skeptic:
  the tighter-TP only survives because WR rises 17%→40%; if a 10y run shows WR doesn't hold, this trips.)
- **F7** — Phantom-fill: any fill at a price the bar's [low,high] never traded → immediate HALT. (sacred)

## 7. Council verdict — 2026-06-13 (PROCEED-WITH-CHANGES)

Seats fired: red-team, falsifier, cost-skeptic, gold, socrates. Key adjudications:
- **Red-team (was FATAL):** under the OLD 3R exits the edge was 5 trades (top-5 = 142.7% of +10.29R; longs net
  −0.71R; 4/5 winners short). F6-concentration already tripped. → The exit redesign (F3) had to be proven FIRST.
- **F3 ran and PASSED** and, crucially, **de-concentrated** the edge (1.5% cap: top-2-removed still +1.42R, WR
  17%→40% as timeouts convert). This refutes red-team's fatal attack AND the cost-skeptic's static-WR death verdict.
- **Cost-skeptic:** tighter TP is a cost trap *only if WR stays at 31%*. The real price walk shows WR rises, so it
  survives at the 1.5% cap. Min cost-viable TP ≈2.7% if WR were static — F6 is the live check on 10y.
- **Gold:** 2% cap sound as a ceiling (structural cap binds first); best "significant level" proxy = **prior-day/
  prior-week pivots + $50 round numbers** (implemented as S1); `REVERSAL_LOOKBACK` 30→240 bars (S5). Short-bias is
  **regime-contaminated** → F5 mandatory before any autonomous long deploy.
- **Socrates:** real fork is autonomous-strategy vs **screener**; the engine serves both, so the build isn't wasted.

**Outcome:** BUILD APPROVED. Only the 1.5% cap is robust; cap + RR-floor are **grid-reported, never hand-picked**.
Direction/regime (F5) and 10y cost (F6) are **deployment** gates, not build gates.

## 7b. BUILD OUTCOME — 2026-06-14 (`src/regimes/ztt_v2.py` built + tested)

The v2 engine was built (all of S1–S5 + E1–E3, toggleable) and tested against the 60 labels.

**Layer 2 (EXITS) — VALIDATED. Adopt.**
- F3 re-exit transfer PASSED: the user's 30 takes, re-exited under the %-capped TP, net **+8.72R**
  (1.5% cap) vs +10.28R under wide 3R — but **WR 17%→40%** and the edge **de-concentrates**
  (survives removing the top-2 winners: +1.42R). The tighter structural/%-cap TP is a genuine
  mechanical improvement over fixed-3R.

**Layer 1 (AUTONOMOUS SELECTION) — FALSIFIED. The edge is discretionary.**
- Filter ablation over the 60 labels (`tv_review/v2_ablate.py`): base geometry keeps 93% of takes
  but only rejects 13% of skips. Of the six selection mechanisms:
  - **false-bo (S3) + session (S4): DISCRIMINATE** — keep 93–100% of takes, reject 27% of skips combined.
  - **significance-pivot (S1a), momentum (S2): NON-discriminating** — reject takes≈skips (disc≈0.9), pure
    volume knobs.
  - **opposing-level cap (S1b) + RR-floor (E2): OVER-reject** — at 2-touch swing granularity a strong
    level is always nearby, so every TP collapses → n→0.
- Four independent mechanizations of the user's *core* judgment ("significant level", "momentum",
  "opposing level strong enough", "is there an edge here") all fail to separate his takes from skips.
  **~73% of his skips are irreducibly discretionary** with the available features. F1 (reject ≥80% of
  skips) is **un-meetable** without destroying recall → the autonomous selection filter is rejected.

**SHIPPED CONFIG (`ZTTV2Params` defaults) = HIGH-RECALL SCREENER + better exits:**
base break-retest geometry + S3 false-bo + S4 session + E1 %-cap TP. Keeps ~93% of the user's takes,
trims ~27% of obvious junk, surfaces the rest for the user to judge. **The user IS the selection layer**
(recovering his +10.29R edge), the engine supplies clean setups + the improved exits.

**Why this is the right call (not giving up):** red-team showed the +10.29R was 5 down-month shorts;
socrates + gold predicted the edge lives in judgment; the ablation confirms it across 4 feature sets.
Forcing a higher-rejection filter would be curve-fitting one regime. Path to autonomy: collect labelled
take/skip across MORE months & regimes (esp. an up-trend), then re-test discrimination on a fatter,
multi-regime sample.

## 8. Honest risk

30 takes / 1 month is a thin, single-regime (down-trend) sample. Every filter is a **stated general principle**
(significant level, opposing-level, momentum, no-fakeout), not a point-fit; F4/F5 guard concentration & regime;
cap/floor grid-reported. The build produces a v2 ENGINE (`src/regimes/ztt_v2.py`) usable as screener OR strategy.
**No SBRS logic inherited.** Sacred-param freeze deferred to post-F5/F6 validation. Nothing deployable yet.
