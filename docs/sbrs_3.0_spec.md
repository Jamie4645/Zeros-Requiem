# SBRS 3.0 — Clean-Slate Specification (DRAFT, 2026-06-02)

> **Status: DRAFT for co-design.** This supersedes SBRS 2.0, which was found
> (audit 2026-06-01) to have no real edge — its track record was a phantom-fill
> artifact, and its "smart-money" upgrades were proven net-negative. SBRS 3.0 is
> a deliberate strip-back to the simplest faithful codification of the user's
> discretionary breakout-retest, where **every component must earn its place by
> improving realistic-fill PF in ablation, or it is cut.**

## Design principles (non-negotiable)
1. **Codify, don't invent.** Every rule must trace to the user's methodology doc
   (`Zeros_Trading_Methodology.docx`) or to a measured improvement. No invented
   indicators or scoring math.
2. **Realistic fills only.** Validate on the fixed engine (limit orders fill only
   on a real touch; entries are candle-close unless proven otherwise). No
   feature is judged on phantom fills, ever again.
3. **Earn-your-place ablation.** A component ships only if removing it *hurts*
   realistic-fill PF on the full sample. Default for everything is OFF.
4. **No self-deception gates.** Full-sample BT must clear elite gates (PF ≥1.5,
   Sharpe ≥1.5, MaxDD ≤15%, expectancy >0) BEFORE walk-forward; WF before MC; MC
   before any paper trade. SACRED params stay pinned (`tests/test_sacred_params.py`).
5. **Gold 1H first.** Prove the edge on the anchor before touching other
   instruments. No multi-asset claims until Gold clears.

## What the evidence says we KEEP (the only positive core)
Bare with-trend breakout-retest on clean levels: Gold 10Y realistic-fill
PF **1.07**, +$1,431, Sharpe 0.16, DD 20.6% (348 trades). Positive but NOT elite.
This is the 3.0 starting baseline — the floor we must beat.

## What the evidence says we CUT (proven net-negative on realistic fills)
- ❌ Confluence scoring (FVG/liquidity/MA-cross points) — **anti-predictive**
  (conf≥2.0 → PF 0.16). Removed entirely.
- ❌ Counter-trend trades — lose money. With-trend only.
- ❌ False-breakout-level trades — lose money. Skip contested levels.
- ❌ Failed-breakout-reversal injected entries — the phantom-fill source. Removed
  (may only return as a properly-simulated limit order IF it earns its place).
- ❌ Limit-at-retest entry — tested worse than candle-close. Keep candle-close.
- ❌ Tighter retest tolerance / 3+ touch gate — both hurt. Keep 2-touch, ~0.5–0.7 ATR.

## SBRS 3.0 entry rules (proposed baseline)
1. **Bias (4H, causal):** trade only with the 4H trend. Long if bullish, short if
   bearish, skip if neutral. Use the existing causal trend series (no look-ahead).
2. **Level:** horizontal S/R with ≥2 confirmed touches.
3. **Break:** full 1H candle close beyond the level (not a wick).
4. **Retest:** price returns within RETEST_TOLERANCE_ATR of the broken level, then
   closes showing intent; enter at that candle's close.
5. **Filters:** R:R gate only (see exits). No confluence, no counter-trend, no
   false-BO entries.

## SBRS 3.0 risk (unchanged, locked)
- 1% risk/trade (portfolio sizing via SYMBOL_RISK_CAP clamp, already wired).
- SL beyond the structural retest extreme − SL_BUFFER_ATR.
- Sizing = risk$ / SL distance.

---
## DESIGN DECISIONS — RESOLVED with user (2026-06-02)

**D1 — Exits = STRUCTURAL, with room (the core 3.0 edge thesis).** Per the user:
- **Take-profit** is placed at a *significant* structural level in the trade
  direction — NOT a fixed/adaptive R-multiple. Specifically:
  - If the current trend resumed after an opposing trend, target **where that prior
    opposing trend broke / originated** (e.g., short entry on a downtrend resumption
    → TP at the level where the preceding uptrend gave way).
  - If the market was already trending, target the **previous consolidation zone or a
    historically strongly-respected level** within range, in the trade direction.
  - **Refinement (user, 2026-06-02):** for a LONG, target the prior consolidation
    **LOW** (the NEAR edge of the overhead range) or a **previous medium/big reversal
    level** — NOT the consolidation high (far edge). Symmetric for shorts (near edge
    of the range below / prior reversal). Mechanize as: nearest *significant prior
    reversal swing* in the trade direction beyond entry. TEST BOTH near-edge vs
    far-edge target modes (`tp_mode`).
  - TP is **never close to entry**; winners are given room to run. R:R is variable
    and often large — do NOT cap it at 3R.
- **Stop-loss** is placed **beyond the most recent structural swing** (e.g. below the
  most recent swing low for a long), **with room** for normal adverse movement —
  never tight. "No trade immediately moves in your predicted direction."
- Implementation thesis: detect the nearest *significant* opposing structural level
  (major swing / consolidation) via a longer-lookback swing scan for TP; structural
  swing-based SL with an adequate buffer. Fixed-3R is replaced.
- **Validation note:** because R:R is now variable, the MIN_RR=3.0 SACRED gate must
  be reconsidered for 3.0 — keep it as a *minimum acceptable* filter (skip setups
  whose structural target gives <3R) but never as the target itself.

**D2 — MA convention = SMMA > WMA is BULLISH (use the methodology doc).** Reverts the
2.0 WMA>SMMA convention (which was validated only on phantom-fill data).

**D3/D4 — Smart-money + reversal = OUT of baseline; ablate later.** Baseline 3.0 has
no FVG/liquidity/reversal. Then run ablations ON THE 3.0 STRUCTURAL-EXIT FOUNDATION:
  - +FVG (as a filter) alone
  - +liquidity sweep (as a filter) alone
  - +both together
  - +failed-breakout reversal (as a real resting-limit order, Trade 15) 
  Each must improve realistic-fill PF to be included. (User: "keep them, but leave out
  for now and ablate individually then together; apply the structural-exit logic when
  testing them too.")

**D5 — deferred:** confirmation candle at retest + session filter — revisit after the
structural-exit baseline is measured.

---
## Build & validation sequence (once spec is locked)
1. Implement 3.0 as a clean module (`src/regimes/sbrs_v3.py`), 2.0 left intact for diff.
2. Full-sample Gold 1H BT, realistic fills → must beat PF 1.07 baseline, target ≥1.5.
3. Ablate each added component (earn-your-place).
4. Only if Gold clears elite gates → walk-forward → Monte Carlo → other instruments.
5. Update canon ONLY from realistic-fill, gate-clearing results.
