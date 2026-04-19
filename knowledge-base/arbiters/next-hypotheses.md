---
tags: [arbiters, hypotheses, backlog]
aliases: [Hypothesis Queue, Open Hypotheses]
---

# Open Hypotheses — Arbiter Queue

Each Arbiter reads this before starting work. Claim a hypothesis by changing `Status: open` → `Status: claimed by <your-name>`. Close by linking the canonical finding in `shared-findings.md`.

---

### 2026-04-16 | by: founder | for: arbiter-ablation
**Claim to test:** Re-running the MA-convention ablation test with the corrected patch (SMMA > WMA = bull) will show whether the published +$3,300 MA-convention finding from [[49-MA-Convention-Discovery]] still holds on OANDA 10Y data.
**Why it matters:** If the old convention actually performs BETTER, the premise for v2's MA rule is invalid.
**Suggested test:** `py -m tests.ablation_study --period 10y` — look at test #11 output.
**Priority:** high
**Status:** closed — see shared-findings.md 2026-04-16 | arbiter-ablation (patch leak confirmed; Round 3 PF 5.23 invalidated; corrected patch spec in arbiter-ablation-log.md)

### 2026-04-16 | by: founder | for: arbiter-forex
**Claim to test:** GBP/USD WF collapsed from 62% to 38% between the published baseline and Round 2. W7 especially (2023-10 to 2025-01) produced -$2,013. Determine whether this is: (a) session filter mis-calibrated for forex, (b) confluence threshold too loose, (c) post-Brexit regime change.
**Why it matters:** GBP/USD is the only forex candidate currently in Tier 2; if unsalvageable, drop to Tier 4.
**Suggested test:** Backtest with `CONFLUENCE_MIN_WITH_TREND = 1.5` and compare W7 specifically.
**Priority:** high
**Status:** closed — see shared-findings.md 2026-04-17 arbiter-forex (Round 5 post-mortem)

### 2026-04-16 | by: founder | for: arbiter-risk
**Claim to test:** NASDAQ full-backtest PF 4.53 triggers the >3.0 red-flag per CLAUDE.md, even though WF average is 1.56. Is this a compounding/survivorship artefact, a data-quality issue, or a real regime-specific edge?
**Why it matters:** Before promoting NASDAQ to primary live candidate, rule out data leakage.
**Suggested test:** Run the backtest using non-compounding fixed-dollar sizing and compare final PnL to per-window sum.
**Priority:** high
**Status:** closed by arbiter-risk 2026-04-16 — compounding analytically excluded (1.01x PF movement only). Root cause: regime-concentration in one high-volatility window. WF-avg PF 1.56 is the operative figure. See shared-findings.md.

### 2026-04-16 | by: founder | for: arbiter-regime
**Claim to test:** Gold's Sharpe 0.64 on the 10Y run masks a regime split — W5 (2021-04 to 2022-07) and W7 (2023-10 to 2025-01) both produced negative returns, suggesting a specific regime where SBRS 2.0 underperforms.
**Why it matters:** If we can classify and avoid that regime, Gold's WF consistency could lift from 62% toward 75%+.
**Suggested test:** Run volatility percentile classifier on each WF window; cross-reference with PnL.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: founder | for: arbiter-execution
**Claim to test:** Session filter removes 212 of 413 baseline Gold trades (50% reduction) but lifts net profit by 52%. Hypothesis: the session filter is mainly removing 16:00–20:00 GMT NY-afternoon entries. Is there a sub-session (e.g., specifically the 14:30 NFP window or post-FOMC hours) that is MORE profitable if kept?
**Why it matters:** Could tune session filter from hour-level to minute/event-level.
**Suggested test:** Run with session filter disabled and tag each trade by hour — find which specific hours are net-negative.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: founder | for: arbiter-crypto
**Claim to test:** BTC/ETH showed PF 1.59/1.63 on 2Y backtests but have no WF validation. With the v2.0 FVG downweight, hypothesis is crypto performance improves similarly to Gold (FVG over-fires in 24/7 markets).
**Why it matters:** If crypto post-change shows PF ≥1.8, push for 5Y+ data sourcing to enable WF.
**Suggested test:** Re-run BTC and ETH 2Y backtests with new FVG weight.
**Priority:** medium
**Status:** closed — see shared-findings.md 2026-04-16 arbiter-crypto. Hypothesis rejected: PF degraded (BTC 1.59→1.31, ETH 1.63→1.21). FVG downweight net-negative for crypto.

### 2026-04-16 | by: founder | for: arbiter-data
**Claim to test:** Published Gold baselines (Sharpe 1.77, 2,252 trades) were produced on Yahoo data. Round 2 uses OANDA. Hypothesis: a material part of the performance gap is data-source drift, not strategy drift.
**Why it matters:** If true, the published baselines aren't actually achievable on our current data source — tier rankings need adjustment.
**Suggested test:** Run the exact same v2 build on a Yahoo-sourced Gold 10Y dataset and compare.
**Priority:** high
**Status:** open

### 2026-04-16 | by: founder | for: arbiter-ablation + arbiter-risk + arbiter-data
**Claim to test:** Round 3 ablation test #11 "Old MA Convention (SMMA>WMA=bull)" produced PF 5.23 / $206,367 / Sharpe 2.33 on 10Y Gold OANDA — vs baseline $33,912. This is +508.5%. PF 5.23 triggers CLAUDE.md red-flag >3.0 threshold. Investigate whether this is: (a) a test-patch leak (only `check_ma_cross` is replaced; rest of strategy still uses new convention), (b) genuine edge reversal on OANDA data vs the Yahoo-era +$3,300 [[49-MA-Convention-Discovery]], (c) overfit to 2016-2026 regime.
**Why it matters:** If genuine, this could be the largest edge uplift of the entire project AND a reversal of a core SBRS 2.0 decision. If spurious, we need to know before anyone acts on it.
**Suggested test:** (1) Walk-forward on OLD convention, 10Y Gold OANDA. (2) Walk-forward on OLD convention for DAX, NASDAQ, GBP/USD. (3) Re-run same ablation on Yahoo 10Y Gold to compare. (4) Audit the ablation patch for leakage (is anything else using the NEW convention during an OLD-convention test?).
**Priority:** HIGH
**Status:** partially closed — patch-leak portion closed by arbiter-risk (Round 4, 2026-04-16): confirmed artefact, patch covers only 1 of 4 MA callsites. PF 5.23 invalid. Full clean 4-callsite patch required before WF re-test (see arbiter-risk log + shared-findings.md). arbiter-data sub-task (OANDA vs Yahoo) remains open.

### 2026-04-16 | by: founder | for: arbiter-execution
**Claim to test:** Round 3 ablation shows No-Session-Filter variant produced +$16,443 (+48.5%) on 10Y Gold post-change — reversing the Round 2 finding that session filter was -52%. Hypothesis: session filter was masking FVG-at-1.0 over-fire; now that FVG is at 0.5, the session filter is suppressing good trades.
**Why it matters:** If true, removing the session filter is the single biggest lift available to Gold. If false, we need to know why it flipped.
**Suggested test:** Walk-forward with session filter ON vs OFF on same post-change code. 8 windows each. Accept the winner only if WF consistency ≥75% AND Round 4 ablation re-confirms.
**Priority:** HIGH
**Status:** open

### 2026-04-16 | by: founder | for: arbiter-forex
**Claim to test:** Post-change GBPUSD WF shows 7/8 profitable (up from 5/8 baseline) with W7 worst still -$1,072 (improved from -$2,013). Is the residual W7 loss now small enough to promote GBP/USD back to Tier 2 "validated needs more data"?
**Why it matters:** GBP/USD has the highest single-test PF of any instrument; unlocking it would add a non-correlated FX strategy to the portfolio.
**Suggested test:** Re-run GBPUSD walk-forward post-retry (current run had some OANDA 502 partials). Overlay W7 with regime labels (coordinate with arbiter-regime).
**Priority:** medium
**Status:** closed — see shared-findings.md 2026-04-17 arbiter-forex (Round 5 post-mortem)

---

*(Arbiters append new hypotheses below this line.)*

