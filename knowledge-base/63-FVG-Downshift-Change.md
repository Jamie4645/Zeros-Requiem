---
tags: [sbrs-v2, confluence, fvg, change-log]
aliases: [FVG Downshift, FVG Weight Change, Confluence FVG 0.5]
related: [[00-MOC-Zeros-Requiem]], [[62-Ablation-Round-2-Results]], [[50-Smart-Money-Indicators]], [[51-Confluence-Scoring-System]]
---

# FVG Downshift — Confluence Score 1.0 → 0.5 (2026-04-16)

## Change

In `src/regimes/sbrs_v2.py`:
```python
# BEFORE
CONFLUENCE_SCORE_FVG = 1.0

# AFTER
CONFLUENCE_SCORE_FVG = 0.5
```

## Rationale

Ablation Round 2 ([[62-Ablation-Round-2-Results]]) showed that the "No FVG" variant produced a 154% improvement over baseline on Gold 10Y. At weight +1.0, FVG alone qualifies a setup over the 1.0 with-trend threshold — meaning any setup with FVG present but no other confluence could enter. The data shows these FVG-only setups drag WR and PF down.

At weight +0.5, FVG behaves like the MA cross score: it contributes but cannot single-handedly qualify a setup. A setup must now have at least one of:
- Liquidity sweep (+1.0)
- FVG + MA cross (0.5 + 0.5 = 1.0)
- FVG + level quality (0.5 + 0.5 = 1.0)
- Liquidity + any other (well above threshold)

This restores FVG to its intended role as a **quality booster**, not a primary qualifier.

## Expected Impact (pre-run, from ablation)

The ablation's "No FVG" variant gives an upper bound:
- Gold 10Y: 327 trades → ~400 expected (FVG at 0.5 still fires half the time)
- PF: 1.31 → expected 1.6–1.9 range
- Sharpe: 0.64 → expected 0.9–1.1 range
- DD: 10.1% → expected 7–9% range

## Post-Change Validation (2026-04-16, completed)

Ran after applying FVG 1.0→0.5 + Gold DD cap 20% + squeeze/chop/whipsaw code deletion + main.py default→sbrs_v2.

### Walk-Forward Results (8 windows each)

| Instrument | Metric | Pre-change | Post-change | Δ |
|---|---|---|---|---|
| **Gold 1H** | WF consistency | 62% (5/8) | **100% (8/8)** ✅ | +38 pts |
| Gold 1H | WF total trades | — | 641 | |
| Gold 1H | Avg PF | — | 1.47 | |
| Gold 1H | Avg Sharpe | — | 0.98 | |
| Gold 1H | Best window | — | +$4,478.12 | |
| Gold 1H | Worst window | — | +$154.06 | (no losers) |
| Gold 1H | Combined PnL | — | +$16,608.17 | |
| **DAX 1H** | WF consistency | 88% (7/8) | **100% (8/8)** ✅ | +12 pts |
| DAX 1H | WF total trades | — | 456 | |
| DAX 1H | Avg PF | — | 1.57 | |
| DAX 1H | Avg Sharpe | — | 0.96 | |
| DAX 1H | Best window | — | +$2,513.97 | |
| DAX 1H | Worst window | — | +$330.28 | (no losers) |
| DAX 1H | Combined PnL | — | +$11,615.18 | |
| **GBPUSD 1H** | WF consistency | 62% (5/8) | **62% (5/8)** ⚠️ | no change |
| GBPUSD 1H | WF total trades | 1,323 | 480 | -64% |
| GBPUSD 1H | Avg PF | 2.69 (single-BT) | 1.09 (WF avg) | degradation |
| GBPUSD 1H | Avg Sharpe | 2.00 (single-BT) | 0.19 (WF avg) | degradation |
| GBPUSD 1H | Best window | — | +$1,483.32 | |
| GBPUSD 1H | Worst window | — | -$1,071.55 | improved from -$2,013 |
| GBPUSD 1H | Combined PnL | — | +$2,191.43 | |

### Single-Backtest Results (where OANDA fetch succeeded)

| Instrument | Metric | Pre-change | Post-change | Δ |
|---|---|---|---|---|
| **DAX 1H BT** | Trades | 1,230 | 457 | -63% |
| DAX 1H BT | Win Rate | 41.8% | 49.2% | +7.4 pts |
| DAX 1H BT | PF | 1.34 | 1.96 | +46% |
| DAX 1H BT | Sharpe | 0.88 | 1.21 | +38% |
| DAX 1H BT | Max DD | 11.41% | 7.92% | -31% |
| **NASDAQ 1H BT** | Trades | 888 | 532 | -40% |
| NASDAQ 1H BT | Win Rate | 45.3% | 46.2% | +0.9 pts |
| NASDAQ 1H BT | PF | 1.57 | 3.49 ⚠️ | red-flag (>3.0) |
| NASDAQ 1H BT | Sharpe | 1.11 | 1.81 | +63% |
| NASDAQ 1H BT | Max DD | 17.84% | 5.06% | -72% |

### Failed Fetches (OANDA 502 Bad Gateway — retry pending)

- Gold 1H full 10Y backtest
- GBPUSD 1H full 10Y backtest
- NASDAQ 1H walk-forward

These will be re-run when OANDA API recovers. WF results above used cached/partial data where available.

### Interpretation

**Clear wins:**
- Gold WF consistency jumped 62% → 100% (best explained by DD cap fix recovering ~1,500 previously-blocked trades — see [[64-Risk-Manager-Gold-Cap-Fix]])
- DAX WF consistency jumped 88% → 100%, PF 1.34 → 1.96 single-BT
- NASDAQ BT Sharpe 1.11 → 1.81

**Red flags:**
- NASDAQ PF 3.49 triggers CLAUDE.md >3.0 alert — already assigned to arbiter-risk
- GBPUSD WF did NOT improve (still 62%); trade count dropped 64%. FVG downshift appears to have hurt FX specifically. Flagged to arbiter-forex.

**Unknowns:**
- Monte Carlo on Gold/DAX/NASDAQ not yet re-run post-change
- Pre-change WF numbers for Gold (75%), NASDAQ (88%) were on different baselines than the "413-trade Gold" row — the pre-change "413 trades" was the post-first-DD-cap-regression state, not the historic baseline. The pre/post here reflects code-state changes, not the full 2.0 history.

## Rollback Plan

If post-change results show net degradation (lower combined PnL across all assets vs pre-change), revert by setting `CONFLUENCE_SCORE_FVG = 1.0` and re-run. Keep both versions tagged in git for A/B comparison.

## Related

- [[62-Ablation-Round-2-Results]] — The full ablation that motivated this change
- [[50-Smart-Money-Indicators]] — How FVG is detected
- [[51-Confluence-Scoring-System]] — Overall confluence architecture
- [[64-Risk-Manager-Gold-Cap-Fix]] — Companion change in this release
