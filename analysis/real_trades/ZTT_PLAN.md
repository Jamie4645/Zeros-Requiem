# Zero's True Trade (ZTT) — Strategy Decode + Build Plan

**Status:** PLANNING (pre-implementation). Awaiting council review + user go-ahead.
**Source of truth:** `analysis/real_trades/Zeros True Trade 5m - 15m.docx` (25 annotated real Gold trades).
**Scope:** Gold (XAU/USD) ONLY. All other instruments paused. Clean-slate — does NOT inherit SBRS 2.0 logic.
**Date:** 2026-06-09.

---

## 1. Decoded strategy (ground truth from 25 trades)

### Indicators (user-stated)
- **WMA(144, close)** — slow trend baseline. On 10m, 144 bars ≈ 24h (daily context line).
- **SMMA(5, close)** — fast line (≈50 min on 10m).
- **Bullish** = SMMA(5) > WMA(144) / SMMA crosses up through WMA.
- **Bearish** = WMA(144) > SMMA(5) / WMA crosses up through SMMA.
- (Consistent across all trades. NOTE: opposite labeling to old SBRS canon, but physically correct given the periods.)

### Timeframe
5m / 10m / 15m intraday. **Majority 10m (19/25).** Build TF = **10m**.

### Core setup — with-trend break & retest of a respected horizontal level
1. **Trend context:** structure (LH/LL down, HH/HL up) + price on correct side of WMA-144.
2. **Horizontal level** respected/touched **2–5 times** (the user's circles).
3. Price **breaks** the level (close beyond).
4. Price **retests** the flipped level (broken support→resistance, broken resistance→support).
5. **Enter** in breakout direction on the retest.
6. **MA cross** (SMMA/WMA) — confluence, not required.

### Stop loss
Beyond the most recent **opposing swing**:
- SHORT: above prior lower-high (the swing formed at/after the break).
- LONG: below prior higher-low / lower-low.
Structural invalidation point.

### Take profit
**3R default**, capped at nearest prior significant level (e.g. downtrend lower-high) when one sits inside 3R.

### Discipline rules (refined with user, 2026-06-09)
- **Two valid entry modes — the discriminator is STRUCTURE, not raw trend direction:**
  - **Continuation:** break-retest in the direction of the prevailing trend.
  - **Reversal (legitimate):** break-retest taken AFTER a *confirmed structural shift* — price breaks a **significant/strong opposing swing** (strong lower-high in a downtrend → reversal long; higher-high/strong level in an uptrend → reversal short). Successful examples: Tr9, Tr23, Tr24, Tr25.
  - **Blind counter-trend (blocked):** against the prevailing trend with NO confirmed structural break. The flagged losses Tr12/Tr20/Tr22 are THIS — they are noticed only because they failed; the user makes *successful* reversal trades that must NOT be lumped in with them.
  - ⇒ Phase 4 trend A/B becomes: Arm A = continuation only; **Arm B = continuation + confirmed-reversal (still blocks blind counter-trend).**
- **Level quality = clean respect, not touch count.** A level with **≥2 CLEAN touches** (wick rejections, no body-close through the level, no overlapping penetration that "disrespects" it) qualifies. Tr8 lost because the level was *disrespected* (penetrated/overlapping) before the break — not merely because it was the 2nd touch. Detector scores *clean rejections* and penalizes disrespect; raw count alone is NOT the gate.
- No retest = no trade (Tr14 = valid miss).
- Discretionary hit rate ≈ 19W / 6 (L or miss) ≈ 76%, clean 3R winners.

> **Phase-3 calibration flags (precise thresholds frozen-by-rule before replay):** (a) what makes an opposing swing "significant/strong" enough to confirm a reversal; (b) the quantitative "clean rejection vs disrespect" test (max body-penetration as a fraction of ATR, wick-rejection ratio). Both will be defined as rules, shown back to the user, then held fixed through replay.

---

## 2. Locked decisions (user, 2026-06-09)
| Decision | Choice |
|---|---|
| Timeframe | **10m primary** (5m/15m robustness later) |
| MA cross role | **Confluence, not required** |
| Counter-trend | **Configurable flag; A/B in Phase 4.** Arm A = continuation only; Arm B = continuation + *confirmed-reversal* (structural break of a strong opposing swing). BOTH arms block *blind* counter-trend. Reversal trades are legit, NOT mistakes. |
| Take profit | **3R default + structural cap** |
| WF depth | **10 years** (2016–2026; ~8–10 windows; multi-regime) |
| Calibration set | **The 25 trades only** (user confirms no fuller history). Survivorship caveat ACCEPTED; the 10Y WF carries the burden of multi-regime + honest hit-rate verification. |

## 3. To be calibrated empirically (Phase 3, not user-decided)
- Minimum touches to qualify a "respected level" (trades show 2–5).
- Level-cluster tolerance (price proximity to call touches "the same level").
- Entry trigger mechanic: limit-at-level vs candle-close-rejection (default: close-rejection; validate against the 25).
- Swing lookback/window for structure + SL anchor.
- Spread/slippage model for intraday 10m gold.

---

## 4. Build plan — 8 phases

**Operational directives:** pause all non-Gold instruments (live caps→0, disable in runner); this doc replaces all prior strategy docs; sacred-file/param locks lifted (edit freely, flag each change); both councils at planning + post-analysis; BT=1Y, WF=10Y (data permitting); document to KB+Obsidian; update CLAUDE.md.

- **Phase 0 — Data & housekeeping.** Add `10m→M10` to fetcher; probe OANDA XAU history depth at M5/M10/M15; fetch 1Y + max-available; pin 25 trades into `trades.csv` + map to candles (verify our data matches user fills, UTC+1); pause all non-Gold instruments. → data-availability report + WF-depth decision.
- **Phase 1 — Spec + council review.** Write `docs/ztt_spec.md`; convene both councils; pre-register falsifiers. → approved spec + council brief.
- **Phase 2 — Mechanize primitives (TDD).** `src/regimes/ztt.py` (clean-slate): WMA-144/SMMA-5, structure/trend classifier, multi-touch level detector, break/retest trigger, structural SL, 3R/structural TP. Pin new SACRED params with tests.
- **Phase 3 — Per-trade replay (MAKE-OR-BREAK).** Run over 25 exact windows; algo-vs-user diff per trade. Iterate until it reproduces the user's decisions (matches wins, correctly skips the flagged mistakes). If it can't → escalate, do not deploy.
- **Phase 4 — Backtest (1Y).** Realistic-fill 1Y M10 (+5m/15m robustness); A/B counter-trend flag; vs elite gates. → go/no-go.
- **Phase 5 — Walk-forward + Monte Carlo.** WF over max depth; MC tail-risk.
- **Phase 6 — Post-analysis councils.** Both councils + red-team; tier decision.
- **Phase 7 — Demo → Live (Gold only).** Port to live engine at intraday cadence; paper-gate; then live Gold only.

---

## 4b. COUNCIL REVIEW (2026-06-09) — both councils: PROCEED-WITH-CHANGES

**Arbiter council** (data, cost-skeptic, execution, falsifier, red-team, socrates) + **Philosophical council** (Popper, Munger, Taleb, Feynman, Kahneman). Mandated changes, folded into the plan:

**C1 — Data is BETTER than feared (arbiter-data: GO).** OANDA serves *native* M10 for XAU_USD back to ~2006 → **~20Y available**. 10Y WF fully feasible (16Y optional). One-line fetcher add (`'10m':'M10'`, bars/day 144). No resampling needed.

**C2 — Timezone DST trap (arbiter-data).** User stamps are UTC+1, but that's BST only. Trades in **Jan/Feb (Tr24, Tr25, Tr22, Tr23) are GMT = UTC+0** → offset 0h, not −1h. Phase 0 pinning must apply UK-DST-aware offset per trade date. Tr1 verified: 04:40 UTC+1 = 03:40 UTC bar (L=4458.52) contains entry. Daily 22:00 UTC 1h05 gap + weekend gaps; no forward-fill (good).

**C3 — Cost realism pulled FORWARD to Phase 0 (cost-skeptic + red-team + Taleb).** Build a **session-gated spread model**, not a flat slip: London/NY (06–20 UTC) ~0.4pt/side, rollover (21–23 UTC) ~1.5pt/side, Asia ~0.8pt, news ±5min ~3pt. **Hard rule: no new entries 21:00–23:00 UTC.** **Min SL floor 10pt.** Slip anchor ≥1.0pt/side for 10m gold, A/B {0.5,1.0,2.0}. Falsifier: flat-vs-session-gated PF must not differ >0.10.

**C4 — Entry = candle-close-rejection, NEVER limit-at-level (execution + Feynman).** Phantom-fill repeat risk. Engine rules to pin in Phase 2: (a) entry fires only on bar-close rejection (closes back beyond broken level after touching it); (b) if entry bar's adverse extreme breaches structural SL → failed retest, no entry, reset; (c) evaluate on bar-close only, never intrabar; (d) live runner `bar_is_closed` guard. **Entry mechanic frozen NOW, before replay** (Popper/Feynman: do not tune it to pass).

**C5 — Phantom-fill tripwire (falsifier F2).** Every backtest fill must assert `low ≤ fill ≤ high` on the fill bar AND that the retest level actually traded. Any violation = HALT. WR>80% or any single setup-type >60% of PnL = forced fill-log audit.

**C6 — Phase 3 validates ENTRY/SKIP ONLY, decoupled from exits (red-team + Socrates + Feynman).** TP narration is hindsight-contaminated (Tr16: "looks like it didn't hit TP, but it did... in the future levels"). So replay scores **direction + entry + correct-skip**, NOT exit matching. **All thresholds (touches, cluster-tolerance, swing-window) frozen by RULE before replay; max 2 re-tunes (F4).** Geometry-only entry replay <60% = KILL immediately.

**C7 — Fidelity ≠ profitability; separate verdict branches (Socrates).** Phase 3 = "can it be mechanized faithfully?"; Phase 4 = "does it pass elite gates?". A faithful-but-sub-gate result is a valid, honest *non-failure* answer with its own verdict path. Do not collapse into one go/no-go.

**C8 — Survivorship / one-regime (Kahneman + Munger + Taleb) — NEEDS USER INPUT.** The 25 are a *remembered, screenshotted* highlight reel over a single Jan–Jun 2026 gold bull ramp (~4300→5500). True hit rate unknown; forgotten scratches/skips absent. Two mitigations: (i) request the user's **complete broker statement** to de-bias the win rate; (ii) the 10–20Y WF (now feasible) supplies multi-regime stress the 25-trade calibration set lacks. The strategy must survive chop/down regimes in WF, not just the bull ramp.

**Pre-registered falsifier set F1–F6** (arbiter-falsifier) → commit to `knowledge-base/82-Pre-Registered-Falsifier-ZTT.md` before Phase 2. F1 (replay ≥15/19 entries within 0.3R + skip ≥4/5 mistakes) judged **most likely to trip**.

### Revised phase deltas
- **Phase 0 (expanded):** + DST-aware trade pinning; + build & validate the session-gated cost model (pulled forward); + verify our M10 data contains the user's fill prices; + (if user provides) ingest complete broker history.
- **Pre-Phase-2 freeze gate:** entry mechanic = close-rejection; all thresholds rule-defined; numeric OOS pass line committed. Falsifiers locked.
- **Phase 3:** entry/skip fidelity only; ≥60% geometry kill-floor; fidelity verdict separate from Phase 4 gates.
- **Phase 4:** session-gated cost mandatory; slip A/B; phantom-fill assertions on every fill.

## 4c. PHASE 0 RESULTS (2026-06-09) — COMPLETE ✅

- **Non-Gold paused** (instruction #1): `src/live/runner.py` `SYMBOLS_CONFIG` → Gold-only (others moved to `_PAUSED_SYMBOLS`); `SYMBOL_RISK_CAP` DAX/NDX/GBPUSD → 0.0000. Sacred-file lock on `risk_manager.py` lifted in `scripts/hooks/pre_edit_block_sacred.py` (legacy params file still guarded).
- **M10 wired** — `'10m'→'M10'` + bars/day 144 in `oanda_fetcher.py`. OANDA serves **native M10** (no resample).
- **Data fetched & cached:** `data/cache/oanda_gold_1y_10m.csv` (35,468 bars) + `oanda_gold_10y_10m.csv` (**354,110 bars, 2016-06→2026-06**). 10Y WF fully feasible. Clean 10-min spacing; weekend/daily-break gaps present (no forward-fill).
- **Timezone RESOLVED empirically** (`phase0/pin_trades.py`): platform = **London time** — trades on/after 2026-03-29 map at **UTC+1 (BST)**, before at **UTC+0 (GMT)**. The doc's blanket "UTC+1" is only correct in summer. 18/25 entries pin inside their candle at the correct offset.
- **⚠️ KEY FINDING — timestamps drift, prices are reliable.** Re-pinning by price: Tr11 (stated Sun Apr-26 05:50 = market closed!) really traded ~Apr 29-30; Tr25 (stated Jan-26, price 5471) really traded Jan 28-29; Tr2 (stated 17:00) really traded ~03:40 UTC. **⇒ Phase 3 must locate each setup by PRICE + STRUCTURE within a ±3-day window, NOT by exact timestamp.** Small 5m/15m misses (Tr4/16/24) are 10m-bar-boundary artifacts.
- **Cost model built & validated** (`src/regimes/ztt_costs.py`): session-gated spread. Against the 25 trades — **median cost 5.2% of risk, max 15.5%** (Tr4, 12.9pt SL at 00:20 Asia); 12 Asia / 11 London-NY / 1 NY-close / 1 rollover. Only **Tr18 hits the rollover block (and it WON)** ⇒ rollover gate kept **configurable + A/B**, not a hard exclusion. No trade below the 10pt SL floor.

## 5. Known risks (pre-identified)
- **R1 (data):** OANDA REST intraday history may be < 10Y at 10m → WF depth at risk. Probe in Phase 0.
- **R2 (cost):** Intraday spread/slippage is a larger fraction of a 10m move than a 1H move. Cost realism is make-or-break; the old engine's phantom-fill disaster is the cautionary tale.
- **R3 (fidelity):** "Respected level" + "significant" TP cap are discretionary judgments; mechanization may not capture them.
- **R4 (overfit):** Calibrating to 25 trades risks fitting noise. Phase 3 must validate the LOGIC, not curve-fit thresholds to these exact trades.
