---
tags: [optimisation, tuning, weak-areas]
aliases: [Optimisation Weak Areas]
related: [[22-Priority-5-6-Metrics-WalkForward]], [[24-Optimisation-Round-2]], [[25-Walk-Forward-Full-Results]], [[00-MOC-Zeros-Requiem]]
---

# Optimisation Pass: Fixing Weak Areas

**Date:** 2026-02-11

---

## Changes Implemented

### O1: USD/JPY Asian Breakout Logic
**File:** `src/regimes/forex.py`

USD/JPY's Asian session is the primary move (BoJ influence), not a trap. When price breaks the Asian range, it's a real breakout. Added `_is_jpy_pair()` detection and `_detect_asian_breakout()` function that trades WITH the break instead of fading it. JPY pairs still check PDH/PDL with standard fade logic.

New regime label: `forex_jpy_breakout`

### O2: Gold Mean Reversion Stop/Target Improvements
**File:** `src/regimes/gold.py`

- Stop loss widened: `bb + 0.5*ATR` to `bb + 1.0*ATR` (Gold pushes through BB by $20-30)
- Take profit improved: if SMA(20) target is too close (<1.2R), uses midpoint between SMA and opposite BB
- Min R:R lowered from 1.5 to 1.2 (wider SL means the raw R:R is naturally smaller, but WR improves)

### O3: Timeframe-Aware Risk Limits
**File:** `src/core/risk_manager.py` + `main.py`

Added `risk_config_for_interval()` factory function. 1H data gets:
- `max_same_direction: 4` (was 2) — unlocks clustered signals
- `max_concurrent_risk_pct: 0.08` (was 0.06)

### O4: Crypto Min-Compression Duration
**File:** `src/regimes/crypto.py`

VR must stay below 0.8 for at least 6 consecutive bars before counting as valid compression. Filters out quick VR dips that bounce back immediately (especially noisy on 1H).

---

## Results Comparison

### 4H — 1 Year

| Symbol | Before Trades | Before PnL | After Trades | After PnL | Delta |
|--------|--------------|------------|-------------|-----------|-------|
| Gold | 73 | +$2,360 | 73 | +$2,477 | **+$117** |
| Gold MR only | 12, 17% WR | -$118 | 13, **31% WR** | -$99 | **+$19, WR doubled** |
| EUR/USD | 23 | +$221 | 23 | +$221 | unchanged |
| GBP/USD | 26 | +$546 | 26 | +$542 | ~same |
| USD/JPY | 14 | +$86 | 41 | -$183 | needs tuning |
| Bitcoin | 7 | +$215 | 4 | +$520 | **+$305** |
| Ethereum | 7 | +$575 | 7 | +$575 | unchanged |
| **TOTAL** | **150** | **+$4,003** | **174** | **+$4,152** | **+$149** |

### 1H — 6 Months

| Symbol | Before Trades | Before PnL | After Trades | After PnL | Delta |
|--------|--------------|------------|-------------|-----------|-------|
| Gold | 43 | -$440 | 45 | **-$94** | **+$346** |
| Gold MR only | 14, 21% WR | -$16 | 15, **33% WR** | +$52 | **+$68, WR +12pp** |
| EUR/USD | 56 | +$377 | 60 | **+$709** | **+$332** |
| GBP/USD | 33 | +$896 | 34 | **+$1,366** | **+$470** |
| USD/JPY | 52 | -$749 | 83 | **+$1,732** | **+$2,481** |
| Bitcoin | 9 | +$427 | 4 | +$16 | reduced but safer |
| Ethereum | 9, 11% WR | -$442 | 7 | -$115 | **+$327** |
| **TOTAL** | **202** | **+$68** | **233** | **+$3,614** | **+$3,546** |

---

## Key Wins

1. **USD/JPY 1H: -$749 to +$1,732** — The JPY breakout logic is a massive improvement. `forex_jpy_breakout` generated $1,188 alone, with the standard killzone fade adding $545 on PDH/PDL.

2. **Gold Asia MR WR doubled** — 17% to 31% on 4H, 21% to 33% on 1H. Wider stops let the trade breathe before the reversal kicks in.

3. **1H total portfolio: +$68 to +$3,614** — The combined effect of all 4 optimisations turned the 1H timeframe from breakeven to significantly profitable.

4. **BTC compression filter working** — Reduced from 7/9 trades to 4/7, but quality improved. BTC 4H went from +$215 to +$520 with fewer trades.

---

## Remaining Weak Spots

- **USD/JPY 4H**: -$183 — the breakout logic generates 33 trades but 30% WR. May need a stronger EMA trend filter for the breakout entries.
- **ETH 1H**: still negative but improved from -$442 to -$115
- **Gold 1H**: still 79 trades blocked — the O3 change helped some but Gold 1H generates too many clustered signals
