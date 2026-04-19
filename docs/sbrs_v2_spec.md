# SBRS 2.0 -- Sovereign Breakout Retest Strategy v2.0

## Overview

SBRS 2.0 is the evolution of SBRS 1.1, built on the same proven breakout-retest core from 3-4 years of profitable discretionary Gold trading, enhanced with smart money concepts derived from 17 documented discretionary trades.

**Key upgrades:**
- Confluence scoring replaces binary pass/fail gates
- **Corrected MA convention:** SMMA(7) > WMA(9) = bullish (matches actual discretionary trading)
- Counter-trend trades enabled with 2.0+ confluence threshold
- 2-touch minimum level quality gate (methodology: "at least two confirmed touches")

## What Changed from SBRS 1.1

| Feature | SBRS 1.1 | SBRS 2.0 |
|---------|----------|----------|
| MA Cross | Binary gate (required) | Confluence booster (+1.0 score) |
| Counter-trend trades | Blocked entirely | Allowed with score >= 2.0 |
| Fair Value Gap | Not used | Detected as confluence booster (+1.0) |
| Liquidity Sweep | Not used | Detected as confluence booster (+1.0) |
| Level Quality | Not used | 3+ touches adds +0.5 score |
| Bollinger Squeeze | Not used | First breakout rejected during squeeze |
| MA Whipsaw | Not detected | Noisy MA crosses ignored |
| False Breakout | Not tracked | Requires extra confluence (score >= 2.0) |
| Short Retest Tolerance | Same as longs (0.5 ATR) | Tighter for shorts (0.3 ATR) |
| Indices Retest Tolerance | 0.5 ATR | 0.6 ATR (wider for erratic PA) |
| Exit conditions | 6 conditions | 7 conditions (counter-trend trailing) |
| Regime tags | `sbrs_gold`, `sbrs_indices` | `sbrs_v2_gold`, `sbrs_v2_forex`, `sbrs_v2_indices` |

## Entry Model: Confluence-Scored Breakout-Retest

### Mandatory Gates (ALL must pass)

These are non-negotiable. Every trade, regardless of confluence score, must satisfy:

1. **Structure break detected** -- Price closes beyond a swing high (long) or swing low (short) identified with a 20-bar lookback and 3-bar swing confirmation window.
2. **Retest confirmed within ATR tolerance** -- Price returns to within the asset-specific ATR tolerance of the broken level and shows directional intent (candle closes in trade direction).
3. **4H trend alignment** -- For with-trend trades, the 4H trend must align (bullish for longs, bearish for shorts). Counter-trend trades are allowed but require higher confluence (score >= 2.0).

### Confluence Boosters

After mandatory gates pass, the strategy scores available confluence signals:

| Signal | Score | Description |
|--------|-------|-------------|
| Fair Value Gap (FVG) | +1.0 | A 3-candle imbalance gap is present near the breakout level |
| Liquidity Sweep | +1.0 | Price swept past a swing point then reversed (smart money trap) |
| MA Cross | +1.0 | SMMA(7) crossed WMA(9) for longs / WMA(9) crossed SMMA(7) for shorts, within 10 bars, no whipsaw |
| Level Quality | +0.5 | The broken S/R level has 3 or more confirmed touches (stronger level) |

### Score Thresholds

| Trade Type | Min Score | Requirements |
|------------|-----------|--------------|
| With-trend | >= 1.0 | Standard gates + at least 1 confluence booster |
| Counter-trend | >= 2.0 | All gates + 2 or more boosters required |
| Post-false-breakout | >= 2.0 | A prior false breakout at this level demands extra conviction |
| During squeeze | >= 1.0 | Standard score, but first breakout attempt is rejected entirely |

**Level Quality Gate:** All levels require at least 2 confirmed touches (hard gate). Levels with 3+ touches get the +0.5 bonus score.

## New Concepts

### Fair Value Gap (FVG)

A Fair Value Gap is a 3-candle imbalance where the middle candle's body creates a gap between the wicks of the surrounding candles.

**Bullish FVG:** The low of candle 3 is above the high of candle 1, with candle 2 being a large bullish candle. This gap represents unfilled buying interest -- price is likely to revisit this zone.

**Bearish FVG:** The high of candle 3 is below the low of candle 1, with candle 2 being a large bearish candle. Represents unfilled selling interest.

In SBRS 2.0, an FVG detected near the broken level adds +1.0 to the confluence score, indicating institutional participation in the breakout.

### Liquidity Sweep

A liquidity sweep occurs when price briefly pushes past a swing high or low (triggering stop losses and breakout entries) then immediately reverses. This is a smart money pattern -- institutions sweep liquidity pools before moving price in the intended direction.

In SBRS 2.0, detecting a sweep past a swing point in the trade direction adds +1.0 confluence. The detection uses the pre-computed swing high/low masks to identify swept levels.

