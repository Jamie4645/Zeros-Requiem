---
tags: [priority, forex, USD-JPY, AUD-USD, rejection]
aliases: [Forex Fixes, JPY Fix, AUD Rejection]
related: [[21-Priority-3-4-New-Pairs]], [[26-P1-Gold-BE-Stop-Fix]], [[28-P4-Monte-Carlo]], [[00-MOC-Zeros-Requiem]]
---

# P3: USD/JPY 4H Fix + P6: AUD/USD Rejection

**Date:** 2026-02-12

---

## P3: USD/JPY 4H — Skip Asian Range Fades

### Problem

USD/JPY on 4H was producing -$183 with 41 trades at 30% WR. The issue: the Asian range sweep-and-fade logic designed for EUR/GBP was being applied to JPY. For JPY, the Asian session IS the primary move (BoJ influence), so fading it is counter-productive.

The N1 optimisation already made JPY use breakout logic on 1H, but on 4H (`is_fast_tf = False`), JPY fell into the standard killzone fade path which includes Asian range sweeps.

### Fix

**File:** `src/regimes/forex.py` (line 362)

Added a check: when `is_jpy and not is_fast_tf`, skip Asian range sweep detection entirely. Only PDH/PDL sweeps are checked for JPY on 4H+. These are more universal levels that work regardless of session dynamics.

### Results

| Metric | Before P3 | After P3 | Change |
|--------|-----------|----------|--------|
| Trades | 41 | **10** | -31 (noise removed) |
| Win Rate | 30% | **40%** | +10pp |
| PnL | -$183 | **-$132** | +$51 |

Still slightly negative, but the drag is much smaller. USD/JPY 4H is a marginal contributor that doesn't actively hurt the portfolio anymore.

### Forex 4H Combined (After P3)

| Pair | Trades | WR | PnL | PF |
|------|--------|----|-----|-----|
| EUR/USD | 22 | 36% | +$38 | 1.03 |
| **GBP/USD** | **25** | **52%** | **+$853** | **1.68** |
| USD/JPY | 10 | 40% | -$132 | 0.74 |
| **COMBINED** | **57** | — | **+$760** | — |

---

## P6: AUD/USD — Tested and Rejected

### Hypothesis

Add AUD/USD to increase forex trade count. The killzone logic is pair-agnostic, so it should work.

### Results

**AUD/USD 4H (1Y):** 4 trades, 25% WR, **-$2,448** (24.5% drawdown!)
- Expectancy: -5.047R per trade (losses 5x larger than intended)
- Risk manager blocked 23/27 setups (massive clustering)

**AUD/USD 1H (6mo):** 1 trade, 0% WR, **-$1,636** (16.4% drawdown!)
- Risk manager blocked 65/66 setups

### Why It Failed

The killzone strategy was designed for **European majors** (EUR, GBP) where:
1. Asian session creates a liquidity range
2. London/NY opens sweep that range (trap)
3. Price reverses back (the real move)

**AUD/USD breaks this model completely:**
- AUD is a Pacific currency — the Asian session IS its primary session
- Asian range sweeps for AUD are real breakouts, not traps
- Fading them is the opposite of what you should do
- The same applies to NZD/USD (another Pacific currency)

### Key Insight

The killzone framework has a natural boundary:
- **Works:** EUR, GBP (European majors where Asia is a trap)
- **Partially works:** JPY (Asian primary move, but PDH/PDL fades OK)
- **Doesn't work:** AUD, NZD (Pacific currencies where Asia IS the move)

Forex diversification must come from **more timeframes on existing pairs** (1H + 4H + Daily on EUR/GBP), not from adding pairs that don't fit the session dynamics model.

### Decision

AUD/USD and NZD/USD will NOT be added to the portfolio. The forex universe remains: EUR/USD, GBP/USD, USD/JPY.
