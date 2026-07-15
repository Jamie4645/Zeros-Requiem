# ZTT (Zero's True Trade) — Mechanical Specification v1.0 (FROZEN)

**Status:** ✅ FROZEN 2026-06-09 (user signed off SACRED params + all 11 mechanization
defaults). No threshold may change without an explicit ≤2-re-tune amendment logged in
Phase 3 (Falsifier F4). Frozen before Phase 2 code — council pre-commitment gate honoured.
**Instrument:** Gold (XAU/USD) only. **Timeframe:** 10m primary.
**Derived from:** 25 real annotated trades (`analysis/real_trades/`) + Phase 0/1 geometry
(`phase0/trade_geometry.py`). Clean-slate — inherits NO SBRS 2.0 logic.

---

## 1. Indicators
| Name | Definition | Role |
|---|---|---|
| `WMA144` | WMA(close, 144) | Slow baseline / context (≈24h on 10m). **NOT a hard trend gate.** |
| `SMMA5` | SMMA(close, 5) | Fast line (≈50m). |
| `ma_momentum` | sign(SMMA5 − WMA144): +bull / −bear | **Confluence only** (present in 75% of real trades). |
| `ATR14` | ATR(14) | Volatility unit for all tolerances + buffers. |

## 2. Market structure (the real trend filter)
- **Swing pivots** via fractal: swing-high at i if `High[i]` = max over `[i−SWING_W, i+SWING_W]`; swing-low symmetric. `SWING_W` confirmed bars each side (causal: a pivot is only *known* `SWING_W` bars later — no look-ahead).
- **Trend state** from the last pivots:
  - **Downtrend:** last 2 swing-highs descending AND last 2 swing-lows descending (LH + LL).
  - **Uptrend:** last 2 swing-highs ascending AND last 2 swing-lows ascending (HH + HL).
  - **Range/undefined:** otherwise (no with-trend setups taken).

## 3. Horizontal level detection (the crux)
- A **level** = a price band touched ≥ `MIN_TOUCHES` times by swing pivots, all within `LEVEL_TOL × ATR` of each other (clustered). Resistance = clustered swing-highs; support = clustered swing-lows.
- **Touch** = a swing pivot whose extreme reaches the band.
- **Clean touch (respect)** = the pivot rejected the level: the candle **body did not close beyond** the level by more than `DISRESPECT_TOL × ATR`. A close beyond = **disrespect** (penetration).
- **Level qualifies** if: `clean_touches ≥ MIN_TOUCHES` AND `clean_touches > disrespectful_penetrations` (mostly respected). Raw count alone is NOT sufficient — this encodes the Tr8 lesson (lost on a disrespected level).

## 4. Break detection
- **Break** = a candle **closes** beyond the qualified level by > `BREAK_BUFFER × ATR` in the setup direction (continuation-short → close below support; etc.). Close-based, never intrabar wick.

## 5. Setup modes & direction filter (A/B in Phase 4)
- **Continuation:** break-retest in the prevailing structural-trend direction.
- **Confirmed reversal:** break-retest where price has **closed beyond a *significant* opposing swing** — defined as a swing extreme that was the high/low over ≥ `REVERSAL_LOOKBACK` bars (it bounded the prior trend leg). This flips structure. (Examples: Tr9, Tr23, Tr24, Tr25.)
- **Blind counter-trend (BLOCKED in both arms):** against structure with NO significant-swing break.
- **Phase 4 A/B:** Arm A = continuation only · Arm B = continuation + confirmed-reversal.

## 6. Retest + entry — FROZEN: candle-close-rejection (NEVER limit-at-level)
- After a break, within `MAX_RETEST_WAIT` bars, price returns to within `RETEST_TOL × ATR` of the broken (now flipped) level.
- **Entry fires on the CLOSE of a rejection candle**: the bar touched the flipped-level band AND closed back in the breakout direction (beyond the level on the correct side).
- **No qualifying retest within `MAX_RETEST_WAIT` → setup expires, no trade** (encodes Tr14 miss).
- **Intrabar rule:** evaluate only on bar close. If the entry bar's adverse extreme (low for long / high for short) breaches the structural SL price, it is a **failed retest → no entry, reset** (anti-phantom, per arbiter-execution).

