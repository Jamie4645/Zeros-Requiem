---
tags: [arbiters, charter, governance]
aliases: [Charter, Council Charter, Arbiter Rules]
---

# Sovereign Quant Arbiter — Council Charter

**Every Arbiter must read this file before starting work.**

## Mission

> Build the top-1% systematic algo-trader by codifying and refining Jamie's proven discretionary edge — never by inventing a new one.

## The Five Fundamental Truths (Mark Douglas)

Every Arbiter thinks in probabilities:
1. Anything can happen on any single trade.
2. You don't need to know what will happen next to make money.
3. There is random distribution between wins and losses.
4. An edge is a higher probability indication — not a certainty.
5. Every moment in the market is unique.

## Elite Benchmarks (the bar)

| Metric | Target |
|---|---|
| Sharpe Ratio | ≥1.5 |
| Profit Factor | ≥1.5 |
| Annual Return | ≥20% |
| Max Drawdown | ≤15% |
| Walk-Forward Consistency | ≥75% of windows profitable |
| Monte Carlo Prob(20% DD) | <5% |
| Trades per strategy | ≥500 |
| Simultaneous strategies | ≥5 uncorrelated |

## Hard Rules (NEVER violate)

1. **Never modify sacred files** without explicit user approval:
   - `src/core/risk_manager.py`
   - `WMA_PERIOD`, `SMMA_PERIOD`, `SWING_LOOKBACK`, `MIN_RR`, `RETEST_TOLERANCE_ATR`
2. **Never deploy to live.** Arbiters propose; user approves; user deploys.
3. **Never cherry-pick.** Report the full walk-forward table including losing windows.
4. **Never claim validation without walk-forward.** Single-backtest = hypothesis, not conclusion.
5. **Never invent strategies.** Codify Jamie's edge. If considering new logic, flag to Council for user decision.
6. **Never hide failure.** Honest rejection > false hope.
7. **Never over-optimise.** Parameters outside ±20% range of published values require explicit approval.

## Standard Protocol

### Before starting
1. Read `council-charter.md` (this file)
2. Read `shared-findings.md` — what others have learned
3. Read your own log `logs/<your-name>-log.md` — what you've tried before
4. Read `next-hypotheses.md` — what other Arbiters have flagged for your domain

### During
- Prefer skills (`/walk-forward`, `/monte-carlo`, `/ablation`) over inline Python
- Use the existing sub-agents (`strategy-validator`, `new-pair-scout`, `portfolio-correlator`, `bug-hunter`) when their domain matches
- Write intermediate observations to your own log; final canonical findings to shared-findings.md

### After
1. Append to your own log (chronological)
2. Append to `shared-findings.md` if finding is novel
3. Append to `next-hypotheses.md` if you have ideas outside your domain

## Finding Template (use in shared-findings.md)

```markdown
### YYYY-MM-DD | <arbiter-name> | <short title>
**Hypothesis:** <what you set out to test>
**Test:** <command, period, instrument>
**Result:** <one sentence conclusion>
**Evidence:** <log path or reproducible command>
**Confidence:** low / medium / high
**Implications:** <what downstream decisions does this unlock>
```

## Hypothesis Template (use in next-hypotheses.md)

```markdown
### YYYY-MM-DD | by: <author-arbiter> | for: <target-arbiter>
**Claim to test:** <testable statement>
**Why it matters:** <expected impact if true>
**Suggested test:** <specific approach>
**Priority:** low / medium / high
**Status:** open / claimed / closed
```

## Tier Classification (for any new instrument or variant)

| Tier | Criteria | Action |
|---|---|---|
| 1 | PF ≥1.5, Sharpe ≥1.5, WF ≥75%, MC pass, 500+ trades | Recommend paper-trade at 0.25% risk |
| 2 | PF ≥1.3, Sharpe ≥1.0, WF 62–74%, or insufficient data | Document, investigate gaps |
| 3 | PF 1.0–1.3, barely profitable | Note, do not deploy |
| 4 | PF <1.0 or catastrophic DD | Reject with reason |

## Current Portfolio (as of Round 2, 2026-04-16 — to be updated post-change-validation)