### MA Whipsaw Detection

When WMA(9) and SMMA(7) cross each other multiple times within a short window, the signal becomes unreliable. SBRS 2.0 detects these whipsaw conditions and excludes the MA cross from the confluence score (rather than blocking the trade entirely, as v1 would).

This is critical for ranging markets where MAs oscillate rapidly around each other.

### Tight Consolidation (Bollinger Squeeze)

When Bollinger Band bandwidth compresses significantly, the market is in a tight consolidation (squeeze). First breakouts from squeezes have a high failure rate because:
- Lack of momentum behind the move
- Price often retests the range before the real breakout

SBRS 2.0 tracks breakout attempts per level. During a detected squeeze, the first breakout attempt is rejected (`SQUEEZE_REJECT_FIRST_BREAK = True`). Only the second or subsequent attempt (`SQUEEZE_MIN_BREAK_ATTEMPTS = 2`) is eligible for a trade.

### Counter-Trend Trades

SBRS 1.1 strictly blocked any trade against the 4H trend. SBRS 2.0 allows counter-trend trades under strict conditions:

- **Minimum confluence score of 2.0** (requires 2+ boosters)
- **Reduced take profit:** TP is placed at 70% of the distance to the previous swing extreme, not the full 3R target
- **Reduced R:R minimum:** 2.0 instead of 3.0 (since TP is closer)
- **Tighter trailing:** Counter-trend exits add a 7th exit condition with tighter trailing at 1.5R

This captures the high-probability reversals that an experienced discretionary trader would take, while keeping position sizing conservative.

### Failed Breakout Reversal

When a prior breakout at a specific level has already failed (SL was hit), SBRS 2.0 flags subsequent breakout attempts at that level as `false_breakout_at_level = True`. These setups require the higher confluence threshold of 2.0 (same as counter-trend) to filter out persistent false breakouts.

### False Breakout Filter

The `detect_false_breakout` function from the smart money module checks whether the current level has seen a failed breakout in recent history. This is tracked via the `breakout_attempts` dictionary, which counts how many times price has broken a specific (rounded) level.

## Exit Logic (7 Conditions)

Exit on ANY of these:

1. **Take Profit hit** -- 3R+ for with-trend, reduced for counter-trend
2. **Stop Loss hit** -- Initial or breakeven SL
3. **Breakeven move** -- At 1.5R profit, SL moves to entry + 0.1R buffer
4. **MA Cross Reversal** -- WMA(9) crosses back through SMMA(7) against position direction
5. **Structure Break** -- New swing high/low forms against the position
6. **Max Hold Time** -- 40 bars since entry
7. **Counter-trend tighter trailing** -- At 1.5R, counter-trend trades apply a tighter trailing stop

## Parameters

### Sacred Parameters (DO NOT CHANGE)

These come from real discretionary trading and are never optimized:

```
WMA_PERIOD = 9              # Weighted Moving Average period
SMMA_PERIOD = 7             # Smoothed Moving Average period
SWING_LOOKBACK = 20         # Bars to search for swing highs/lows
SWING_WINDOW = 3            # Bars on each side for swing confirmation
MIN_RR = 3.0                # Minimum Risk:Reward ratio (with-trend)
RETEST_TOLERANCE_ATR = 0.5  # Retest proximity for longs (ATR units)
```

### Tunable Parameters (can test +/-20%)

```
ATR_PERIOD = 14                   # Can test: 12-16
MAX_RETEST_WAIT = 10              # Can test: 8-12
SL_BUFFER_ATR = 0.3               # Can test: 0.24-0.36
BE_TRIGGER_R = 1.5                # Can test: 1.3-1.7
BE_BUFFER_R = 0.1                 # Buffer above breakeven
MAX_HOLD_BARS = 40                # Can test: 30-50
MA_CROSS_LOOKBACK = 10            # Can test: 8-12
TREND_CROSS_LOOKBACK = 5          # 4H MA cross recency window
CHOP_ATR_THRESHOLD = 1.0          # Range < this x ATR = choppy
CHOP_LOOKBACK = 10                # Bars to measure chop
```

### New SBRS 2.0 Parameters

