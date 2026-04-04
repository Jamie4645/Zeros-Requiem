---
tags: [sbrs, parameters, reference, sacred]
aliases: [SBRS Parameters, Parameters Reference]
---

# SBRS 1.1 — Parameters Reference

> Locked reference of all SBRS parameters. Core parameters come from 3-4 years of profitable discretionary trading. DO NOT OPTIMIZE.

**Source file**: `src/regimes/sbrs_original_parameters.py` (locked 2026-02-15)

---

## Core Parameters (SACRED — DO NOT CHANGE)

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `WMA_PERIOD` | 9 | Weighted Moving Average period |
| `SMMA_PERIOD` | 7 | Smoothed Moving Average period |
| `SWING_LOOKBACK` | 20 | Bars to search for swing highs/lows |
| `SWING_WINDOW` | 3 | Bars on each side for swing confirmation |
| `MIN_RR` | 3.0 | Minimum risk:reward ratio to enter |
| `RETEST_TOLERANCE_ATR` | 0.5 | How close retest must be to broken level (longs) |
| `RETEST_TOLERANCE_ATR_SHORT` | 0.3 | Tighter retest tolerance for shorts |

---

## Tunable Parameters (±20% range ONLY)

| Parameter | Value | Test Range | Purpose |
|-----------|-------|------------|---------|
| `ATR_PERIOD` | 14 | 12–16 | ATR calculation period |
| `MAX_RETEST_WAIT` | 10 | 8–12 | Max bars to wait for retest after break |
| `SL_BUFFER_ATR` | 0.3 | 0.24–0.36 | SL distance beyond retest extreme |
| `BE_TRIGGER_R` | 1.5 | 1.3–1.7 | Move SL to breakeven at this R-multiple |
| `BE_BUFFER_R` | 0.1 | — | Buffer above breakeven |
| `MAX_HOLD_BARS` | 40 | 30–50 | Force close after this many bars |
| `MA_CROSS_LOOKBACK` | 10 | 8–12 | Bars to search for recent MA cross on 1H |
| `TREND_CROSS_LOOKBACK` | 5 | — | "Recently crossed" lookback on 4H |
| `CHOP_ATR_THRESHOLD` | 1.0 | — | Range < this × ATR = choppy (skip entry) |
| `CHOP_LOOKBACK` | 10 | — | Bars to measure choppiness |

---

## Session Filter

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `SESSION_BLOCK_START_HOUR` | 16 | GMT hour to stop new entries |
| `SESSION_BLOCK_START_MINUTE` | 30 | Minute cutoff (16:30 GMT) |
| `SESSION_BLOCK_END_HOUR` | 24 | Resume entries (next day Asia open) |

**Rationale**: 16:30–24:00 GMT consistently loses money on Gold (-$660 over 10Y).

---

## Index-Specific Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `INDICES_RETEST_TOLERANCE_ATR` | 0.5 | Retest tolerance for indices |
| `INDICES_OPEN_WINDOW_MINUTES` | 90 | First 90 min after open — high volatility window |
| `INDICES_CLOSE_WINDOW_MINUTES` | 60 | Last 60 min before close — closing auction window |

### Index Market Hours (GMT)

| Index | Open | Close |
|-------|------|-------|
| S&P 500 (`^GSPC`) | 13:30 | 20:00 |
| NASDAQ (`^IXIC`) | 13:30 | 20:00 |
| DAX (`^GDAXI`) | 07:00 | 15:30 |

---

## Engine Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `SBRS_BE_TRIGGER_R` | 1.5 | Engine-side breakeven trigger |
| `SBRS_BE_BUFFER_R` | 0.1 | Engine-side breakeven buffer |
| `SBRS_MAX_HOLD_BARS` | 40 | Engine-side max hold timeout |
| `SBRS_TRAILING_TRIGGER_R` | 3.0 | Trailing stop trigger (at TP level) |

---

## Related

- [[CLAUDE]] — Full strategy spec with entry/exit logic
- [[44-Live-Runner-Architecture]] — How parameters are used in live trading
- [[00-MOC-Zeros-Requiem]]
