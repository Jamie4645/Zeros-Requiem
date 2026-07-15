# Round 8 — Evidence-Weighted Portfolio Sizing

Date: 2026-04-19
Status: CANONICAL (supersedes R7 1.50% allocation)
Authors: Philosophical Council (18-member) + Arbiter Council (domain) synthesis
Entry point: `src/core/risk_manager.py SYMBOL_RISK_CAP`

---

## The council verdict: 1.50% → 1.10%

Both councils reviewed the R7 canon (9/10 with 1.50% live risk across 5 strategies) and independently arrived at the same conclusion: **the 1.50% allocation averaged genuine edges (Gold) with fragile ones (NDX SLOPE, USDJPY red-flag) at equal weight, hiding diversifiable risk.**

Neither council endorsed a pure barbell (Gold-only + cash) nor the pure per-strategy MC (accept all 5 at equal 0.25% weight). The evidence-weighted allocation is the third answer that survived both councils' cross-examination.

## Per-strategy sizing derivation

| Strategy | R7 size | R8 size | Δ | Primary reason |
|---|---:|---:|---:|---|
| Gold | 0.50% | **0.50%** | 0bps | Structural R3-hedge; 100% WF; PLATEAU slip curve; R8 direction-run confirms both L and S streams. Anchor — untouched. |
| DAX | 0.25% | **0.25%** | 0bps | PLATEAU slip curve (15.6% PF range); MC 2.42% PASS. Robustness earns stability — no change. |
| NDX | 0.25% | **0.15%** | -10bps | **SLOPE** slip curve (32.2% PF range, DD doubles 0.5→1.25pt). Reversal from Tier 4 in R6 makes the edge parameter-dependent. Halve the bet. |
| GBPUSD | 0.25% | **0.20%** | -5bps | 100% WF but 275 trades (<500 gate) and only $4k over 10Y. Small-PnL contributor; can't justify 0.25%. |
| USDJPY | 0.25% | **0.00%** | -25bps | Paper-only. BT PF 3.18 > red-flag; WR 54.7% highest in portfolio; 161 trades; council dissent unresolved. Remove from live queue. |
| **Total** | **1.50%** | **1.10%** | **-40bps** | Evidence-weighted. |

## Measured portfolio MC at 1.10%

`logs/round8/portfolio_studentt_mc_110.log` (seed=42, 10k sims):

| Metric | Student-t ν=4 base | Gaussian | Student-t +0.2 stress |
|---|---:|---:|---:|
| Prob(20%DD) | **0.0%** | 0.0% | **0.0%** |
| Prob(15%DD) | 0.0% | 0.0% | 0.0% |
| Prob(10%DD) | 0.0% | 0.0% | 0.0% |
| Avg Max DD | 3.14% | 3.15% | 3.16% |
| P95 Max DD | 4.86% | 4.93% | 4.95% |
| P99 Max DD | 6.09% | 6.13% | 6.25% |
| **Expected Annual PnL** | **$6,468 (64.68%)** | $6,433 | $6,425 |
| P5 Annual PnL | $3,785 | $3,707 | $3,683 |
| P95 Annual PnL | $9,617 | $9,614 | $9,643 |
| Worst 1% Annual PnL | +$2,797 | +$2,758 | +$2,731 |

**Verdict:** PASS elite <5% base / <10% stress. Penalty vs Gaussian +0.0pp. Worst-1% annual is still positive.

## What we gave up vs R7 1.50%

- Expected PnL is ~8% lower than hypothetical 1.50% (but Round 7 never measured exact 1.50% MC; analytical approximation suggested 60.1% return, so Δ is ~5-7pp).
- Max exposure cut by 27% (1.50 → 1.10).
- USDJPY "promotion narrative" from R7 frozen — protects against the red-flag PF.
- NDX now scales only 0.6x in each trade — avoids the SLOPE tail.

## What we bought

- No single strategy contributes >45% of portfolio risk (Gold 0.50 / 1.10 = 45%).
- No fragile strategy (SLOPE / red-flag) dominates.
- Both councils' minority reports are converted into enforceable falsifiers (see `75-Pre-Registered-Falsifier-R8.md`).
- Live-ramp decision becomes reversible: if Falsifier #1 trips, the default action is HALT not tune.

## Code changes

- `src/core/risk_manager.py::SYMBOL_RISK_CAP` expanded from `{'GBPUSD': 0.0025, 'USDJPY': 0.0025}` to the full 5-key R8 dictionary.
- `_normalize_symbol_for_cap` extended with ticker map (GC=F → GOLD, ^IXIC → NDX, ^GDAXI → DAX) so the cap mechanism binds at engine level, not just CLI.
- Gate enforces `min(caller_requested_risk, SYMBOL_RISK_CAP[symbol])` — caller cannot over-ride the council's sizing by passing a larger `--risk`.

## Rollback condition

The council agrees to revisit this allocation if and only if:
1. 60d paper-trade shows realized slip within tolerance (Falsifier #1 PASS), AND
2. Per-strategy direction/regime data clears Falsifier #5 for NDX / DAX / GBPUSD / USDJPY (currently only Gold clear), AND
3. `arbiter-canon-audit` confirms freshness of every BT/WF/MC number on the next review.

If all three pass → proposal to lift NDX back to 0.20% and GBPUSD to 0.25%, total 1.20%. Gold and DAX would remain unchanged. USDJPY unchanged at 0.00% until its gates clear independently.