## 7. Stop loss (structural)
- **LONG:** `SL = (swing-low formed at/after the break, i.e. the retest higher-low) − SL_BUFFER × ATR`.
- **SHORT:** `SL = (swing-high formed at/after the break, i.e. the lower-high) + SL_BUFFER × ATR`.
- **Floor:** reject the setup if `|entry − SL| < MIN_SL_DOLLARS` (cost realism; observed min real SL ≈12.9pt).
- Observed real SL distance 1.5–6.7 ATR (median 3.0) — consistent with structural anchor + small buffer, NOT a fixed multiple.

## 8. Take profit
- `TP = entry ± MIN_RR × |entry − SL|`, `MIN_RR = 3.0` (SACRED — real trades cluster at 3.00).
- **Structural cap (default ON, secondary):** if a prior significant opposing level lies between entry and the 3R target, cap TP just before it (`STRUCT_CAP_BUFFER × ATR` short of it). Rarely binds (real R:R ≈ 3.0 throughout).

## 9. Parameter table — SACRED vs FROZEN-mechanization (NEEDS USER SIGN-OFF)

**SACRED (from the user's real trading — never optimized):**
| Param | Value |
|---|---|
| `WMA_PERIOD` | 144 |
| `SMMA_PERIOD` | 5 |
| `ATR_PERIOD` | 14 |
| `MIN_RR` | 3.0 |

**FROZEN mechanization params (proposed defaults; principled + sanity-checked vs the 25 trades; ≤2 re-tunes allowed in Phase 3 per Falsifier F4):**
| Param | Proposed default | Rationale |
|---|---|---|
| `SWING_W` | 3 | Fractal pivot window each side; matches 10m swing granularity in the charts. |
| `MIN_TOUCHES` | 2 | User enters on 2+ *clean* touches (Tr3 "2x", Tr19 "3-4x"). Quality gates it, not count. |
| `LEVEL_TOL` | 0.25 ATR | Band width to cluster touches into "the same level". |
| `DISRESPECT_TOL` | 0.10 ATR | Body-close beyond level allowed before it counts as disrespect. |
| `BREAK_BUFFER` | 0.10 ATR | Close-beyond margin to confirm a real break (filters marginal pokes). |
| `REVERSAL_LOOKBACK` | 30 bars | A swing extreme over ≥30 bars is "significant" enough to confirm a reversal. |
| `RETEST_TOL` | 0.50 ATR | How close the retest must come to the flipped level. |
| `MAX_RETEST_WAIT` | 10 bars | Stale-setup expiry (no retest → no trade). |
| `SL_BUFFER` | 0.30 ATR | Buffer beyond the structural swing for the stop. |
| `MIN_SL_DOLLARS` | 10.0 | Reject setups with sub-10pt structural stops (cost realism). |
| `STRUCT_CAP_BUFFER` | 0.25 ATR | TP capped this far short of an intervening level. |

## 10. Cost & session (Phase 0 model)
`src/regimes/ztt_costs.py` session-gated spread; slip A/B {0.5,1.0,2.0}; rollover-entry block **configurable + A/B** (only Tr18 affected, and it won); `MIN_SL_DOLLARS` floor as above.

## 11. Numeric pass lines (pre-committed — see falsifiers KB 90)
- **Phase 3 (fidelity, entry/skip ONLY):** reproduce ≥15/19 winning entries (within 0.3R) AND correctly SKIP ≥4/5 flagged mistakes (Tr8,12,14-miss,20,22). Geometry-only entry replay <60% = KILL.
- **Phase 4 (profitability, realistic cost, 1Y):** PF ≥1.5, Sharpe ≥1.0, expectancy >0, ≥80 trades. PF <1.3 or negative net expectancy = KILL.
- **Out-of-sample (data outside the 25-trade dates / WF):** PF ≥1.3 AND (in-sample − OOS) PF gap ≤0.7.
- **Fidelity ≠ profitability:** a faithful mechanization that fails Phase 4 gates is an honest *non-failure* answer with its own verdict (Socrates).
