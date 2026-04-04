---
tags: [trading, book-analysis, forex, pipeline]
aliases: [Kathy Lien Book Analysis, Day Trading Currency Market Strategies]
---

# Day Trading and Swing Trading the Currency Market (2nd Ed) — Book Analysis

> **Author:** Kathy Lien | **Year:** 2008 (2nd Edition) | **Focus:** Forex-specific strategies
> **Publisher:** Wiley Trading | **Pages:** ~307

---

## Overview

Kathy Lien's book is one of the most practical forex strategy books available, combining microstructure insights (order flow, round numbers, stop hunting), session-based strategies, fundamental analysis, and clean mechanical rules. Unlike many trading books, nearly every strategy includes specific entry/exit rules with exact indicator parameters.

**Strategies extracted:** 14 codifiable systems | **Additional concepts:** 8 frameworks | **Market focus:** Forex only

---

## Strategy Summary Table

| # | Strategy | Type | Timeframe | Best Pairs | Clarity | Completeness |
|---|----------|------|-----------|-----------|---------|-------------|
| 1 | [[Double Zero Fade]] | Mean-Reversion | Intraday (10-15m) | USD/JPY, crosses | 9 | 9 |
| 2 | [[London Open Real Deal]] | Breakout | Intraday (15-30m) | GBP/USD only | 8 | 8 |
| 3 | [[Inside Day Breakout]] | Breakout | Swing (Daily) | EUR/GBP, USD/CAD, EUR/CHF | 9 | 9 |
| 4 | [[The Fader - False Breakout]] | Mean-Reversion | Intraday (Hourly) | Less volatile pairs | 9 | 8 |
| 5 | [[20-Day False Breakout Filter]] | Trend-Following | Swing (Daily) | All majors | 9 | 9 |
| 6 | [[Channel Breakout FX]] | Breakout | Intraday/Swing | Any channeling pair | 8 | 7 |
| 7 | [[Perfect Order MA Strategy]] | Trend-Following | Swing (Daily) | EUR/USD, USD/CHF, USD/CAD | 8 | 8 |
| 8 | [[News Proactive Trading]] | News | Intraday (5m) | Release-specific pair | 8 | 8 |
| 9 | [[News Reactive Trading]] | News | Intraday (5m) | Release-specific pair | 8 | 8 |
| 10 | [[News Combined Pro-Reactive]] | News | Intraday (5m) | Release-specific pair | 8 | 8 |
| 11 | [[20-100 Momentum Strategy]] | Momentum | Intraday (5m) | All liquid majors | **10** | **10** |
| 12 | [[High Probability Turn Strategy]] | Mean-Reversion | Swing (Daily) | EUR/USD, GBP/USD, USD/JPY | **10** | **10** |
| 13 | [[Leveraged Carry Trade]] | Carry | Position (6mo+) | AUD/JPY, NZD/JPY, AUD/CHF | 7 | 7 |
| 14 | [[Bond Spread Leading Indicator]] | Trend-Following | Swing/Position | AUD/USD, GBP/USD, USD/CAD | 7 | 6 |

---

## Top 3 Strategies (Most Codifiable)

### 1. 20-100 Short-Term Momentum Strategy (Ch. 9, pp. 150-155)

**Type:** Momentum | **Chart:** 5-minute | **Pairs:** All liquid majors

**Entry (Long):**
- Price crosses ABOVE both 20-EMA and 100-SMA by 15 pips
- MACD histogram (12, 26, 9) turned positive within last 5 candles
- Buy at market

**Entry (Short):** Mirror opposite

**Exit:**
- Stop: Low of candle that broke the MAs
- TP1: Close half at 1x risk, move stop to breakeven
- TP2: Trail remainder by 20-EMA +/- 15 pips

**Why it works:** Three-layer confirmation (trend via 100-SMA, trigger via 20-EMA, momentum via MACD). The 15-pip buffer filters noise. The 5-candle MACD rule ensures fresh momentum, not stale.

---

### 2. High-Probability Turn Strategy (Ch. 9, pp. 155-164)

**Type:** Mean-Reversion | **Chart:** Daily | **Pairs:** EUR/USD, GBP/USD, USD/JPY

**Entry:**
- 7 consecutive days where close < open (for long) or close > open (for short)
- Enter at 5:00 PM NY time (next candle open)

**Exit:**
- Stop: 30 pips
- TP1: 60 pips (close half), move stop to breakeven
- TP2: 120 pips (close remainder)

**Statistical Basis (10 years of data):**
- EUR/USD: Only 5 out of 10 seven-day extensions lasted to day 8. Max was 10 days.
- GBP/USD: Only 7 out of 12 extended to day 8. Max was 12 days.
- USD/JPY: Only 7 out of 12 extended to day 8. Max was 9 days.

**Re-entry math:** If stopped out, re-enter next day. Net positive as long as extension doesn't reach 12th day (happened only once in 10 years across all 3 pairs).

---

### 3. Inside Day Breakout Play (Ch. 9, pp. 124-129)

