--
tags: [strategy, research, indicators]
aliases: [Smart Money, FVG, Liquidity Sweep, Smart Money Indicators]
related: [[47-SBRS-2.0-Upgrade]], [[51-Confluence-Scoring-System]], [[48-Ablation-Study-Results]], [[CLAUDE]], [[00-MOC-Zeros-Requiem]]
---

# Smart Money Indicators — SBRS 2.0

**Date added:** 2026-04-04
**File:** `src/indicators/smart_money.py`
**Used by:** `src/regimes/sbrs_v2.py`

---

## Overview

SBRS 2.0 introduced smart money concepts from the methodology document (17 discretionary trades). These are institutional price action patterns that indicate where large players are operating.

---

## Fair Value Gap (FVG) — CRITICAL (+$1,519 impact)

A 3-candle imbalance where aggressive buying/selling creates a gap between candle wicks.

**Bullish FVG:** `candle[j].High < candle[j+2].Low` — gap between candle 1 and candle 3
**Bearish FVG:** `candle[j].Low > candle[j+2].High` — inverse gap

**In SBRS 2.0:** FVG detected near the broken level adds +1.0 to confluence score. Must form during the breakout move (not just anywhere in history).

**Ablation result:** Removing FVG drops PnL from $513 to -$1,006 on pre-tuning baseline. It is the single most valuable signal after the breakout-retest pattern itself.

### Functions
- `detect_fvg_bullish(df, current_idx, lookback)` — Returns `(bar_idx, gap_low, gap_high)` or None
- `detect_fvg_bearish(df, current_idx, lookback)` — Same for bearish
- `detect_fvg_near_level(df, current_idx, level, direction, atr_val, ...)` — Checks FVG overlaps with S/R level

---

## Liquidity Sweep — VALUABLE (+$281 impact)

Price briefly pushes past a swing high/low (triggering stops), then immediately reverses. Indicates institutional manipulation.

**For longs:** Price breaks BELOW a swing low, then closes back above within 3 bars
**For shorts:** Price breaks ABOVE a swing high, then closes back below within 3 bars

**In SBRS 2.0:** Adds +1.0 to confluence score. Validates the directional move.

### Function
- `detect_liquidity_sweep(df, current_idx, swing_high_mask, swing_low_mask, direction, lookback, sweep_confirm_bars)`

---

## Level Quality (Touch Count)

Counts how many times price respected a S/R level without breaking through.

**In SBRS 2.0:** 
- Hard gate: levels need >= 2 touches to qualify (from methodology: "at least twice")
- Bonus: 3+ touches adds +0.5 to confluence score

### Function
- `count_level_touches(df, level, current_idx, atr_val, lookback, tolerance_atr)`

---

## False Breakout Detection — PROTECTIVE

Checks if a level has seen a failed breakout recently (price closed through then reversed within 3 bars).

**In SBRS 2.0:** If a false breakout was detected, the confluence threshold increases to 2.0 (same as counter-trend). Prevents entering low-quality repeated breakout attempts.

### Function
- `detect_false_breakout(df, level, direction, current_idx, atr_val, lookback, tolerance_atr)`

---

## Bollinger Squeeze

Detects tight consolidation by comparing current BB width to average. When width < 50% of average, a squeeze is detected.

**In SBRS 2.0:** Originally rejected first breakout in squeeze. Ablation showed ZERO impact on Gold — the condition never triggers during valid setups. Removed from entry loop but function preserved for indices.

### Function
- `detect_bollinger_squeeze(df, current_idx, bb_period, bb_std, squeeze_threshold, lookback)`

---

## Related

- [[51-Confluence-Scoring-System]] — How these signals combine into scores
- [[48-Ablation-Study-Results]] — Impact measurement of each signal
- [[47-SBRS-2.0-Upgrade]] — The upgrade that introduced these
- [[00-MOC-Zeros-Requiem]]