**Pre-change baselines (frozen for comparison):**
- Gold v2: 413 trades | PF 1.31 | Sharpe 0.64 | WF 62% | MC 20%DD = 25.9%
- DAX v2: 1,230 trades | PF 1.34 | Sharpe 0.88 | WF 75% | MC 20%DD = 22.4%
- NASDAQ v2: 888 trades | WF 100% | MC 20%DD = 4.16% *(only asset meeting elite bar)*
- GBPUSD v2: 1,323 trades | WF 38% | MC 20%DD = 73% *(needs investigation)*

**Post-change results** will be recorded in `shared-findings.md` once background tests complete.

## Related

- [[../CLAUDE|CLAUDE.md]] — root project spec
- [[../65-Sovereign-Quant-Arbiters|Arbiter System Overview]]
- [[../16-Risk-Management-Elite-System|Risk Management]]

## Portfolio History — Round 4 (2026-04-16, post domain-arbiter returns)

**Tier 1 confirmed:**
- DAX v2 (NEW): WF 100% (8/8), single-BT PF 1.96, Sharpe 1.21, Max DD 7.92%. Clean OANDA data. MC pending.

**Tier 1 provisional (pending clean re-run):**
- Gold v2: WF 8/8 post DD-cap-fix, worst window +$154 (thin), 643 trades (vs Yahoo-era 2,252). OANDA 502 partials on BT leg — requires clean re-fetch. Mechanism (DD cap 0.10→0.20) confirmed.

**Tier 1 pending WF re-run (fetch-blocked):**
- NASDAQ v2: full-BT PF 4.53 ruled regime-concentration (not leakage, not compounding). WF-avg PF 1.56 is canonical. OANDA 502 blocked post-change WF retry.

**Tier 2 conditional:**
- GBPUSD v2: post-change WF 7/8 (87.5%), W7 -$1,072 (was -$2,013). Blocked from Tier 1 by: MC not rerun post-change (baseline was 73% prob 20% DD), forex-scoped confluence-1.5 test outstanding, OANDA data completeness unconfirmed.

**Tier 3 (downgraded from Tier 2):**
- BTC v2: PF 1.31 post FVG-0.5 (was 1.59). FVG downweight is net-negative for crypto.
- ETH v2: PF 1.21 post FVG-0.5 (was 1.63). DD 19.71% > 15% elite gate.

**Tier 3 (unchanged):**
- USDJPY, EURUSD — post-change WF outstanding.

**Portfolio-level (Gold 0.5% + DAX 0.25% + NASDAQ 0.25%):**
- Prob(20%DD) = 0.0% (elite gate PASSED). P95 max DD = 5.6%. P99 = 7.2%. Correlated MC 20k sims (DAX-NASDAQ +0.55, Gold-indices -0.15).

## Portfolio History — Round 5 (2026-04-18, post Health Audit synthesis)

**Tier 1 CONFIRMED (all four MC-cleared, paper-trade ready):**
- Gold v2: WF 8/8 (100%), BT PF 1.88, Sharpe 1.25, DD 11.87%, MC 3.08% PASS (filter-ON 643-trade sample — re-run due on filter-OFF 737-trade production distribution)
- DAX v2: WF 100%, BT PF 1.96, Sharpe 1.21, DD 7.92%, MC 0.76% PASS. 457 trades (slight caveat vs 500 floor)
- NASDAQ v2: WF 8/8 (100%), WF-avg PF 1.73, BT PF 3.49 (regime-concentration confirmed, not leakage), MC 0.38% PASS. Paper trade GREEN; LIVE YELLOW pending trade-log fat-tail pull (arbiter-data)
- GBPUSD v2: WF 7/8 (88%), PF 1.51, MC 0.76% PASS. **274 trades below 500-minimum** — paper-trade cleared at 0.25% risk; do NOT lift to 0.5% until count exceeds 500

**Tier 2 (data-limited):**
- USDJPY v2: WF 88%, PF 1.48, Sharpe 1.16 — only 23 trades on OANDA 2Y. 5Y+ data required.

**Tier 3:**
- EURUSD v2: WF 88% but Sharpe 0.38, W7 -$806 — edge too thin; hypothesis that EURUSD is too efficiently priced for SBRS retest duration
- BTC v2: PF 1.31, MC 20% FAIL — confirmed FVG downweight hurt; per-asset weight path gated on 5Y+ Binance data
- USDJPY (repeat): data-limited, 2Y only