**Type:** Breakout | **Chart:** Daily | **Pairs:** EUR/GBP, USD/CAD, EUR/CHF, EUR/CAD, AUD/CAD

**Entry:**
- 2+ consecutive inside days (daily range within prior day's range)
- Buy 10 pips above high of previous inside day
- Sell 10 pips below low of previous inside day

**Exit:**
- Stop-and-reverse: 2 lots placed 10 pips beyond opposite extreme
- TP: 2x risk or trail from there
- If stop-and-reverse triggers: new stop 10 pips beyond original inside day extreme

**Why it works:** Volatility compression always resolves into expansion. Multiple inside days amplify the compression. The stop-and-reverse mechanism handles false breakouts elegantly.

---

## Session-Based Strategies

### London Open Fake-Out (Waiting for the Real Deal)

- **Pair:** GBP/USD exclusively
- **Setup window:** 1:00 AM - 2:00 AM NY (Frankfurt/London power hour)
- **Concept:** U.K. dealers are notorious stop hunters. The initial move at London open is often a false move to trigger stops. The REAL directional move comes after.
- **Entry:** Wait for 25+ pip fake move, then enter when price reverses and breaks the opposite side of the range + 10 pips
- **Stop:** 20 pips | **Target:** 2x risk, then trail

### Channel Breakout (Asian-to-London)

- **Common pattern:** Tight channel forms during Asian session, breaks out at London or U.S. open
- **Even better:** When breakout coincides with major economic release

---

## Fundamental Strategies

### Leveraged Carry Trade
- Buy high-yield currency, sell low-yield currency
- Works in low-risk-aversion environments
- 2.5% yield differential = 25% on 10x leverage
- **Key risk:** Risk-aversion spikes (LTCM 1998, 9/11, financial crises) can reverse months of gains in days
- **Time horizon:** 6+ months minimum

### Bond Spread Leading Indicator
- 10-year government bond yield differentials LEAD currency prices
- When spread widens favoring a currency, that currency tends to appreciate
- Track in Excel: AUD/USD vs AU-US 10yr spread, GBP/USD vs UK-US 10yr spread

### Commodity-Currency Correlations
- AUD/USD and NZD/USD: 0.80 correlation with gold
- USD/CAD: -0.40 correlation with oil (weaker, more complex)
- Gold/oil moves can LEAD currency moves

---

## Additional Frameworks

### ADX Environment Classification (Ch. 8)
- **ADX < 20:** Range-bound market. Use oscillators (RSI, Stochastics, Bollinger Bands).
- **ADX > 25:** Trending market. Use trend-following (MAs, momentum, Fibonacci).
- **ADX > 25 but falling from 40+:** Trend fading. Be careful with aggressive positions.

### Seasonality Patterns (Ch. 7)
| Month | Pattern | Pairs | Win Rate |
|-------|---------|-------|----------|
| January | USD strengthens | EUR/USD, USD/CHF | 82% (11yr) |
| January | USD strengthens | USD/JPY | 73% (11yr) |
| May | AUD/NZD weaken | AUD/USD, NZD/USD | 82% / 73% |
| July | USD strengthens | USD/JPY, USD/CAD | 82% / 73% |
| August | Reversal of July | USD/JPY, USD/CAD | 82% / 73% |
| September | USD weakens | USD/CHF, GBP/USD | 82% |
| November | NZD strengthens | NZD/USD | 73% |

### Option Volatility Signal
- 1-month vol << 3-month vol: Expect breakout
- 1-month vol >> 3-month vol: Expect range reversion

### Risk Reversal Contrarian Signal
- Extreme positive risk reversal (1 std dev above mean): Overbought, expect decline
- Extreme negative risk reversal (1 std dev below mean): Oversold, expect rally

---

## Universal Risk Management Rules

1. **Risk per trade:** Max 2% of equity
2. **Risk-reward minimum:** 1:2
3. **Stop placement:** Two-day low method (10 pips below 2-day low) OR Parabolic SAR
4. **Breakeven rule:** Move stop to breakeven once profit = initial risk
5. **Scaling:** Close half at first target, trail remainder
6. **Trailing methods:** 2-bar low/high, Parabolic SAR, or 20-day SMA on 5-min chart

---

## Key Indicators Used Across Strategies

| Indicator | Parameters | Usage |
|-----------|-----------|-------|
| ADX | 14-period | Environment classification (trend vs range) |
| SMA | 20, 50, 100, 200 | Trend direction, perfect order, support/resistance |
| EMA | 20-period | Momentum trigger (20-100 strategy) |
| MACD | 12, 26, 9 | Momentum confirmation |
| Bollinger Bands | Default | Volatility compression, range identification |
| RSI | 14-period | Overbought/oversold in range environments |
| Stochastics | Default | Range-bound entries |
| Parabolic SAR | Default | Trailing stops |

---

## Links

- [[Master Report]]
- [[Strategy Comparison Overview]]
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]

---

*Analysis date: 2026-03-25 | Source: Strategy Pipeline automated extraction*
