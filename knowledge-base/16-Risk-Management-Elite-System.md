---
tags: [risk-management, core, elite-benchmark]
aliases: [Risk Management, 5-Layer Risk]
related: [[CLAUDE]], [[33-Tool-Protected-Files-Hook]], [[28-P4-Monte-Carlo]], [[00-MOC-Zeros-Requiem]]
---

# Risk Management: Elite 5-Layer System (v3.0)

## Overview

v3.0 implements professional-grade risk management that matches what the top 1% of independent algo traders use. This is not optional -- it's what separates sustainable profitability from account blow-ups.

**The Philosophy:** Capital preservation comes before trade frequency. A system that never breaches a 10% drawdown over 5 years will outlast and outperform a system that occasionally has 30% drawdowns even if the latter has higher peak returns.

## The 5 Layers

### Layer 1: Daily Loss Limit (Critical)

**What it does:** Stops all trading if the account loses more than X% in a single day.

**Default:** 3% maximum loss per day

**Why it matters:** Prevents catastrophic "tilt" scenarios where multiple bad trades compound in one session. Without this, a streak of 5-6 bad trades in one day could create a 10-15% drawdown. With it, you're capped at 3% and live to trade tomorrow.

**How it works:**
- At the start of each trading day, `daily_start_capital` is recorded
- As trades close, `daily_pnl` is tracked
- If `daily_pnl < -(daily_start_capital * 0.03)`, no new trades are allowed until the next day
- The algorithm will still manage open trades (trail stops, exit at SL/TP)

**Config parameter:** `max_daily_loss_pct` (default 0.03 = 3%)

### Layer 2: Drawdown Circuit Breaker (Critical)

**What it does:** Pauses ALL trading if the account drops more than X% from its peak equity.

**Default:** 10% maximum drawdown from peak

**Why it matters:** This is the single most important risk control. Every professional trader has this. It forces you to stop, review what went wrong, and fix the system before continuing. Most retail traders blow up because they keep trading through a 20-30% drawdown hoping to recover.

**How it works:**
- `peak_equity` is tracked (highest account value ever reached)
- Current drawdown = `(peak_equity - current_capital) / peak_equity`
- If drawdown >= 10%, trading is paused
- Once the account recovers back above 90% of peak (drawdown < 10%), trading resumes automatically

**Config parameter:** `max_drawdown_pct` (default 0.10 = 10%)

**Elite benchmark:** This limit aligns directly with your target of <=15% max drawdown. By setting it at 10%, you have a 5% buffer before breaching the benchmark.

### Layer 3: Max Concurrent Risk (High Priority)

**What it does:** Limits the total dollar risk across all open positions simultaneously.

**Default:** 6% of capital

**Why it matters:** Without this, you could have 3 open trades each risking 2% (your `risk_per_trade` setting), but if all 3 are correlated (e.g., all long commodities), your real risk is 6%. If they all hit stop loss on the same day, that's a 6% loss in one session -- double your daily loss limit. This layer caps the cumulative exposure.

**How it works:**
- Before opening a trade, calculate `trade_risk = abs(entry - stop_loss) * position_size`
- Sum up risk of all currently open trades
- If `total_risk + new_trade_risk > capital * 0.06`, the new trade is blocked

**Config parameter:** `max_concurrent_risk_pct` (default 0.06 = 6%)

**Real example:**
- Capital: $10,000
- Max concurrent risk: $600 (6%)
- Open trade 1: risking $200
- Open trade 2: risking $300
- Total risk: $500
- New trade would risk $150 -> $500 + $150 = $650 > $600 -> **BLOCKED**

### Layer 4: Position Correlation Check (Medium Priority)

**What it does:** Prevents opening multiple highly-correlated positions that are effectively the same bet.

**Default:** Don't open a second trade from the same strategy if directional concentration >70%

**Why it matters:** Gold and Silver are ~85% correlated. EUR/USD and GBP/USD are ~90% correlated. If you're long both, you're not diversifying -- you're doubling down on the same bet. This layer provides a simplified correlation check.

**How it works (simplified version implemented):**
- Counts open trades from the same strategy (structure_reversal, consolidation_rectangle, etc.)
- Checks directional concentration (% of trades that are long vs short)
- If >70% of trades are in one direction AND you already have a trade from this strategy, block the new one
- This is a proxy for correlation without needing full asset-level correlation matrices

