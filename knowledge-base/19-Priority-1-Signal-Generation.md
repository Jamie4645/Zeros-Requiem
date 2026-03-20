---
tags: [priority, signal-generation, SCAF, optimisation]
aliases: [P1 Signal Generation]
related: [[17-SCAF-2.0-Architecture]], [[18-SCAF-Session-Results]], [[20-Priority-2-Gold-Daily-Fix]], [[00-MOC-Zeros-Requiem]]
---

# Priority 1: Increase Signal Generation

**Date:** 2026-02-11
**Goal:** Increase from ~18 trades/year to 400-800+ for statistical validation (500+ per strategy target)

---

## Problem

With only 18 trades across 3 markets (Gold, Forex, Crypto), nothing is statistically meaningful. The 5 Fundamental Truths demand 500+ trades per strategy before drawing conclusions. The root cause was overly strict detection criteria designed for textbook-perfect setups that rarely occur on higher timeframes.

---

## Changes Implemented

### 1.1 — Near-FVG Tolerance (HIGHEST IMPACT)
**File:** `src/execution/displacement.py`

- **Before:** Required a complete price gap — candle[i]'s low strictly above candle[i-2]'s high (bullish). Almost never happens on 4H/Daily.
- **After:** Added `overlap_tolerance_atr` parameter (default 0.1 ATR). If candles overlap by less than 10% of ATR, it's still treated as a "near-FVG". The gap zone is constructed from the midpoint of the overlapping wicks, sized at 25% of the displacement candle's body.
- **New field:** `is_near_fvg: bool` on `FairValueGap` dataclass to track which FVGs are partial.

### 1.2 — Multi-Bar Sweep Detection
**File:** `src/execution/liquidity.py`

- **Before:** Required the poke beyond AND close back on the *same* candle. Many real sweeps take 2-3 bars.
- **After:** Added `sweep_lookback` parameter (default 3). Looks back up to 3 bars for the poke, uses current bar's close for confirmation. The `sweep_extreme` is the most extreme wick in the window.

### 1.3 — Widened Sweep Tolerance
**File:** `src/execution/liquidity.py`

- **Before:** `sweep_tolerance_atr_mult = 0.3` — only 0.3x ATR beyond the level counted.
- **After:** Default raised to `0.5` ATR. Gold frequently pokes 0.4-0.5 ATR beyond levels before reversing.

### 1.4 — Lowered Displacement Factor Thresholds
**Files:** All regimes + `src/execution/entries.py`

| Path | Before | After |
|------|--------|-------|
| FVG detection (`detect_fvg` calls) | min_df = 1.5 | min_df = 1.0 |
| Displacement fallback (all regimes) | Df >= 1.0 (Gold/Crypto), Df >= 1.5 (Forex) | Df >= 0.75 (all) |
| `validate_entry` default | min_df = 1.5 | min_df = 1.0 |

### 1.5 — Relaxed Expansion Candle (Crypto)
**File:** `src/regimes/crypto.py`

- **Before:** `threshold=0.75` — body must be 75% of range.
- **After:** `threshold=0.65` — 65% body/range ratio. Still filters dojis but allows moderate-wick candles.

### 1.6 — Widened EMA Trend Filter Distances
**Files:** All regimes

| Regime | Before | After |
|--------|--------|-------|
| Gold (Asia MR) | 1.5% from EMA | 2.5% |
| Gold (NY fallback) | 1.5% from EMA | 2.5% |
| Crypto | 2% from EMA | 3% |
| Forex | 1% from EMA | 2% |

### 1.7 — Removed MSS Lookahead Bias (Forex)
**File:** `src/regimes/forex.py`

- **Before:** `_detect_mss()` checked the *next* bar's close to confirm direction change. This is future peeking in a backtest.
- **After:** MSS is confirmed by the sweep itself — `detect_liquidity_sweep` already requires the candle's close to be back inside the level. That close-back IS the market structure shift. No additional confirmation needed.

---

## Expected Impact

| Change | Impact Level | Rationale |
|--------|-------------|-----------|
| 1.1 Near-FVG | **VERY HIGH** | Was filtering 90%+ of potential setups on higher TFs |
| 1.2 Multi-bar sweep | **HIGH** | Many institutional sweeps take 2-3 candles |
| 1.3 Wider sweep tolerance | **MEDIUM** | Catches more aggressive sweeps |
| 1.4 Lower Df thresholds | **HIGH** | Df 1.5 is extremely strict (top ~7% of candles) |
| 1.5 Expansion candle | **LOW-MEDIUM** | Crypto-specific |
| 1.6 Wider EMA filters | **MEDIUM** | Stops filtering in moderate trends |
| 1.7 MSS fix | **MEDIUM** | Fixes bias + increases signals |

**Combined estimate:** 10-20x increase in signal count. With 1H timeframe data (next step), could reach 400-800+ trades per strategy.

---

## Risk Management

Each relaxation trades strictness for volume. Key safeguards still in place:
- Sweep must still poke beyond AND close back (just multi-bar now)
- FVG/near-FVG still requires institutional displacement (Df >= 1.0)
- EMA trend filter still active (just wider)
- Risk/reward minimum still 1.5:1
- Position sizing unchanged (1% risk per trade)
- All 5 risk management layers unchanged

---

## Next Steps (Remaining Priorities)

- **Priority 2:** Fix Gold Daily (0 trades — FVG logic on daily candles)
- **Priority 3:** Add GBP/USD, USD/JPY
- **Priority 4:** Add ETH alongside BTC
- **Priority 5:** Walk-forward testing framework (5+ years)
- **Priority 6:** Sharpe/Sortino/Expectancy in reports