### 2026-04-16 | by: arbiter-forex | for: arbiter-forex (next session)
**Claim to test:** CONFLUENCE_MIN_WITH_TREND = 1.5 applied as a forex-scoped override (not global) will improve GBP/USD W7 PnL by removing minimal-evidence setups (FVG 0.5 + MA 0.5 = 1.0) while keeping high-quality setups (Liquidity 1.0 + any partial). EUR/USD and USD/JPY expected to improve proportionally.
**Why it matters:** If W7 turns positive or narrows significantly, GBP/USD can progress toward Tier 1. If EUR/USD/JPY improve, two Tier 3 pairs may approach Tier 2.
**Suggested test:** Modify sbrs_v2.py to add CONFLUENCE_MIN_WITH_TREND_FOREX = 1.5 (separate constant, forex asset_class branch only). Run WF for GBP/USD, EUR/USD, USD/JPY. Report W7 specifically for GBP/USD. Do NOT change CONFLUENCE_MIN_WITH_TREND globally. Requires user approval before any code change.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-forex | for: arbiter-risk
**Claim to test:** GBP/USD Monte Carlo (baseline: 73% prob 20% DD) has not been rerun post-change. Post-change WF improvement (5/8 to 7/8) may substantially reduce MC risk profile.
**Why it matters:** MC is the gating criterion for GBP/USD Tier 1 promotion and paper trade approval. Cannot proceed without it.
**Suggested test:** Run MC on GBP/USD post-change (FVG 0.5, DD cap 0.20, sbrs_v2 default). 10,000 simulations. Report prob(20% DD). Target: <5% for Tier 1.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-forex | for: arbiter-regime
**Claim to test:** GBP/USD W7 (2023-10 to 2025-01) ATR percentile behaviour: was GBP/USD ATR below the 25th percentile for sustained stretches in W7? If so, the ATR filter (ATR_PCTILE_ENABLED_FOREX = True) was blocking valid BoE-resolution setups.
**Why it matters:** If ATR filter is blocking good trades in low-vol macro compression windows, a forex-specific ATR threshold (e.g., 15th pctile instead of 25th) could recover edge without raising confluence bar.
**Suggested test:** Compute hourly ATR percentile distribution for GBP/USD 2023-10 to 2025-01. Flag any sustained sub-25th-pctile stretches. Cross-reference with W7 trade count (if trades/week drops sharply, ATR filter is the gatekeeper).
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-forex | for: arbiter-data
**Claim to test:** EUR/USD and USD/JPY post-change WF has not been run. Confirm post-change WF for both pairs when OANDA API is stable.
**Why it matters:** Cannot reclassify EUR/USD or USD/JPY without post-change numbers. Current Tier 3 classifications are based on pre-change data.
**Suggested test:** /walk-forward EURUSD=X 1h (or OANDA symbol) and /walk-forward USDJPY=X 1h post-change. Report PF, Sharpe, WF consistency, and W7 specifically.
**Priority:** medium
**Status:** open


### 2026-04-16 | by: arbiter-gold | for: arbiter-execution
**Claim to test:** Post-change Gold backtest per-direction breakdown will show whether the long/short WR gap (pre-change: longs 45.6% vs shorts 41%) has narrowed after FVG downweight 1.0→0.5. FVG over-fires preferentially in trending (bullish) Gold conditions, so downweight should disproportionately remove weak long signals.
**Why it matters:** If gap narrows, shorts are viable co-contributors to edge and no directional filter is needed. If gap persists, a long-bias filter may unlock additional PnL.
**Suggested test:** `py main.py --strategy sbrs_v2 --instrument GC=F --period 10y --direction-breakdown` or equivalent trade-log extraction split by direction. Compare WR and PF per direction to pre-change baseline.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-gold | for: arbiter-data
**Claim to test:** Gold post-change WF 8/8 result was produced with OANDA 502 partials on the BT run. A clean re-fetch when the API stabilises may produce a different window composition or worst-window result. The +$154 worst window is thin enough that one bad re-fetch could flip it to 7/8.
**Why it matters:** If clean re-run confirms 8/8, Gold is canon at 100% WF consistency. If it drops to 7/8 it is still Tier 1 (≥75%). Either way the result must be clean before being cited in portfolio decisions.
**Suggested test:** Re-run `py main.py --strategy sbrs_v2 --instrument GC=F --walk-forward --period 10y` after OANDA API stabilises. Record worst window PnL and compare to current +$154 provisional figure.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-gold | for: arbiter-regime
**Claim to test:** W5 (2021-04 to 2022-07) and W7 (2023-10 to 2025-01) were the two pre-change failing windows. Post-change they are now positive. Confirm via direct window-level PnL extraction that these specific windows flipped, not other windows, to canonise the DD cap as the mechanism.
**Why it matters:** If a different pair of windows flipped positive (and W5/W7 were already borderline), the narrative changes — it may be the FVG downweight, not the DD cap, that drove the recovery.
**Suggested test:** Extract per-window PnL from pre-change logs (if available in /tmp/) and compare window-by-window to post-change. Label W5 and W7 explicitly.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-indices | for: arbiter-risk
**Claim to test:** The engine's slippage formula (`apply_slippage` in risk_manager.py) uses `slippage_pips * 0.01` for any asset with price >10. At NASDAQ prices of 15,000-20,000 index points, this produces slippage of ~$0.015 per trade — negligible relative to actual index spread/slippage of 0.5-2 index points ($5-$20 per contract). Hypothesis: index slippage is being modelled at ~100x too low, artificially inflating PF for DAX and NASDAQ.
**Why it matters:** If true, NASDAQ and DAX real-world PF will be meaningfully lower than reported. Could drop both below Tier 1 threshold in a properly calibrated model. Critical to check before live deployment.
**Suggested test:** Calculate correct slippage for NASDAQ (typical spread + market impact = ~1 NQ point = ~$0.25 per share equivalent for index). Re-run NASDAQ and DAX full BT with corrected slippage. Compare PF delta.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-indices | for: arbiter-data
**Claim to test:** NASDAQ WF fetch failed with OANDA 502 in the post-change run. The pre-change WF was 88% (7/8) on what is now known to be a potentially under-slipped model. Retry the NASDAQ WF when OANDA API recovers and confirm post-change consistency score.
**Why it matters:** NASDAQ cannot be confirmed as Tier 1 until a complete post-change WF run (all 8 windows, no partial fetches) is available.
**Suggested test:** `/walk-forward ^IXIC 1h` using cached IBKR data. Report all 8 windows. Accept Tier 1 only if ≥75% profitable and avg WF PF ≥1.5.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-indices | for: arbiter-indices (self, next session)
**Claim to test:** NASDAQ "improving edge over time" (+$504/window slope per CLAUDE.md) is a real regime characteristic OR a compounding artefact amplified at the walk-forward level due to growing window PnL as equity grows. Since WF resets capital each window, the slope should be clean. But confirm by checking whether the slope is present when using non-compounding fixed-dollar sizing within each window.
**Why it matters:** If the slope is genuine, NASDAQ edge is getting stronger and live deployment has a tailwind. If it is a within-window compounding artefact, the edge is flat and the slope is noise.
**Suggested test:** Re-run NASDAQ WF with flat fixed-dollar per-trade PnL (position size = constant, not equity-scaled) and check edge_degradation field from WalkForwardResult.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-crypto | for: arbiter-crypto (future session)
**Claim to test:** Per-asset FVG weight (crypto class restored to 0.75 or 1.0 while Gold/forex stays at 0.5) will recover BTC/ETH PF toward pre-downweight levels without re-introducing the Gold over-fire problem.
**Why it matters:** FVG downweight is the single factor that degraded crypto from PF 1.59/1.63 to 1.31/1.21. If the weight is asset-class-switchable in code, this is a low-risk recovery. If not, requires engine change (ask-first rule applies).
**Suggested test:** Check whether `sbrs_v2.py` has an asset-class branch for confluence weights. If yes, set `CONFLUENCE_SCORE_FVG_CRYPTO = 0.75` and re-run 2Y BTC/ETH. Compare PF and trade count. Only proceed to 5Y+ sourcing if PF ≥1.8.
**Priority:** low (data constraint — 2Y only makes further tuning premature; unblock by sourcing 5Y+ Binance data first)
**Status:** open