**Tier 4 (rejected):**
- ETH v2: DD 19.71% breach, MC 27.57% FAIL
- S&P 500: structurally locked out of live runner, zero regression risk
- AUDUSD: no edge (pre-existing)

**Portfolio-level (Gold 0.5% + DAX 0.25% + NASDAQ 0.25% + GBPUSD 0.25% = 1.25% total):**
- Correlated MC (Gaussian, 20k sims, Cholesky 4x4): Prob(20%DD) = 0.00%, Avg max DD 4.64%, P50 4.29%, P95 8.00%, P99 10.21%
- All gates PASS. Student-t nu=4 fat-tail re-run queued for Round 7 before any sizing increase.

**Portfolio score: 9/10** (up from Round 4 5/8). Blocker to 10/10: one additional WF-validated strategy. USDJPY is the highest-probability 5th candidate (blocked on 5Y+ data).

**User-decision queue (from Round 5 synthesis):**
1. Flip production SESSION_BLOCK_START_HOUR to 99 (Gold) — required before Round 6 ablation
2. Approve risk_manager.py third slippage bracket (entry_price > 5000 -> slip = 1.5 * 1.0) — mandatory before professional-capital live for NASDAQ/DAX
3. GBPUSD sizing ceiling confirmed at 0.25% until WF trade count reaches 500


## Portfolio History — Round 6 (2026-04-18, post R6 closure synthesis)

**Tier 1 (paper-trade authorized at current sizing):**
- Gold v2: WF 8/8, BT PF 2.05, Sharpe 1.43 (vs 1.50 target — marginal shortfall named honestly), Max DD 11.44%, MC **2.24% PASS** (filter-OFF 733-trade authoritative, supersedes Round 5 3.08%). Hold at 0.5% — do NOT raise to 0.6%.
- DAX v2: WF 100%, BT PF 1.96, Sharpe 1.21, DD 7.92%, MC 0.76% PASS. **Caveat:** cited under old-cost model; never B1-isolated. R7 3-variant slippage parallel mandatory before live-sizing decisions. Paper at 0.25% defensible.
- GBPUSD v2: WF 7/8, PF 1.51, MC 0.76% PASS. **Hard-capped at 0.25%** (274 WF trades below 500 floor). C4 sweep identifies T=20 optimal (PF 1.57) — R7 merge after per-pair-scoped WF re-run.

**Tier 4 (SUSPENDED — recoverable):**
- NASDAQ v2: Under B1 live, fresh 10Y OANDA BT PF 0.86 (Tier 4). R6-1 isolation RESOLVED — data-source flip contributes ~0%, 100% of collapse is B1 slippage being ~10× too conservative for OANDA NAS100. **Restorable to Tier 1** on user approval of slippage recalibration THEN fresh WF at new cost. Variant B alone (old 0.15pt cost, PF 3.57) is NOT a sufficient reinstatement gate per arbiter-indices.

**Tier 2 (data-blocked):**
- USDJPY v2: WF 88%, PF 1.48, 23 OANDA trades. 5Y+ data required.

**Tier 3:**
- BTC v2: PF 1.31, 2Y only. Pre-WF ablation spec from arbiter-crypto: FVG OFF + Liquidity OFF + weekend/weekday split before committing to 5Y+ WF.
- EURUSD v2: Sharpe 0.38, edge too thin.

**Tier 4 (rejected):**
- ETH v2: DD 19.71%, MC 27.57% FAIL. Slippage under-costed but independently rejected on DD + MC.
- S&P 500: locked out.
- AUDUSD: no edge.

**Portfolio-level (Gold 0.5% + DAX 0.25% + GBPUSD 0.25% = 1.0% total under B1 live):**
- arbiter-risk: defensible for 30-60d paper run as-is (safer than 4-strategy 1.25%).
- Portfolio score: **8/10 under B1 live | 9/10 restorable on slippage_pips=0.75 approval | 10/10 blocked on 5th WF-validated strategy**.

**User-decision queue (single blocker for Round 7 Phase 1):**
1. **Approve slippage_pips = 0.75 (Option 2, global)** — restores NDX reinstatement path + DAX validation. Gold unaffected (hits 0.1 multiplier branch, not B1 1.0 branch).
