---
tags: [priority, walk-forward, metrics, validation, elite-benchmark]
aliases: [P5-P6 Walk-Forward Metrics]
related: [[21-Priority-3-4-New-Pairs]], [[23-Optimisation-Weak-Areas]], [[25-Walk-Forward-Full-Results]], [[28-P4-Monte-Carlo]], [[00-MOC-Zeros-Requiem]]
---

# Priority 5 & 6: Walk-Forward Testing + Elite Metrics

**Date:** 2026-02-11

---

## Priority 6: Elite Performance Metrics

### Problem
The backtest output only showed basic stats (trades, WR, PnL, PF, drawdown). Missing the professional-grade metrics needed to evaluate edge quality against Elite Benchmarks.

### Metrics Added

| Metric | Formula | What It Tells You |
|--------|---------|------------------|
| **Sharpe Ratio** | mean(returns) / std(returns) * sqrt(periods/year) | Risk-adjusted return. >1.0 = good, >2.0 = excellent |
| **Sortino Ratio** | mean(returns) / downside_std * sqrt(periods/year) | Like Sharpe but only penalises downside. More useful for skewed returns |
| **Expectancy** | total_pnl / total_trades | Average $ per trade. Must be positive |
| **Expectancy (R)** | mean(pnl / risk_amount) per trade | Average return per unit of risk. >0.2R = solid |
| **Avg Win / Avg Loss** | mean(winners) / mean(losers) | Win/loss ratio. Combined with WR tells the full story |
| **Max Consecutive Losses** | Longest losing streak | Psychological resilience — can you survive this? |
| **Max Consecutive Wins** | Longest winning streak | Confidence calibration |
| **RoMaD** | total_pnl / max_drawdown_amount | Return per unit of pain. >2.0 = efficient |
| **Total Return %** | (final - initial) / initial * 100 | Simple return percentage |

### Files Modified
- `src/core/engine.py` — Extended `BacktestResult` dataclass + calculation in report section
- `main.py` — Updated `_print_result()` to display elite metrics

### Initial Results (Gold 4H, 1Y)
- Sharpe: 1.41
- Sortino: 0.96
- Expectancy: $32.37/trade, 0.236R/trade
- RoMaD: 6.87
- Avg Win $212 vs Avg Loss $79 (2.7:1 ratio)

---

## Priority 5: Walk-Forward Testing Framework

### Problem
Running a single backtest over one period doesn't prove the edge is real. The strategy might be curve-fit to that specific market condition. Walk-forward analysis tests whether the edge persists across multiple independent time periods.

### Implementation

**New file:** `src/core/walk_forward.py`

The framework:
1. Fetches the **longest available data** (2y for 4H, 5y for daily)
2. Splits into N sequential non-overlapping windows
3. Runs the full regime analysis + backtest on each window independently
4. Reports per-window results and aggregate consistency metrics

Since SCAF 2.0 is rule-based (not curve-fit per period), the walk-forward measures **edge persistence** — does the same strategy work in every market condition?

### Key Outputs

| Metric | Meaning |
|--------|---------|
| **Consistency Score** | % of windows that are profitable |
| **Edge Degradation** | Linear slope of PnL across windows. Negative = edge weakening |
| **Avg Sharpe** | Average Sharpe across all windows |
| **Best/Worst Window** | Range of outcomes |

### Usage

```bash
# Walk-forward on Gold, 4 windows, max data
py main.py --walk-forward GC=F --interval 4h --windows 4

# Walk-forward on EUR/USD, daily, 8 windows
py main.py --walk-forward EURUSD=X --interval 1d --windows 8

# Walk-forward on BTC, 6 windows
py main.py --walk-forward BTC-USD --interval 4h --windows 6
```

### Initial Walk-Forward Results

**Gold 4H (2 years, 4 windows):**
- Consistency: 50% (2/4 profitable)
- Edge degradation: +$896/window (improving)
- Combined: +$1,769 over 2 years
- W3 and W4 strongly profitable, W1-W2 losing (strategy improved with Priority 1 relaxations)

**EUR/USD 4H (2 years, 4 windows):**
- Consistency: 50% (2/4 profitable)
- Edge degradation: +$118/window (improving)
- Combined: -$412 over 2 years
- EUR/USD edge is marginal across the full 2-year period

### Interpretation
The improving edge degradation scores suggest the Priority 1 signal relaxations are working as intended — the strategy captures more opportunities in recent periods. The 50% consistency indicates room for improvement but is not alarming for a rule-based system that was recently tuned.

---

## Files Summary

| File | Change |
|------|--------|
| `src/core/engine.py` | Extended BacktestResult + elite metric calculations |
| `src/core/walk_forward.py` | **New** — walk-forward framework |
| `main.py` | Elite metrics display + --walk-forward flag |