### 2026-04-16 | by: arbiter-crypto | for: arbiter-data
**Claim to test:** Binance API can deliver 5Y+ BTC/ETH 1H data needed for WF validation. Confirmed working at 2Y (17,520 bars via 10 requests). Extending to 5Y (43,800 bars) requires verifying Binance rate limits and pagination handling in `src/data/fetcher.py`.
**Why it matters:** Without 5Y+ data, no walk-forward is possible for crypto and the asset class cannot move beyond Tier 3. 5Y would enable 4 WF windows (minimum); 7Y+ preferred for 8-window standard.
**Suggested test:** Inspect `src/data/fetcher.py` Binance fetch logic — confirm max bars per request, pagination, and whether period='5y' is supported. If not, extend manually. Verify data availability on Binance for BTC (available from 2017) and ETH (available from 2017).
**Priority:** medium (prerequisite for all future crypto WF work)
**Status:** open

### 2026-04-16 | by: arbiter-ablation | for: arbiter-ablation (Round 5)
**Claim to test:** A fully corrected three-callsite MA-convention patch (covering `check_ma_cross` + `compute_4h_context` + engine exit blocks) will produce a materially different result than Round 3's partial-patch PF 5.23 / $206,367. The true old-convention PnL is unknown until all three callsites are simultaneously flipped.
**Why it matters:** If the corrected run still produces PF >3.0, it is a red-flag candidate for walk-forward escalation and could challenge the SBRS 2.0 MA premise. If PF falls below 1.5, Round 2 canon (new convention = better) is fully reinstated.
**Suggested test:** Implement `_USE_OLD_MA_CONVENTION_FULL` flag that patches: (a) `v2_module.check_ma_cross` — existing patch kept; (b) `v2_module.compute_4h_context` — monkey-patch to invert cross conditions (SMMA crossing above WMA = bullish); (c) monkey-patch engine exit function `_check_ma_cross_inline` and the two inline exit blocks via a module-level flag in `engine.py`. Then run `py -m tests.ablation_study --period 10y`. Compare test #11 result to Round 3's $206,367 baseline.
**Priority:** HIGH
**Status:** open

### 2026-04-16 | by: arbiter-ablation | for: arbiter-ablation (Round 5)
**Claim to test:** If the corrected full patch produces PF >2.0 on Gold 10Y OANDA, the finding must be replicated on DAX and NASDAQ before escalation — cross-instrument confirmation is required per charter (cannot claim convention reversal from single instrument).
**Why it matters:** MA convention is a sacred-parameter-adjacent decision affecting all instruments. Cross-instrument validation gates the escalation path.
**Suggested test:** Run corrected full-patch ablation on DAX (^GDAXI) and NASDAQ (^IXIC) 10Y OANDA data. Require PF uplift in SAME direction on both before escalating to walk-forward.
**Priority:** medium (blocked on Round 5 corrected-patch result)
**Status:** open

### 2026-04-16 | by: arbiter-regime | for: arbiter-forex
**Claim to test:** All 3 GBPUSD losing windows (W1/W2/W7) have WR <= 35.6%; all 5 winning windows have WR >= 36.0%. Hypothesis: tightening the confluence threshold from 1.0 to 1.5 (with-trend) will raise WR above 36% in the losing windows by removing marginal setups, converting at least 2 of the 3 losers to profitable.
**Why it matters:** If confluence threshold explains the WR collapse, GBPUSD can be promoted toward Tier 2 validated. If not, GBPUSD may have an unfixable FX-specific regime problem.
**Suggested test:** Re-run GBPUSD WF with `CONFLUENCE_MIN_WITH_TREND = 1.5`. Report per-window WR and PnL. Accept only if >= 6/8 windows profitable AND worst-window PnL > -$500.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-regime | for: arbiter-forex (with arbiter-regime cross-check)
**Claim to test:** GBPUSD W7 (2023-10-15 to 2025-01-15) sits at 17th vol percentile (LOW regime, ATR/price=0.696%), lowest of any GBPUSD window. Hypothesis: a GBP-specific vol floor — skip new entries if ATR/price < 0.72% (30th pctile) — would have filtered W7's entry conditions without substantially reducing trades in the 5 profitable windows.
**Why it matters:** A vol-floor filter targeting GBP specifically (not Gold/DAX, which are regime-robust) could lift GBPUSD WF from 62% to 75%+ without overfitting if it generalises to W1 (HIGH vol, 78th pctile — which also lost). Note: W1 fails the vol-floor in the opposite direction, so the filter alone cannot explain both W1 and W7 losses. Test must be honest about this.
**Suggested test:** Backtest GBPUSD with entry gate: `skip if ATR(14)/price < 0.0072`. Report per-window trades and PnL. If W1 and W2 are not helped, discard filter — two losing windows in non-LOW regime means this is instrument-specific WR collapse, not vol regime.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-risk | for: arbiter-data
**Claim to test:** NASDAQ full-backtest PF 4.53 is driven by fat-tail wins concentrated in one or two walk-forward windows (likely the 2020-2022 high-volatility period). Compounding and duplicates have been ruled out analytically.
**Why it matters:** If confirmed, it validates NASDAQ as WF-PF 1.56 (Tier 1). If a different mechanism is found (data error, price-spike feed anomaly), NASDAQ may need tier review.
**Suggested test:** Pull the NASDAQ trade-level log from the full backtest run. Calculate per-trade PnL. Identify which calendar period produced the 5.47x avg_win/avg_loss implied by PF 4.53. Cross-reference with known market events.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-risk | for: arbiter-ablation
**Claim to test:** A coherent old-convention test (SMMA>WMA=bull) must patch ALL four MA callsites: check_ma_cross (sbrs_v2.py:360), compute_4h_context (sbrs_v2.py:219-222), _check_ma_cross_inline (engine.py:410), and manage_sbrs_v2_trade (engine.py:340-348). The current patch covers only one.
**Why it matters:** PF 5.23 from the incomplete patch is an artefact. A clean 4-callsite test is the only valid way to determine whether the MA convention reversal is genuine. If the clean test produces PF <3.0 and WF consistency <75%, the current convention is confirmed correct.
**Suggested test:** Build a `convention='old'` flag in sbrs_v2.py and engine.py. Run full 10Y WF (8 windows) on Gold OANDA under both conventions. Accept old convention only if WF consistency >=75% AND PF <3.0 on the single BT (i.e., plausible, not artefactual).
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-risk | for: arbiter-monte-carlo
**Claim to test:** Post-change per-strategy Monte Carlo for Gold, DAX, and NASDAQ has not been run (OANDA 502 prevented it in Round 4). The portfolio-level Prob(20%DD) estimate of 0.0% uses WF-avg parameters and normal shocks only.
**Why it matters:** Per-strategy MC Prob(20%DD) values feed into the portfolio-level benchmark. Pre-change Gold was at 25.9% — far above 5%. The Layer-2 fix likely pushed it below 5%, but this must be confirmed.
**Suggested test:** Re-run /monte-carlo on Gold, DAX, NASDAQ post-change code when OANDA API is available. Report individual Prob(20%DD) and feed into portfolio-level correlated simulation.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-data | for: arbiter-execution
**Claim to test:** `is_session_blocked()` in `sbrs_v2.py` reads `timestamp.hour` directly. Yahoo returns America/New_York timestamps; OANDA returns UTC. This causes 18.9% of bars to be misclassified as NOT blocked when they should be (NY afternoon 16:30-21:00 GMT). Fix: change to `timestamp.tz_convert('UTC').hour` (with fallback for tz-naive). Verify the fix does not change OANDA results (OANDA is already UTC) and quantify the trade count change on OANDA 10Y Gold.
**Why it matters:** Session filter accounts for ~52% of Gold's net profit (Round 2 ablation). A 18.9% misclassification rate on non-OANDA data undermines all prior Yahoo-sourced ablations. Even on OANDA data, the bug is a latent risk if the source ever changes.
**Suggested test:** (1) Apply UTC conversion fix to `is_session_blocked()`. (2) Re-run Gold 10Y WF before and after. (3) Confirm OANDA trade counts unchanged (expected: 0 delta). (4) Document fix in shared-findings.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-data | for: arbiter-data (self, next session)
**Claim to test:** IBKR caches for DAX (^GDAXI) and NASDAQ (^IXIC) are 27 days stale (last bar 2026-03-20). Before the next DAX/NASDAQ walk-forward run, refresh the cache. Verify bar counts post-refresh: expect DAX ~23.8k bars (adding ~1k), NASDAQ ~18.5k bars.
**Why it matters:** Stale caches mean the last 27 days of market data are missing from walk-forward Window 8 (most recent). This could bias the latest window's results if it covers a live-trading period.
**Suggested test:** Run IBKR cache refresh (requires TWS running), then re-check bar counts and date ranges.
**Priority:** medium
**Status:** open

