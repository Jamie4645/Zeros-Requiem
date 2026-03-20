---
tags: [priority, gold, daily, bug-fix]
aliases: [P2 Gold Daily Fix]
related: [[19-Priority-1-Signal-Generation]], [[21-Priority-3-4-New-Pairs]], [[25-Walk-Forward-Full-Results]], [[00-MOC-Zeros-Requiem]]
---

# Priority 2: Fix Gold Daily (0 Trades)

**Date:** 2026-02-11
**Goal:** Make Gold Daily produce meaningful trade signals by adapting the execution protocol to daily candle structure.

---

## Problem Diagnosis

Gold Daily produced **0 trades** because of 4 compounding issues:

1. **Only PDH/PDL as liquidity levels** -- on daily data, session levels don't exist. The only sweep targets were yesterday's high/low, which is too limiting.

2. **Sweep pattern is intraday by nature** -- requiring price to poke beyond a level and close back inside on the same candle is rare on daily Gold. Gold trends heavily -- when it breaks yesterday's high, it usually keeps going.

3. **Mean reversion was disabled** -- daily data was forced into NY Momentum mode only. The Bollinger Band mean reversion strategy (which is well-suited to daily data) was never run.

4. **FVG tolerance too tight for daily candles** -- daily Gold candles are ~$30-50 range. The 0.1 ATR near-FVG tolerance from Priority 1.1 was still too strict for these larger candles.

---

## Changes Implemented

### 2.1 -- Weekly Level Sweeps
**File:** `src/execution/liquidity.py`

Added `get_weekly_levels()` as a shared utility function. Returns the high/low of the last N bars (7 for daily, 40 for 4H). Updated `scan_for_sweeps()` to accept `weekly_high` and `weekly_low` parameters.

Gold Daily now scans weekly highs/lows as sweep targets. These are the most natural liquidity pools on a daily timeframe -- retail traders cluster stops above/below the week's range.

### 2.2 -- Swing High/Low Detection
**File:** `src/execution/liquidity.py`

Added `get_swing_levels()` that detects the most recent swing high and swing low using a configurable window (default: 3 bars on each side). A swing high is a bar whose high exceeds the highs of the 3 bars before and after it.

Gold Daily now scans swing levels as sweep targets. These represent natural support/resistance where institutional orders accumulate.

Updated `scan_for_sweeps()` to accept `swing_high` and `swing_low` parameters.

### 2.3 -- Bollinger Band Mean Reversion on Daily
**File:** `src/regimes/gold.py`

**Structural change:** On daily data, the engine now runs **both** mean reversion AND momentum modes on every bar (not either/or). Previously, daily data was forced into NY Momentum only.

- Mean reversion uses the same BB(20, 2.5) fade logic as Asia session
- Daily MR has a relaxed EMA slope filter (3% vs 2% for intraday)
- Daily MR trades are labelled `gold_daily_mr` for tracking
- Daily momentum trades are labelled `gold_daily_momentum`

This is sound because daily BB mean reversion is one of the most statistically studied strategies in technical analysis. It works differently from intraday MR but the principle is the same.

### 2.4 -- Wider Near-FVG Tolerance for Daily
**File:** `src/regimes/gold.py`

Near-FVG `overlap_tolerance_atr` is now **0.2** for daily data (was 0.1). Daily Gold candles are 2-3x larger than 4H candles, so the tolerance scales proportionally. Intraday data keeps the 0.1 ATR tolerance from Priority 1.1.

---

## New Liquidity Level Hierarchy (Gold Daily)

| Level | Source | Priority |
|-------|--------|----------|
| PDH/PDL | Previous day's high/low | Built-in (scan_for_sweeps) |
| Weekly H/L | Last 7 bars' high/low | Priority 2.1 |
| Swing H/L | 20-bar lookback, 3-bar window | Priority 2.2 |

All three are scanned on every daily bar, giving the sweep detection 6 potential targets instead of just 2.

---

## New Regime Labels

| Label | Description |
|-------|-------------|
| `gold_asia_mr` | Intraday Asia session Bollinger Band mean reversion |
| `gold_daily_mr` | Daily Bollinger Band mean reversion (new) |
| `gold_ny_momentum` | Intraday NY session sweep + displacement |
| `gold_daily_momentum` | Daily sweep + displacement (new) |

---

## Expected Impact

- **0 trades -> 20-50+ trades/year** on Gold Daily
- Mean reversion alone should generate ~10-20 signals/year (BB touches)
- Weekly + swing level sweeps should unlock ~10-30 momentum signals/year
- Combined with Priority 1 relaxations, could exceed 50 trades/year

---

## Risk Notes

- Daily mean reversion uses the same trend filters as intraday (EMA slope + directional bias) so it won't blindly fade strong trends
- Swing level detection uses a 3-bar window on each side, which is conservative enough to avoid noise
- Weekly levels might occasionally duplicate with PDH/PDL -- this is acceptable since the sweep must still pass all validation layers
