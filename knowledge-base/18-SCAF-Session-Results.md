---
tags: [SCAF, results, build-session]
aliases: [SCAF Build Results]
related: [[17-SCAF-2.0-Architecture]], [[19-Priority-1-Signal-Generation]], [[00-MOC-Zeros-Requiem]]
---

# SCAF 2.0 - Build Session Results

## What Was Built

In a single session, Zeros Requiem was completely rewritten from a single-strategy price action system (v1.0-v3.0) to a regime-aware cross-asset framework (SCAF 2.0, v4.0).

### Old System (v1.0-v3.0) Problems
- Single strategy (Structure Reversal) dominated, others never triggered
- O(n^2) performance made testing impractical (20+ minute backtests)
- No session awareness (time-blind)
- No slippage modelling (unrealistic results)
- Multiple filter layers but unclear architecture

### New System (SCAF 2.0) Architecture
- Three distinct regimes: Gold, Forex, Crypto
- Session-aware (Asia, London Killzone, NY)
- Three-layer execution: Liquidity Sweep + Displacement + FVG
- Slippage modelled at 1.5 pips per trade
- 5-layer risk management
- Linear performance (backtests in <60 seconds)

## Results

### Gold 4H / 1 Year
| Sub-Regime | Trades | Win Rate | PnL | Status |
|---|---|---|---|---|
| Asia Mean Reversion | 8 | 38% | +$153 | Profitable edge |
| NY Momentum | 4 | 25% | -$165 | Too few signals |
| **Total** | **12** | **33%** | **-$12** | Near breakeven |

Asia MR was turned profitable by adding EMA trend filter (50-period slope check) and directional bias (won't short when price >1.5% above EMA). NY Momentum remains too strict due to sweep + FVG + Df alignment requirement.

### EUR/USD 4H / 1 Year
| Regime | Trades | Win Rate | PnL | Profit Factor |
|---|---|---|---|---|
| Killzone | 3 | 67% | +$360 | 3.87 |

The strongest result. Three high-quality setups during London/NY killzones with 2.50 R:R each. Profit factor of 3.87 exceeds the elite benchmark of 1.5.

### BTC-USD 4H / 1 Year
| Regime | Trades | Win Rate | PnL | Status |
|---|---|---|---|---|
| Compression | 3 | 0% | -$417 | Inconclusive (sample too small) |

After fixing false signals (14 down to 3 by requiring expansion candle + Df > 0.5), remaining trades had genuine displacement (Df 1.1-2.9) but all lost. With only 3 trades, this could be bad luck.

### Combined Across All Markets
| Metric | Value |
|---|---|
| Total Trades | 18 |
| Combined PnL | -$69 |
| Max Drawdown | 6.83% (BTC) |
| Slippage Modelled | Yes (1.5 pips) |
| Risk Management | 5 layers active |

## Key Insights

1. **EUR/USD Killzone is the strongest edge found** -- the Asian range trap with MSS confirmation and displacement produces high-quality, low-frequency signals.

2. **Gold Asia MR works when trend-filtered** -- the Bollinger Band mean reversion is profitable when you don't short into a strong uptrend.

3. **Signal count is the #1 problem** -- 18 trades across 3 markets and a year of data is nowhere near the 500+ needed for validation. The execution protocol (sweep + Df + FVG) is too strict for 4H data.

4. **Daily timeframes don't work** -- the SCAF 2.0 execution protocol is fundamentally an intraday concept. FVGs, sweeps, and killzones require sub-daily data.

5. **Slippage matters** -- all results include 1.5 pip slippage tax. Previous v1.0-v3.0 results without slippage were unrealistically optimistic.

## What Carries Into Next Session

### Priority 1: More Signals
- Test on 1H timeframe
- Allow sweep and FVG detection across 2-3 adjacent bars
- Add more forex pairs (GBP/USD, USD/JPY)
- Add ETH to crypto regime
- Relax crypto VR threshold (0.7 -> 0.8)

### Priority 2: Validation
- Walk-forward testing framework
- Sharpe/Sortino calculation
- Monte Carlo simulation
- Test over 2-5 years (not just 1)

### Priority 3: Gold NY Fix
- The sweep + FVG alignment is too strict
- Consider allowing FVG detection on the bar AFTER the sweep (not same bar)
- Or use a simpler momentum entry (displacement close) for Gold NY