### 2026-04-16 | by: arbiter-data | for: arbiter-ablation
**Claim to test:** The MA-convention Round 3 ablation (PF 5.23, $206k) cannot be compared to a Yahoo 10Y baseline because Yahoo 1H caps at 2Y for GC=F. The only valid 10Y ablation comparison is OANDA-vs-OANDA. The arbiter-ablation should audit the test patch code to confirm whether the ablation patch is truly swapping both the trend check AND the exit check, or only one of them (mixed-convention leak).
**Why it matters:** If the patch only replaces `check_ma_cross` exit logic but leaves the entry-side trend convention unchanged, the test is measuring a semi-reversal, not a full convention swap — which could artificially inflate performance.
**Suggested test:** Print the exact code diff applied in ablation test #11. Verify WMA>SMMA=bull vs SMMA>WMA=bull is consistently applied in: (1) `check_trend_context_4h`, (2) `check_ma_cross` exits, (3) confluence scoring MA component.
**Priority:** high
**Status:** open

### 2026-04-16 | by: arbiter-execution | for: arbiter-ablation
**Claim to test:** Session filter removal (Gold 16-23 GMT block eliminated) is supported by WF evidence (7/8 windows favour OFF, both 8/8 profitable, +$5,177 cumulative). Requires Round 4 ablation re-confirmation before production change.
**Why it matters:** Removing the filter is the single largest available PnL lift on Gold (+31% cumulative, +$5,177 over 10Y). It is also a reversal of a previously confirmed finding and touches a "sacred-adjacent" guardrail — it must be re-confirmed by ablation, not just WF.
**Suggested test:** Run Round 4 ablation on Gold 10Y OANDA post-change code. Config A = current (filter ON). Config B = filter OFF. Confirm B beats A and that PF of B does not trigger the >3.0 red flag. Also confirm WF consistency of B on a fresh fetch (OANDA may have cached prior run).
**Priority:** HIGH
**Status:** open

### 2026-04-16 | by: arbiter-execution | for: arbiter-execution (future session)
**Claim to test:** Hour-of-day buckets for hours 16-23 GMT are all net positive in aggregate but none individually meets the 50-trade minimum (max 45 trades in h=16). With more historical data (15Y+ if available) or by pooling across multiple instruments (DAX, GBP/USD), can we reach 50-trade/bucket validity for sub-hour filter decisions?
**Why it matters:** Would allow principled hour-level filter tuning rather than blunt remove-all-or-block-all. Especially relevant for Asia hours (h=22-23 only +$517 combined, WR 31%) vs NY hours (h=17-19, WR 50-62%).
**Suggested test:** Re-run hour-of-day analysis on DAX 10Y and NASDAQ 10Y filter-OFF. Pool with Gold. Check if any hour consistently net-negative across instruments.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-crypto | for: arbiter-data
**Claim to test:** Binance 5Y+ infrastructure is confirmed working (code audit complete — see shared-findings.md 2026-04-17). Arbiter-data should execute the fetch to build the 9Y (2017-present) BTC/ETH/SOL 1H caches without any code changes.
**Why it matters:** All crypto WF validation and per-asset FVG weight testing is blocked on data. This is the single unblocking action for the entire crypto domain.
**Suggested test:** Run `py -m src.data.binance_fetcher` (calls `fetch_binance` for BTC-USD and ETH-USD at '5y' by default). Extend to 'max' for BTC history back to 2017. Verify bar count: expect ~78,840 bars for BTC 9Y 1H. Also run for SOL-USD (SOL has never been validated at all). Cache lands in `data/cache/BTCUSD_1h_binance.csv` etc.
**Priority:** HIGH (prerequisite for all crypto advancement)
**Status:** open

### 2026-04-17 | by: arbiter-crypto | for: arbiter-crypto (future session, after data sourced)
**Claim to test:** Per-asset FVG weight (CONFLUENCE_SCORE_FVG_CRYPTO = 0.75 or 1.0, while Gold/forex stays at 0.5) will recover BTC PF from 1.31 toward pre-downweight 1.59+, and ETH from 1.21 toward pre-downweight 1.63+, without re-introducing the over-fire problem seen in Gold. This test is gated on 5Y+ Binance data being available.
**Why it matters:** FVG downweight is the confirmed sole driver of crypto degradation. Per-asset weight is the minimal-footprint fix. If BTC recovers to PF ≥1.5 on 5Y WF, it re-enters Tier 2 consideration. If ETH recovers DD below 15%, it exits Tier 4.
**Suggested test:** After 5Y+ data sourced — (1) Check whether sbrs_v2.py has an asset-class branch for confluence weights. If not, add `CONFLUENCE_SCORE_FVG_CRYPTO` constant with an `asset_class == 'crypto'` branch (ask-first rule applies — requires user approval before code change). (2) Test at 0.75 first, then 1.0 if 0.75 insufficient. (3) Run 5Y WF (minimum 4 windows, prefer 8 if data allows). Accept recovery only if PF ≥1.5 AND DD <15% AND ≥4 windows profitable.
**Priority:** medium (blocked on data sourcing)
**Status:** open — blocked on arbiter-data Binance 5Y+ fetch

### 2026-04-17 | by: arbiter-crypto | for: arbiter-crypto (future session, after data sourced)
**Claim to test:** SOL-USD has never been validated at any level. Infrastructure supports it (SOLUSDT mapped in binance_fetcher.py). After 5Y+ cache is built, run a baseline 2Y BTC-equivalent backtest on SOL to check if any edge exists before committing to full WF resources.
**Why it matters:** SOL is in scope per arbiter-crypto charter. One zero-cost scout run determines whether SOL warrants further investigation or joins S&P/AUD in the reject pile.
**Suggested test:** Run `py main.py --symbol SOL-USD --interval 1h --period 2y --strategy sbrs_v2`. Report PF, Sharpe, DD, trade count. Minimum bar for further investigation: PF ≥1.3 AND DD <20% AND trades >100.
**Priority:** low (SOL never validated; BTC/ETH recovery takes precedence)
**Status:** open — blocked on arbiter-data Binance 5Y+ fetch

### 2026-04-17 | by: arbiter-gold | for: arbiter-risk
**Claim to test:** Gold MC Prob(20%DD) of 3.08% was computed on the 643-trade filter-ON distribution. Session filter removal adds ~94 trades, changing the per-trade PnL distribution. Re-run MC on the 737-trade filter-OFF Gold post-change run to confirm whether the figure stays below 5% (elite gate).
**Why it matters:** Paper-trade approval and the 0.5% risk sizing recommendation rest on MC passing. If filter-OFF MC moves above 5%, risk sizing must be reduced.
**Suggested test:** `/monte-carlo GC=F 1h 10y` post-change with `SESSION_BLOCK_START_HOUR = 99`. Report Prob(20%DD), Prob(profitable), P95/P99 max DD. Compare to 3.08% baseline.
**Priority:** medium (current evidence passes — not urgent but should be confirmed before live deployment)
**Status:** open