```
# Confluence scoring weights
CONFLUENCE_SCORE_FVG = 1.0            # Fair Value Gap present
CONFLUENCE_SCORE_LIQUIDITY = 1.0      # Liquidity sweep detected
CONFLUENCE_SCORE_MA_CROSS = 1.0       # MA crossover confirms direction
CONFLUENCE_SCORE_LEVEL_QUALITY = 0.5  # Level has 3+ touches (bonus)

# Confluence thresholds
CONFLUENCE_MIN_WITH_TREND = 1.0       # Min score for with-trend trades
CONFLUENCE_MIN_COUNTER_TREND = 2.0    # Min score for counter-trend trades
CONFLUENCE_MIN_AFTER_FALSE_BO = 2.0   # Min score after false breakout at level

# Level quality
MIN_LEVEL_TOUCHES = 2                 # Hard gate: reject levels with < 2 touches

# Counter-trend settings
COUNTER_TREND_RR_MIN = 2.0           # Reduced R:R minimum
COUNTER_TREND_TP_FACTOR = 0.7        # TP at 70% of distance to prev swing

# Short-specific
RETEST_TOLERANCE_ATR_SHORT = 0.3     # Tighter retest for shorts

# Tight consolidation
SQUEEZE_REJECT_FIRST_BREAK = True    # Reject first breakout in squeeze
SQUEEZE_MIN_BREAK_ATTEMPTS = 2       # Require 2nd+ breakout attempt

# Session filter
SESSION_BLOCK_START_HOUR = 16        # GMT hour to stop new entries
SESSION_BLOCK_START_MINUTE = 30      # Minute cutoff (16:30 GMT)
SESSION_BLOCK_END_HOUR = 24          # Resume entries (next day)
```

## Risk Management

Unchanged from SBRS 1.1 -- the 5-layer risk management system:

1. **Per-trade risk:** 1% of account equity
2. **Position sizing:** `(equity * risk_pct) / SL_distance`
3. **Breakeven move:** At 1.5R, SL moves to entry + 0.1R
4. **Max hold time:** 40 bars
5. **Session filter:** No entries during losing sessions (16:30-24:00 GMT for Gold)

Stop loss placement:
```
LONG:  SL = Retest Low - (0.3 x ATR)
SHORT: SL = Retest High + (0.3 x ATR)
```

## Instrument Adaptations

| Instrument | Retest Tolerance (Long) | Retest Tolerance (Short) | Session Window |
|------------|------------------------|--------------------------|----------------|
| Gold | 0.5 ATR | 0.3 ATR | Block 16:30-24:00 GMT |
| Forex | 0.3 ATR | 0.3 ATR | London/NY only (07:00-16:00 GMT) |
| Indices | 0.6 ATR | 0.3 ATR | Market hours only; constrained mode available |

### Indices Session Details

| Index | Market Hours (GMT) | Constrained Mode |
|-------|-------------------|------------------|
| S&P 500 (^GSPC) | 13:30 - 20:00 | First 90 min + last 60 min |
| NASDAQ (^IXIC) | 13:30 - 20:00 | First 90 min + last 60 min |
| DAX (^GDAXI) | 07:00 - 15:30 | First 90 min + last 60 min |

## Validation Requirements

Same elite benchmarks as SBRS 1.1. ALL must be met before live deployment:

| Benchmark | Target |
|-----------|--------|
| Sharpe Ratio | >= 1.5 |
| Profit Factor | >= 1.5 |
| Annual Return | >= 20% |
| Max Drawdown | <= 15% |
| Expectancy | > 0 |
| Trade Count | 500+ per strategy |
| Walk-Forward | 5Y+ data, 8 windows, 75%+ consistency |
| Slippage | 1.5 pips modeled |
| Monte Carlo | < 5% probability of 20% drawdown |

### Red Flags (Stop and Investigate)

- Win rate > 70% (likely bug or overfit)
- Sharpe > 3.0 on walk-forward (too good to be true)
- 100% consistency across all windows (inspect code)
- Profit Factor > 3.0 average (check for data leakage)

## File Map

```
src/
  regimes/
    sbrs_v2.py           # SBRS 2.0 strategy implementation (analyze_sbrs_v2, get_sbrs_v2_indicators)
    sbrs_gold.py          # SBRS 1.1 strategy (legacy, still default)
  indicators/
    technical.py          # Core indicators: WMA, SMMA, ATR, swing detection
    smart_money.py        # SBRS 2.0 indicators: FVG, liquidity sweep, squeeze, whipsaw, level touches
  execution/
    entries.py            # TradeSetup dataclass (v2 fields: confluence_score, fvg_present, etc.)
  core/
    engine.py             # Backtest engine (accepts sbrs_v2_indicators parameter)
    walk_forward.py       # Walk-forward validation (accepts sbrs_indicator_fn callable)
    risk_manager.py       # Risk management (PROTECTED -- do not modify)
    monte_carlo.py        # Monte Carlo simulation
  data/
    fetcher.py            # Data fetching (Yahoo, OANDA, IBKR routing)
main.py                   # CLI entry point (--strategy sbrs_v2 flag)
tests/
  test_sbrs_v2.py         # Integration tests for SBRS 2.0
docs/
  sbrs_v2_spec.md         # This document
```

### CLI Usage

```bash
# Single backtest with SBRS 2.0
py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2

# Walk-forward validation with SBRS 2.0
py main.py --walk-forward GC=F --interval 1h --windows 8 --strategy sbrs_v2

# Default (SBRS 1.1)
py main.py --symbol GC=F --interval 1h --period 10y
```