**Config parameter:** `check_correlation` (default True)

**Future enhancement:** A full implementation would check actual asset correlations (e.g., Gold vs Silver 0.85, Gold vs EUR/USD 0.30) and enforce a `max_correlation_exposure` limit.

### Layer 5: Kelly-Based Position Sizing (Optional)

**What it does:** Dynamically adjusts position size based on recent performance.

**Default:** Disabled (set `use_kelly_sizing=False`)

**Why it's optional:** Kelly sizing can be aggressive and requires a stable, proven edge. Enable it only after:
1. You've validated the system with 500+ trades
2. Walk-forward testing shows consistent performance
3. You're confident the edge is real

**How it works:**
- Tracks last 50 trades (wins, losses, avg win, avg loss)
- Calculates full Kelly: $f^* = \frac{(p \times b - q)}{b}$ where $p$ = win rate, $b$ = avg win / avg loss
- Applies fractional Kelly (1/4 by default): `kelly_adjusted = kelly_full * 0.25`
- Scales `risk_per_trade` up or down based on Kelly suggestion (capped at 2x)
- If recent performance is strong (60% WR, 2:1 avg), Kelly scales up to ~2%
- If recent performance is weak (45% WR, 1:1 avg), Kelly scales down to ~0.75%

**Config parameters:**
- `use_kelly_sizing` (default False)
- `kelly_fraction` (default 0.25 = 1/4 Kelly, conservative)
- `kelly_lookback` (default 50 = use last 50 trades)

**Warning:** Full Kelly is mathematically optimal but practically suicidal. It can suggest risking 30-40% per trade. ALWAYS use fractional Kelly (1/4 to 1/10).

## When Risk Limits Trigger

**Example scenario on Gold 4H:**
- Starting capital: $10,000
- Day 1 trades: -$120, -$150, -$80 = -$350 total
- Daily loss limit: $300 (3%)
- **Circuit breaker trips** -- no more trades today
- Day 2: Resets, trading resumes

**Example scenario on drawdown:**
- Peak equity: $11,500
- Series of losses brings capital to $10,300
- Drawdown = ($11,500 - $10,300) / $11,500 = 10.43%
- **Drawdown breaker trips** -- all trading paused
- Manual review required (in live trading)
- In backtest: pauses until equity recovers to $10,350 (9.6% drawdown)

## Config Defaults

All risk management is enabled by default with conservative settings:

| Parameter | Default | Elite Standard | Notes |
|---|---|---|---|
| `use_risk_manager` | True | Always | Don't disable |
| `max_daily_loss_pct` | 0.03 (3%) | 2-3% | Conservative |
| `max_drawdown_pct` | 0.10 (10%) | 10-15% | Aligned with benchmark |
| `max_concurrent_risk_pct` | 0.06 (6%) | 5-8% | Conservative |
| `check_correlation` | True | Always | Simplified version |
| `use_kelly_sizing` | False | After 500+ trades | Too risky initially |
| `kelly_fraction` | 0.25 (1/4) | 1/4 to 1/10 | Never use full Kelly |

## Impact on Backtest Results

Risk management will:
- **Reduce trade count** when limits are hit (this is good -- it prevents compounding losses)
- **Improve max drawdown** by stopping trading before catastrophic losses
- **Reduce total return in some cases** if the algorithm would have recovered after being paused
- **Improve Sharpe ratio** by cutting the tail risk

If the risk manager blocks >10% of your trades, your edge is weak or your limits are too tight. Investigate why it's intervening.

## Files Changed

- `src/risk_manager.py` -- NEW: RiskManager class with all 5 layers
- `src/strategy.py` -- RiskManager integration, config parameters
- `main.py` -- Risk management stats display

## How to Adjust Limits

Conservative (recommended during testing):
```python
config.max_daily_loss_pct = 0.02  # 2%
config.max_drawdown_pct = 0.08    # 8%
config.max_concurrent_risk_pct = 0.04  # 4%
```

Aggressive (only after 500+ validated trades):
```python
config.max_daily_loss_pct = 0.05  # 5%
config.max_drawdown_pct = 0.15    # 15%
config.max_concurrent_risk_pct = 0.10  # 10%
config.use_kelly_sizing = True
```

Never disable:
```python
config.use_risk_manager = False  # DON'T DO THIS
```

The risk manager is your safety net. It's what prevents a bad week from becoming a blown account.