### 2026-04-17 | by: arbiter-gold | for: arbiter-data
**Claim to test:** OANDA Gold 1H bar construction (mid-price) vs Yahoo/COMEX settlement creates structural differences in swing detection (swing highs/lows depend on bar High/Low ranges). OANDA bars may have narrower high-low ranges due to spread-adjusted mid-pricing, reducing the number of valid swing points detected by SWING_LOOKBACK=20, SWING_WINDOW=3. This could explain part of the 737 vs 2,252 trade count gap.
**Why it matters:** If OANDA bar construction suppresses swing detection, the SBRS 2.0 edge metric (PF 2.14, Sharpe 1.50) is computed on an under-sampled signal pool. The true OANDA-achievable edge may be higher or different once the bar construction effect is characterised.
**Suggested test:** (1) Compare avg (High-Low) range per bar: OANDA Gold vs Yahoo GC=F on same 2Y overlap period. (2) Count swing highs/lows detected per 1000 bars on each source. (3) Compare SBRS 2.0 setup count (pre-entry-filter) on matched data. Report delta.
**Priority:** high (this is the single largest unresolved data-source risk on Gold)
**Status:** open

### 2026-04-17 | by: arbiter-gold | for: arbiter-execution
**Claim to test:** Long/short WR gap (pre-change: longs 45.6% WR vs shorts 41% WR) has not been re-measured on the Round 5 post-change 737-trade dataset. FVG downweight should disproportionately reduce over-fired long signals in trending Gold conditions, potentially narrowing the gap. If gap persists above 5pp, a long-bias filter or short-specific confluence floor may be warranted.
**Why it matters:** Shorts currently contribute ~12% of Gold profit (PF 1.09 vs 1.77 for longs). If the gap has not narrowed, shorts are a drag on aggregate PF and a potential source of future drawdown in bear-market regimes.
**Suggested test:** Extract per-direction WR and PF from the 737-trade post-change Gold trade log. Compare to pre-change baseline (longs 45.6%/PF 1.77 vs shorts 41%/PF 1.09). Report delta. If gap remains >5pp, flag to arbiter-gold for long-bias filter hypothesis.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-gold | for: arbiter-ablation
**Claim to test:** With session filter now OFF and MA convention closed, RETEST_TOLERANCE_ATR = 0.5 has never been tested in isolation on OANDA filter-OFF data. The Round 2 ablation note references 0.7 ATR for Gold longs, but this was on pre-FVG-downweight, pre-DD-cap-fix, filter-ON data. Filter removal opens NY-afternoon and Asia hours where retest behaviour may differ from London session. A monitoring ablation (not optimisation) should confirm whether 0.5 still maximises PF in the filter-OFF regime.
**Why it matters:** RETEST_TOLERANCE_ATR is a sacred parameter — it cannot be changed without explicit user approval. But if the filter-OFF regime reveals a material sensitivity at ±10% (0.45 or 0.55), that information should be surfaced to the user as an awareness flag, not a recommendation to change.
**Suggested test:** Run a 3-config ablation ONLY: {0.45, 0.50, 0.55} × RETEST_TOLERANCE_ATR on Gold 10Y OANDA filter-OFF post-change. Report PF and trade count. Do NOT change production value regardless of outcome — result is monitoring data only. Requires framing as an informational test, not an optimisation.
**Priority:** low (sacred parameter — informational only)
**Status:** open

### 2026-04-17 | by: arbiter-forex | for: arbiter-risk
**Claim to test:** GBP/USD Monte Carlo post-Round-5 (confluence-1.5 live, FVG 0.5, DD cap 0.20) will show Prob(20%DD) < 5%, clearing the final gate for Tier 1 promotion and paper trade approval.
**Why it matters:** MC is the only remaining mandatory gate. Prior baseline was 73% Prob(20%DD) on a completely different parameter set (1,323 trades, no confluence-1.5). With 274 trades and tighter filter, the risk profile is structurally different and cannot be extrapolated from the baseline. Cannot approve paper trade without this number.
**Suggested test:** Run /monte-carlo GBPUSD=X 1h on post-Round-5 code (sbrs_v2, CONFLUENCE_MIN_WITH_TREND_FOREX=1.5 confirmed live at sbrs_v2.py:118). 10,000 simulations minimum. Report Prob(20%DD) and Prob(profitable). Target: <5% for Tier 1 gate.
**Priority:** high (CRITICAL — gates paper trade decision)
**Status:** open

### 2026-04-17 | by: arbiter-forex | for: arbiter-regime
**Claim to test:** ATR_PCTILE_ENABLED_FOREX = True (25th percentile, 100-bar lookback) may be over-suppressing valid GBP/USD entries during BoE hold cycles where sustained low-vol deflates the rolling baseline. Specifically: does ATR_PCTILE_THRESHOLD = 15 recover meaningful trade count in W7 (2023-10 to 2025-01) without substantially increasing W7 net-loss exposure?
**Why it matters:** W7 residual is -$293 after two rounds of improvement. A third independent suppressor (ATR filter over-reaching) could explain the residual. If the threshold change recovers net-positive trades in W7, the filter is miscalibrated for BoE-driven forex regimes. Applies equally to USD/JPY post-BoJ-intervention normalisation windows.
**Suggested test:** Run GBP/USD W7 backtest (2023-10-15 to 2025-01-15) with ATR_PCTILE_THRESHOLD = 15, then 20, then 25 (current). Report trade count and net PnL per threshold. Accept lower threshold only if net PnL in W7 is higher AND W7 trade count increase is consistent across multiple non-W7 windows (to avoid overfitting).
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-forex | for: arbiter-data
**Claim to test:** USD/JPY 5Y+ historical data (OANDA or IBKR) is prerequisite for a statistically valid walk-forward (currently only 23 trades on 2Y data). Confirm whether OANDA API provides USD/JPY history back to 2016 (enabling 10Y WF) or whether IBKR is required.
**Why it matters:** USD/JPY Round 5 WF showed 88% consistency and PF 1.48 — both near Tier 1 bar — but on 23 trades the result is not actionable. 5Y+ data enabling ≥500 trades is the gating requirement.
**Suggested test:** Fetch USD/JPY 1H from OANDA with period=10y. Check bar count and earliest date. If OANDA covers back to 2016, run full WF immediately. If not, use IBKR (TWS required). Report bar count, date range, and NaN rate before running WF.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-forex | for: arbiter-forex (self, future session)
**Claim to test:** EUR/USD W7 -$806 persists even with confluence-1.5 applied. EUR/USD Sharpe 0.38 on WF-avg is too thin for Tier 2. Hypothesis: EUR/USD edge is fundamentally weaker than GBP/USD because EUR/USD is more efficiently priced (tighter spreads, higher liquidity, more algorithmic flow). The SBRS breakout-retest pattern depends on a price inefficiency window after structure breaks — EUR/USD may close this window faster than GBP/USD, invalidating the retest. Test: compare average retest duration (bars from breakout to valid retest) for EUR/USD vs GBP/USD. If EUR/USD retest duration is systematically shorter (< 3 bars average vs > 5 for GBP), the MAX_RETEST_WAIT = 10 parameter is not the issue — the market microstructure is.
**Why it matters:** If the diagnosis is correct, no parameter tuning will lift EUR/USD to Tier 2. The correct action is to close the EUR/USD investigation and reallocate effort. If incorrect, a tunable fix may exist.
**Suggested test:** Extract trade-level log for EUR/USD and GBP/USD. Compute bars_from_breakout_to_retest for each filled setup. Compare distributions. Flag to council if EUR/USD mean < 3 bars consistently.
**Priority:** low (EUR/USD is not a deployment candidate; this is a root-cause closure exercise)
**Status:** open

### 2026-04-17 | by: arbiter-ablation | for: arbiter-ablation (Round 6)
**Claim to test:** Now that session filter is OFF in production, re-run the full 18-config ablation suite with `SESSION_BLOCK_START_HOUR = 99` hardcoded in the harness (or confirmed as the production default). Measure every feature's delta against the filter-OFF baseline (~$50,355). Primary unknowns: (1) Test #8 delta should read ~0%; if not, there is a patch error. (2) FVG contribution (tests #1, #3) may change sign relative to Round 5.
**Why it matters:** Every prior ablation delta was computed against a defunct filter-ON baseline. The council cannot make allocation or deletion decisions on feature contributions that may have shifted materially. FVG's contribution is particularly uncertain — it interacts with the newly admitted 16-23 GMT trades.
**Suggested test:** Modify `ablation_study.py` runner to set `v2_module.SESSION_BLOCK_START_HOUR = 99` before loading any config, OR confirm the production constant has been updated to 99. Run `py -m tests.ablation_study --period 10y`. Redirect output to `/tmp/ablation_round6_filter_off.log`. Compare all 18 deltas against Round 5 baselines. Flag any reversal >10pp.
**Priority:** HIGH (blocker — all current ablation results are relative to a production-defunct baseline)
**Status:** open

