---
tags: [ablation, sbrs, validation, round6]
aliases: [Round 6 Ablation, Filter-OFF Ablation]
related: [[00-MOC-Zeros-Requiem]], [[48-Ablation-Study-Results]], [[62-Ablation-Round-2-Results]], [[66-Ablation-Round-3-Post-Change]], [[67-Round-5-Post-Council-Validation]], [[73-Round-5-Remediation-Log]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the ablation PF/Sharpe/PnL table below is a void artifact, not
> current state. Retained as historical record only. Current canon: root `CLAUDE.md` +
> [[00-MOC-Zeros-Requiem]].

# Round 6 Ablation Results — Gold Filter-OFF Re-Baselined (2026-04-18)

> **Council mandate (Round 5):** Round 4 ablation deltas were measured against a defunct filter-ON baseline. With `SESSION_BLOCK_START_HOUR = 99` now production, every delta must be recomputed against the filter-OFF canon.

## Context

- **Data:** OANDA Gold (GC=F) 10Y 1H, 59,065 candles (2016-04-20 → 2026-04-17).
- **Baseline config:** post-Round-5 SBRS 2.0 with `SESSION_BLOCK_START_HOUR = 99`, FVG weight 0.5, DD cap 0.20, new B1 slippage bracket.
- **Log:** `logs/round6/ablation_round6.log`

## Full Results Table

| # | Test | Trades | WR | PF | PnL | Sharpe | MaxDD | Δ vs Base |
|---|------|-------:|---:|---:|----:|---:|---:|---:|
| — | **Baseline (full v2.0)** | **733** | **43.8%** | **2.05** | **$46,449.95** | **1.43** | **11.4%** | **BASE** |
| 1 | No FVG | 374 | 43.3% | 2.18 | $25,644.03 | 1.27 | 6.4% | −44.8% |
| 2 | No Liquidity Sweep | 209 | 38.8% | 0.96 | −$607.53 | −0.04 | 20.8% | −101.3% |
| 3 | No FVG + No Liquidity | 67 | 31.3% | 0.76 | −$1,193.42 | −0.25 | 20.8% | −102.6% |
| 4 | No MA Cross Score | 498 | 43.2% | 1.51 | $14,969.16 | 0.83 | 15.5% | −67.8% |
| 5 | MA Cross ONLY | 0 | — | ∞ | $0 | 0.00 | 0.0% | −100.0% |
| 6 | No Level Gate (0 touches) | 750 | 44.1% | 2.05 | $46,703.76 | 1.40 | 13.0% | **+0.5%** |
| 7 | No Counter-Trend | 632 | 42.6% | 1.46 | $17,686.77 | 0.83 | 17.1% | −61.9% |
| 8 | No Session Filter | 733 | 43.8% | 2.05 | $46,449.95 | 1.43 | 11.4% | **+0.0%** (DEAD) |
| 9 | No Squeeze Filter | 733 | 43.8% | 2.05 | $46,449.95 | 1.43 | 11.4% | **+0.0%** (DEAD) |
| 10 | No Whipsaw Detection | 733 | 43.8% | 2.05 | $46,449.95 | 1.43 | 11.4% | **+0.0%** (DEAD) |
| 11 | Old MA Convention (SMMA>WMA=bull) | 56 | 26.8% | 0.55 | −$2,027.30 | −0.46 | 20.3% | −104.4% |
| 12 | Higher Threshold (1.5) | 292 | 43.8% | 2.19 | $19,387.76 | 1.16 | 6.3% | −58.3% |
| 13 | Kitchen Sink OFF | 0 | — | ∞ | $0 | 0.00 | 0.0% | −100.0% |
| 14 | Tight Retest (0.3 ATR all) | 652 | 43.9% | 2.05 | $40,955.90 | 1.34 | 11.6% | −11.8% |
| 15 | Wide Retest (0.8 ATR all) | 793 | 42.5% | 1.75 | $36,245.93 | 1.17 | 14.3% | −22.0% |
| 16 | No False Breakout Filter | 333 | 39.9% | 1.11 | $2,435.89 | 0.26 | 20.1% | −94.8% |
| 17 | No Chop Filter | 733 | 43.8% | 2.05 | $46,449.95 | 1.43 | 11.4% | **+0.0%** (DEAD) |

## Critical Findings

### 1. Liquidity Sweep is THE load-bearing feature
Removing Liquidity Sweep scoring (−$47k, PF 2.05 → 0.96) flips Gold from Tier 1 to net-loss. Paired with FVG removal (test 3), the strategy is non-viable (PF 0.76). The confluence core is the real edge; everything else is second-order.

### 2. Four flags are dead code under filter-OFF production
Tests 8 (No Session Filter), 9 (No Squeeze), 10 (No Whipsaw), 17 (No Chop) produce BYTE-IDENTICAL baseline results. These four flags have zero runtime effect on Gold filter-OFF production.
**Round 7 action:** queue for removal; add a regression test that asserts strategy output is unchanged on the Round 6 baseline.

### 3. FVG at 0.5 is validated in dollar terms (sign-stable vs Round 4)
Removing FVG raises PF by 6.3% (2.05 → 2.18) but halves trade count (733 → 374) and halves dollars ($46k → $25k). FVG at 0.5 is a trade-count amplifier, not a PF amplifier — the downweight decision is correct.

### 4. Old MA Convention is definitively dead
Test 11 produced PF 0.55, −$2,027 on the **corrected four-callsite patch**. This closes the Round 3 PF 5.23 artefact investigation. That result was a single-callsite patch leak — with all four sites flipped (check_ma_cross + compute_4h_context + engine exit blocks), the old convention is Tier 4.
**Canon:** SBRS 2.0's `WMA > SMMA = bullish` convention is reconfirmed.

### 5. Counter-Trend contributes ~$29k (real edge)
Disabling counter-trend entries drops PnL from $46k to $18k. Counter-trend is legitimate profit, not noise.

### 6. Higher confluence threshold (1.5) improves PF but cuts book in half
292 trades vs 733, PF 2.19 vs 2.05. The finding is consistent with forex behaviour — tighter filtering boosts quality but thins the book. **Gold stays at 1.0/2.0 thresholds** — total dollars dominate for position sizing.

### 7. Retest tolerance is roughly flat at 0.3–0.5 ATR, degrades at 0.8
Tight (0.3): 652 trades, PF 2.05, $40,956. Wide (0.8): 793 trades, PF 1.75, $36,246. The current 0.5 ATR is near-optimal; 0.7 (Gold-long-specific) is supported.

## Feature Sign-Stability vs Round 4 (canon check)

**13/14 testable features stable in dollar sign direction.** One flip:
- **FVG PF direction flipped** (Round 4: removing FVG lowered PF; Round 6: removing FVG raises PF). Mechanism: filter-OFF now admits 16-23 GMT trades where FVG over-fires. Dollars still dominate (FVG adds $21k).

**No other reversals.** Round 4 canon on all other features (Liquidity, MA Cross, Counter-Trend, Level Gate, False Breakout, Retest, MA Convention) is preserved.

## Dead-Code Cleanup (Round 7)

| Flag | Current State | Proposed Action |
|---|---|---|
| `SESSION_BLOCK_START_HOUR` | Set to 99 (disabled sentinel) | Keep constant + `GOLD_SESSION_FILTER_ENABLED=False` as belt-and-braces (A1) |
| `is_session_blocked()` | Returns False for all 24h under sentinel | Remove helper + caller guard |
| Squeeze filter | Zero effect on entries | Remove module + confluence path |
| Whipsaw detection | Zero effect on entries | Remove module + confluence path |
| Chop filter | Zero effect on entries | Remove module + confluence path |

**Note:** these flags may have been relevant under pre-Round-5 configs. Removal requires a regression test on the Round 6 baseline to confirm zero behavioral delta.

## Open Questions

- **Y3 ATR_PCTILE_ENABLED_GOLD test:** was not run as a 19th config in this round (already-pending for Round 7). Runtime under filter-OFF may have changed its contribution.
- **Cross-instrument:** ablation suite is Gold-only. Feature signs on DAX/NASDAQ/GBPUSD are untested directly under R6 baseline.

## Reference

- Log: `logs/round6/ablation_round6.log`
- Prior rounds: [[48-Ablation-Study-Results]] (R1), [[62-Ablation-Round-2-Results]] (R2), [[66-Ablation-Round-3-Post-Change]] (R3)
- Feeds: [[73-Round-5-Remediation-Log]]
