---
tags: [architecture, SCAF, framework, core]
aliases: [SCAF 2.0, SCAF Architecture]
related: [[CLAUDE]], [[18-SCAF-Session-Results]], [[19-Priority-1-Signal-Generation]], [[29-P5-P7-P8-OANDA-Portfolio]], [[00-MOC-Zeros-Requiem]]
---

# SCAF 2.0 - Sovereign Cross-Asset Framework

## Overview

SCAF 2.0 is a complete rewrite of Zeros Requiem. It replaces the old single-strategy system with a regime-aware architecture that adapts its trading logic based on the asset class and session.

## Why the Rewrite

The v1.0-v3.0 system had fundamental limitations:
- Applied the same logic regardless of session or market state
- Only one strategy (Structure Reversal) consistently produced trades
- O(n^2) performance made testing impractical on intraday data
- No session awareness (time-blind)

SCAF 2.0 addresses all of these by using distinct regimes per asset class with session-specific logic.

## The Three-Layer Execution Protocol

Every trade must pass three independent validations:

**Layer 1: Liquidity Grab**
- Has a significant pool of retail stops been cleared?
- Checks PDH, PDL, Session High/Low, Asian Range boundaries
- ATR-relative sweep distance (not fixed pips)

**Layer 2: Displacement Factor (Df)**
- Df = (body_current - mean(body_50)) / std(body_50)
- Only proceed if Df > 2.0 (2 standard deviations above average body)
- Ensures institutional participation, not just retail noise

**Layer 3: Fair Value Gap (FVG) Entry**
- Created by the displacement candle (3-candle pattern)
- Entry at FVG midpoint (limit order)
- Better entry price than breakout, pre-defined risk levels

## Asset Regimes

### Gold (XAUUSD)

**Asia Session (00:00-08:00 GMT): Mean Reversion Mode**
- Bollinger Band (20, 2.5 sigma) extremes
- Fade back to 20-SMA when price touches band
- Trend filter: only mean-revert when SMA slope < 0.1%/bar

**NY Overlap (12:00-16:00 GMT): Momentum Drive Mode**
- Scan for liquidity sweeps at PDH/PDL/session levels
- Confirm with Displacement Factor > 2.0
- Enter at FVG midpoint

### Forex (Majors) -- [TODO]

**Killzone Logic: London (08:00-11:00) + NY (13:00-16:00)**
- Identify Asian Session Range (High/Low)
- Wait for Liquidity Sweep (price pokes beyond range)
- Confirm Market Structure Shift (MSS) back into range
- Enter at FVG with Df > 2.0

### Crypto (BTC/ETH) -- [TODO]

**Volatility Compression Mode**
- Monitor VR = ATR(5) / ATR(50)
- VR < 0.7 = High Alert
- Trigger: sweep of Weekly High/Low or CME Gap
- Confirm: expansion candle (body > 80% of range)

## Risk Management (5 Layers)

1. **Per-trade sizing**: PositionSize = (Equity * 0.01) / (ATR(14) * 2)
2. **Daily loss limit**: 3% max loss per day
3. **Drawdown circuit breaker**: 10% from peak = pause
4. **Max concurrent risk**: 6% across all positions
5. **Correlation check**: max 2 trades in same direction

## Slippage Tax

All backtests include a 1.5 pip slippage tax per trade to simulate retail execution conditions. This is applied to both entry and exit prices.

## File Structure

```
src/
  core/engine.py          -- Backtest engine
  core/risk_manager.py    -- 5-layer risk management
  regimes/gold.py         -- Gold Asia + NY regimes
  regimes/forex.py        -- [TODO]
  regimes/crypto.py       -- [TODO]
  execution/liquidity.py  -- Sweep detection
  execution/displacement.py -- Df + FVG
  execution/entries.py    -- Three-layer validation
  indicators/technical.py -- All indicators
  indicators/candlestick.py -- Pattern detection
  data/fetcher.py         -- Yahoo Finance
```