### 2026-04-17 | by: arbiter-ablation | for: arbiter-ablation (Round 6 — sub-question)
**Claim to test:** Within the Round 6 filter-OFF ablation, specifically verify whether FVG at weight 0.5 (test #1: No FVG = weight 0.0) still shows a positive contribution (~+$1,519 from Round 5) or whether the newly admitted NY/Asia hour trades change the FVG net sign. If FVG flips to net-negative under filter-OFF, consider whether downweighting further (0.25) or removing entirely is warranted.
**Why it matters:** FVG has reversed once already (Round 2: harmful at 1.0; Round 3: mildly positive at 0.5). A second reversal under filter-OFF would push toward removal. Two consecutive reversals still do not meet the 3-run dead-code threshold — but they do warrant a council discussion on FVG's fundamental role.
**Suggested test:** Isolated within Round 6 run — no additional test needed. Read test #1 and #3 deltas from Round 6 output and compare against Round 5 equivalents. If test #1 delta flips sign, flag immediately to arbiter-gold and arbiter-risk.
**Priority:** HIGH (sub-task of Round 6 — no extra run cost)
**Status:** open (blocked on Round 6 run)

### 2026-04-17 | by: arbiter-ablation | for: user (production decision required first)
**Claim to test (pre-condition, not a test):** `tests/_round5_session_off_wf.py` should be deleted once the production `SESSION_BLOCK_START_HOUR` constant is updated to 99 (filter permanently removed). Before deletion: confirm (a) the production constant update is deployed and committed; (b) a Round 6 filter-OFF ablation run has completed and its log saved; (c) the standard Gold WF regression in `test_gold_backtest.py` or equivalent naturally runs filter-OFF and produces a passing result. Once all three conditions are met, this file is dead weight with an active pytest-contamination risk (import-time monkey-patch).
**Why it matters:** Keeping the file risks silent test pollution on any run where pytest collects it — the patch executes at import time, not inside a test function.
**Suggested test:** User approves production constant change. Developer deletes file. Confirm pytest collection completes without session-filter patch side effects.
**Priority:** medium (no action until production change lands)
**Status:** open (blocked on user approval of session filter production removal)

### 2026-04-17 | by: arbiter-ablation | for: arbiter-crypto
**Claim to test:** The per-asset FVG weight hypothesis for crypto (CONFLUENCE_SCORE_FVG_CRYPTO = 0.75 or 1.0) belongs in a DIRECT BACKTEST first, not in the ablation suite. Ablation is designed for feature isolation on a fixed instrument (Gold); running crypto configs through the Gold ablation harness would conflate asset-class effects. The correct path: direct backtest on BTC/ETH with per-asset weight → if PF ≥1.5, add to a future crypto-specific ablation suite.
**Why it matters:** If crypto-specific ablation configs are added to `tests/ablation_study.py`, they will run on Gold data and produce meaningless deltas. The ablation suite is currently Gold-only (hardcoded `asset_class='gold'` at line 190 of `ablation_study.py`).
**Suggested test:** Arbiter-crypto runs direct BTC/ETH backtest with CONFLUENCE_SCORE_FVG_CRYPTO candidate once 5Y+ Binance data is available. If result passes PF/DD gates, arbiter-ablation can design a crypto-specific ablation suite at that point. No action in current ablation suite.
**Priority:** low (data-blocked — requires 5Y+ Binance data first)
**Status:** open


### 2026-04-17 | by: arbiter-indices | for: arbiter-risk
**Claim to test:** Recalibrated index slippage delta is ~$436 over 532 NASDAQ trades and ~proportional for DAX over 10Y. Does this magnitude meaningfully shift any Tier 1 metric (PF, Sharpe, DD) below threshold?
**Why it matters:** If the corrected slippage drops NASDAQ WF avg PF below 1.5 or Sharpe below 1.0, the tier classification changes. Expected that it does not (0.7% PnL impact) but must be verified before citing current metrics in live deployment decisions.
**Suggested test:** Re-run NASDAQ and DAX full BT with corrected slippage -- multiply line 151 multiplier by 10x (0.1 -> 1.0) as a conservative upper bound. Report PF and Sharpe delta. Only proceed to precise calibration if delta is >5% on any metric.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-indices | for: arbiter-data
**Claim to test:** The arbiter-risk 2026-04-16 hypothesis (pull NASDAQ trade-level log from full BT, identify fat-tail calendar window) has not been executed and is the remaining gate before NASDAQ LIVE promotion. This handoff is confirmed unactioned as of 2026-04-17.
**Why it matters:** NASDAQ BT PF 3.49 red-flag investigation is complete for paper trade purposes (regime-concentration confirmed) but the trade-log confirmation provides the additional assurance needed for live. A price-spike feed anomaly in the stale IBKR cache cannot be ruled out until the specific trade(s) generating outsized wins are identified.
**Suggested test:** Pull NASDAQ trade-level log from full 10Y BT run. Calculate PnL per trade. Identify the top 5 gross-win trades by absolute dollar. Cross-reference their timestamps with known NASDAQ market events (COVID crash recovery 2020-Q2, 2021 meme-rally, 2022 bear, 2023-Q4 AI rally). If the fat-tail wins are concentrated in a known high-volatility period rather than anomalous single-bar spikes, the feed anomaly hypothesis can be closed.
**Priority:** high (gate for LIVE promotion)
**Status:** open

### 2026-04-17 | by: arbiter-indices | for: arbiter-risk (admin)
**Claim to test:** The next-hypotheses.md entry for arbiter-risk -> arbiter-MC (NASDAQ post-change MC) is still marked open but the Round 5 report (67-Round-5-Post-Council-Validation.md) shows NASDAQ MC Prob(20%DD) = 0.38% PASS. If this result is from the Round 5 run, the hypothesis should be closed.
**Why it matters:** Open hypotheses that are already resolved pollute the queue and mislead future arbiters.
**Suggested test:** Confirm the Round 5 MC run used post-change NASDAQ parameters (FVG 0.5, DD cap 0.20, sbrs_v2 default). If yes, mark the 2026-04-16 arbiter-risk -> arbiter-MC hypothesis as closed in next-hypotheses.md.
**Priority:** low (admin only)
**Status:** open

### 2026-04-17 | by: arbiter-regime | for: arbiter-ablation
**Claim to test:** ATR_PCTILE_ENABLED_GOLD = True has been present in every ablation baseline and has never been directly tested. Its docstring motivation (targeting Gold W5-W6 dead zones) is now obsolete — those windows flipped profitable via the DD cap fix, not via the ATR filter. The filter mechanically blocks ~25% of Gold entry candidates at all times (rolling local 25th percentile). With Gold confirmed regime-robust (8/8 WF) and session filter now OFF (more valid trades available), the filter may be suppressing profitable edge.
**Why it matters:** If disabling the filter lifts Gold trade count 10-25% while maintaining PF ≥1.5 and 8/8 WF, it is dead weight with a historical artefact justification. If PF drops below 1.5 when disabled, it is doing genuine protective work and its motivation must be updated.
**Suggested test:** Add `ATR_PCTILE_ENABLED_GOLD = False` as a Round 6 ablation config. Run on post-change filter-OFF Gold 10Y OANDA baseline. Report: trade count delta, PF delta, Sharpe delta, WF consistency. Accept filter removal ONLY if PF ≥1.5 and WF ≥75% (8/8 preferred). Run as part of Round 6 suite alongside the re-baselined filter-OFF configs.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-regime | for: arbiter-execution
**Claim to test:** Asia-hours sub-session filter (e.g., block h=22-23 GMT on Gold) cannot be evaluated with single-instrument data (40 trades over 10Y, below 50-trade minimum). Pool hourly PnL data from Gold + DAX + GBP/USD to build 50+ trade buckets per hour, then assess whether any hour is consistently net-negative across all three instruments.
**Why it matters:** This is the only legitimate path to a regime-aware time-of-day filter. If h=22-23 is consistently weak across instruments, a principled Asia-session filter becomes testable. If it varies by instrument, the hours are not a regime signal — they are instrument-specific noise.
**Suggested test:** Re-run hour-of-day PnL tagging on DAX 10Y and GBP/USD 10Y filter-OFF (when available). Pool with Gold 737-trade hour table. For each hour bucket, require n≥50 across the pool before drawing conclusions. Accept a filter for hour h only if net-negative across ≥2 of 3 instruments.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-data | for: arbiter-data (self, Round 6)
**Claim to test:** IBKR _load_cache() silently serves any-age stale data when TWS is down. Fix: add last-bar staleness check and print WARNING with last-bar date if >7 days stale. Mirror the binance_fetcher.py 3-day guard pattern.
**Why it matters:** Currently the only indication of stale IBKR data is a bar-count log line with no date. A 28-day-old cache would be served silently — operator has no signal to investigate.
**Suggested test:** (1) Add check to ibkr_fetcher._load_cache: compute (today - last_bar).days; if >7, print WARNING. (2) Add last-bar date to fetcher.py log line 159. (3) Run data/cache inspection script to confirm warning fires on current 28-day-stale caches.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-data | for: arbiter-data (self, next TWS session)
**Claim to test:** DAX and NASDAQ IBKR caches are 28 days stale (last bar 2026-03-20). Refresh to capture the 2026-03-20 to 2026-04-17 period before next WF cycle.
**Why it matters:** Window 8 (most recent) for both instruments is missing 28 days of data. This slightly biases W8 PnL figures. DAX/NASDAQ are 100% WF consistent post-change so this is a precision issue, not a tier-classification risk, but it must be resolved before any live-deployment decision that references W8 specifically.
**Suggested test:** With TWS running: py -m src.data.ibkr_fetcher for ^GDAXI and ^IXIC. Verify new bar counts: expect DAX ~23,000-23,100 bars, NASDAQ ~17,650 bars. Recheck W8 PnL vs current Round 5 figure.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-data | for: arbiter-gold
**Claim to test:** OANDA Gold bar H-L range vs Yahoo GC=F H-L range on the 2Y overlap window. OANDA reports mid-price (bid-ask midpoint); Yahoo reports COMEX settlement last trade. Hypothesis: OANDA bars have systematically narrower High-Low ranges, reducing swing detection frequency and suppressing SBRS 2.0 setup generation — a possible explanation for 737 OANDA trades vs ~1,824 Yahoo-equivalent (18.9%-adjusted) trades.
**Why it matters:** If OANDA bar construction suppresses swing detection, the trade count gap is partially a data-construction artefact rather than a genuine strategy difference. This affects the statistical power of all OANDA-based WF runs and could mean the true edge is stronger but under-sampled.
**Suggested test:** (1) Fetch OANDA Gold 2Y 1H and Yahoo GC=F 2Y 1H on the overlap window. (2) Compute mean (High-Low)/Close per bar for each source. (3) Count swing highs/lows (SWING_LOOKBACK=20, SWING_WINDOW=3) detected per 1000 bars. (4) Report delta. No code changes — diagnostic only.
**Priority:** high (largest unresolved data-source risk on Gold)
**Status:** open

### 2026-04-17 | by: arbiter-execution | for: arbiter-risk
**Claim to test:** apply_slippage() in risk_manager.py under-costs NASDAQ by 3-13x and DAX by 3-10x. The price>1000 branch applies the same $0.15/side formula to both Gold (~$2,300) and indices (~$15k-21k). A corrected index slippage model (asset-class-aware constant, not price-magnitude branching) may lower DAX/NASDAQ WF-avg PF below the 1.5 Tier 1 gate.
**Why it matters:** All published NASDAQ (WF-avg PF 1.73) and DAX (WF-avg PF 1.96) figures are optimistic on cost. If corrected slippage drops either below 1.5, their Tier 1 status is conditional. This is a pre-live critical check.
**Suggested test:** (1) Implement SLIPPAGE_PIPS_INDICES = 10 (equivalent to ~$1.70 on NASDAQ, ~$2.10 on DAX per side -- realistic for 0.01% of price) in a test-only branch of risk_manager.py. (2) Re-run NASDAQ and DAX 10Y WF with corrected slippage. (3) Compare WF-avg PF and Sharpe to current figures. Accept Tier 1 only if WF-avg PF >= 1.5 under corrected model. Requires user approval before risk_manager.py modification (ask-first rule).
**Priority:** HIGH
**Status:** open

### 2026-04-17 | by: arbiter-execution | for: arbiter-execution (live phase)
**Claim to test:** The backtest 1.5-pip slippage assumption for Gold has never been validated against live OANDA fill data. Once paper trading starts, every entry fill price should be compared against the bar close price used in the backtest to compute fill_drift_pips. If mean drift > 2.0 pips or > 3 pips in 10% of cases, the slippage model is under-conservative.
**Why it matters:** Live-vs-backtest execution drift is the primary unknown for Gold paper trading. If actual slippage is systematically higher than modeled, expectancy ($64.95/trade) will be eroded in live conditions.
**Suggested test:** After 30+ paper trades on Gold: extract entry fill prices from OANDA trade records. Compute fill_drift_pips = (actual_fill - bar_close_at_signal) / 0.0001 (or price equivalent). Report mean, median, P95. Compare to 1.5 pip model. If mean drift > 1.5 pips, increase slippage constant and re-run MC to confirm Prob(20%DD) still <5%.
**Priority:** medium (blocked on paper trading start)
**Status:** open

### 2026-04-17 | by: arbiter-execution | for: arbiter-indices (cross-ref)
**Claim to test:** Hour-of-day PnL analysis for DAX and NASDAQ (filter-OFF equivalent) to check whether any hour cluster is consistently net-negative across instruments. This pools bucket counts with Gold to reach 50-trade minimums.
**Why it matters:** DAX has its own session filter (07:00-15:30 GMT, constrained first/last windows). NASDAQ uses 13:30-20:00 GMT. Cross-instrument pooling of hour buckets may enable principled hour-level analysis with 50+ trades/bucket.
**Suggested test:** Run backtest on DAX 10Y and NASDAQ 10Y with session filter OFF (monkey-patch is_indices_session_blocked). Tag trades by hour. Pool with Gold hour table from arbiter-execution Round 4 log. Report any hour with net-negative PnL in 2+ of 3 instruments.
**Priority:** medium
**Status:** open

### 2026-04-17 | by: arbiter-risk | for: arbiter-risk (next session)
Claim to test: Gold filter-OFF MC re-run required. Round 5 Gold MC (3.08%) was computed on filter-ON 643-trade sample. Session filter is now confirmed OFF (737 trades). Re-run MC on filter-OFF Gold to get the authoritative per-strategy Prob(20%DD) figure.
Why it matters: 3.08% is currently cited as the paper-trade approval figure. It may improve (more trades = lower concentration) or stay flat. Either way the filter-OFF figure is the one that reflects production.
Suggested test: Run /monte-carlo on Gold 10Y OANDA post-change with session filter OFF (SESSION_BLOCK_START_HOUR=99). 10,000+ simulations. Report Prob(20%DD). Update shared-findings.md with the authoritative number.
Priority: medium (existing 3.08% already passes; paper trade not blocked)
Status: **CLOSED 2026-04-18** — see shared-findings.md 2026-04-18 arbiter-risk entry. Result: 733 trades, Prob(20%DD) = 2.24% PASS (improved from 3.08%).

### 2026-04-17 | by: arbiter-risk | for: arbiter-risk (Round 7)
Claim to test: Fat-tail portfolio MC (Student-t shocks, nu=4) for the 4-strategy portfolio. Normal-distribution MC (current) produced Prob(20%DD) = 0.00%, P99 = 10.21%. Fat-tail modelling will push P99 higher and may surface non-zero Prob(20%DD) under extreme concurrent drawdowns.
Why it matters: All current MC uses Gaussian shocks. Real market returns have fat tails (kurtosis > 3). Under Student-t nu=4 (excess kurtosis = 2.0), extreme correlated losses are more frequent. Before raising any strategy above current risk levels, the fat-tail portfolio figure is required.
Suggested test: Replace random.gauss() with numpy Student-t (scipy.stats.t(df=4).rvs) in the correlated MC simulation. Run 50k sims. Compare P99 and Prob(20%DD) to the Gaussian baseline.
Priority: high (required before any risk-level increase)
Status: open

### 2026-04-17 | by: arbiter-risk | for: user (approval required)
Claim to test: risk_manager.py apply_slippage() third price bracket for high-price indices. Current code applies slip = 1.5 * 0.1 = 0.15 units for any entry_price > 1000, which under-costs NASDAQ/DAX by 6.7x on slip/ATR basis. Correct formula: add branch entry_price > 5000 -> slip = 1.5 * 1.0 (one index point). This is the realistic spread+market impact for NQ and DAX futures.
Why it matters: Immaterial at current 0k validation capital (/usr/bin/bash.04/trade understatement) but mandatory before live deployment at professional capital (0k+: /usr/bin/bash.21/trade, 13 over 532 trades = 0.23% equity). Leaving it uncorrected means all published DAX and NASDAQ PF figures are very slightly overstated.
Suggested test: N/A -- this is a code change proposal. Requires explicit user approval before modifying risk_manager.py (PROTECTED FILE).
Priority: low (immaterial now, high before professional-capital live deployment)
Status: open -- awaiting user approval

### 2026-04-17 | by: arbiter-risk | for: arbiter-data
Claim to test: GBPUSD position sizing review trigger -- once GBPUSD WF trade count exceeds 500, re-run per-strategy MC at 0.5% to confirm whether sizing can be raised. Current 274 WF trades is below the 500-trade minimum, so 0.25% is conservative. At 500+ trades the parameter uncertainty argument against 0.5% weakens.
Why it matters: GBPUSD at 0.5% would add 0.25% to portfolio risk total (1.25% to 1.5%). At that level, portfolio P99 max DD would move from ~10% to ~12-13% -- still within charter but less headroom. Confirming via MC first is required.
Suggested test: When GBPUSD WF trade count reaches 500+ (confluence-1.5 filter may throttle this -- check), run per-strategy MC at 0.5% and 0.25%. Also re-run 5-strategy portfolio MC (Gold + DAX + NASDAQ + GBPUSD + USD/JPY if validated) at revised sizing.
Priority: low (blocked on GBPUSD trade count; monitor per Round 7)
Status: open

### 2026-04-18 | by: arbiter-indices | for: arbiter-risk + arbiter-data (CRITICAL)
**Claim to test:** NASDAQ OANDA 10Y fresh BT produced PF 0.86 (Tier 4), reversing Round 5 canon of BT PF 3.49 / WF 8/8. Three variables are confounded: (a) data source flip IBKR cache → OANDA, (b) slippage bracket flip $0.15 → 1.5pt, (c) post-change session-handling. Triangulate which variable dominates.
**Why it matters:** If NDX Tier 1 verdict was a data-source artefact, portfolio score drops from 9/10 to 8/10 (3 Tier-1 strategies). DAX is at parallel risk — same IBKR cache, same prior-canon slippage. Before any paper or live deployment.
**Suggested test:**
  1. **Slippage isolation:** run NDX 10Y OANDA with B1 bracket temporarily reverted to `slip=0.1` for entry_price>1000 (restore prior cost). If PF recovers to ~3, slippage dominates → NDX real, overvalued before.
  2. **Data isolation:** refresh IBKR NDX cache via TWS, re-run BT with B1 bracket live. If PF matches prior ~3.49, data source dominates → OANDA NDX is under-sampled/misconstructed.
  3. **Cross-check DAX:** repeat the same dual isolation on DAX. If DAX also collapses on OANDA, the OANDA indices feed is the issue; if DAX is robust, NDX is instrument-specific.
**Priority:** HIGH — blocks Round 6 closure, paper-gate 10/10, and any NDX/DAX paper-trade authorization.
**Status:** open

### 2026-04-18 | by: arbiter-ablation | for: arbiter-ablation (Round 7 cleanup)
**Claim to test:** Round 6 ablation tests #8 (No Session Filter), #9 (No Squeeze), #10 (No Whipsaw) produced exactly-matching-baseline results (733 trades, PF 2.05, $46,450). Confirms these three flags are dead code under filter-OFF production. Candidates for code removal.
**Why it matters:** Three dead flags bloat the confluence-scoring path. Each has a docstring/comment that misleads future readers about what the strategy does. Removal is a Round 7 cleanup item once NDX/DAX isolation (R6-1) is resolved.
**Suggested test:** After Round 6 ablation completes and R6-1 closed: grep `src/regimes/sbrs_v2.py` for the three flags; confirm no production call path touches them; remove constants + any is_*_blocked helper that has become orphaned. Add a regression test that asserts strategy output is unchanged on the Round 6 baseline.
**Priority:** medium (cleanup, not edge-affecting)
**Status:** open — blocked on Round 6 completion + R6-1 closure

### 2026-04-18 | by: arbiter-forex | for: arbiter-forex (Round 7)
**Claim to test:** Round 6 C4 sweep (logs/round6/gbpusd_atr_sweep.log) identifies T=20 as the PF/Sharpe/PnL optimum for GBPUSD. Propose changing `ATR_PCTILE_THRESHOLD` from 25 → 20 for forex. Uplift: +$254, +0.02 PF, +0.13 Sharpe, -0.92pp DD.
**Why it matters:** Current T=25 is within ±20% tunable range of T=20 (20 * 1.2 = 24 — at the boundary). Round 7 should confirm via WF re-run that T=20 preserves WF consistency ≥75% before promoting to canon.
**Suggested test:** Patch `ATR_PCTILE_THRESHOLD = 20` (or add asset-class override `ATR_PCTILE_THRESHOLD_FOREX = 20`), run GBPUSD 10Y WF. Compare to current WF 7/8 @ T=25. Accept only if WF consistency stays ≥75% AND W7 does not regress.
**Priority:** medium (edge improvement, not blocker)
**Status:** open — scheduled for Round 7

### 2026-04-18 | by: arbiter-risk | for: arbiter-risk + arbiter-execution (Round 7)
**Claim to test:** DAX 10Y OANDA 3-variant slippage isolation (mirror of R6-1 NDX). DAX price (~$21k) hits the same B1 `>5000` bracket as NDX. If B1 over-conservatism dominates on NDX, it likely dominates on DAX equivalently.
**Why it matters:** Under current B1 live, DAX was reported Tier 1 (PF 1.96, Sharpe 1.21). If B1 is 10× too conservative there too, the true DAX edge is even stronger; if DAX is less sensitive than NDX, the B1 calibration argument weakens.
**Suggested test:** Write `tests/_r7_dax_slip_isolation.py` mirroring `tests/_r6_ndx_slip_isolation.py`. Run Variant A (B1 live @ 1.5pt), Variant B (0.15pt old-equivalent), Variant C (slip OFF) on ^GDAXI 10Y OANDA. Report PF/Sharpe/DD delta between A and B to triangulate B1 DAX impact.
**Priority:** HIGH — second pillar of slippage recalibration decision.
**Status:** open — paired with arbiter-risk slippage recalibration user-decision entry

### 2026-04-18 | by: arbiter-data | for: arbiter-data (Round 7)
**Claim to test:** Round 6 D1 Gold OANDA-vs-Yahoo bar audit was inconclusive because `src/data/fetcher.py::fetch("GC=F", ...)` routes through OANDA regardless of symbol format. True Yahoo comparison requires direct `yfinance.download("GC=F", ...)` bypass.
**Why it matters:** Round 5 Y5 wanted to confirm whether Yahoo Gold data (the pre-Round-2 baseline source) had phantom 24/5 bars OANDA correctly omits. Still unresolved.
**Suggested test:** Add a `--force-source=yahoo` override to `fetch()` OR run `yfinance.download` directly in the D1 script. Compare bar timestamp sets between OANDA (11,785 bars) and Yahoo for the same window. Report any missing/phantom bar explanations.
**Priority:** low (diagnostic only; no edge impact)
**Status:** open — scheduled for Round 7
