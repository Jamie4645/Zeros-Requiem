> [!warning] SUPERSEDED (2026-07-02 blank-slate re-read)
> This note is a strategy-extraction catalog from the SBRS era and must NOT be treated as canon. The 2026-07 fresh re-read of the full book text found extraction-focus, missing load-bearing content, and in several notes fabricated material (invented quotes/parameters). Durable record: knowledge-base/92-Books-Blank-Slate-Review.md.

# Option Spread Strategies - Book Analysis

#trading #book-analysis #options #spreads #volatility #greeks #butterflies #condors #income

**Book:** Option Spread Strategies: Trading Up, Down, and Sideways Markets (2009)
**Author:** Anthony J. Saliba with Joseph C. Corona and Karen E. Johnson
**Focus:** Options spread trading strategies for directional, neutral, and volatility plays across 22 strategies
**Link to:** [[Master Report]] | [[Strategy Comparison Overview]]

---

## Overview

Saliba's book is the definitive practical guide to options spread construction, covering 22 strategies spanning directional (bullish/bearish), neutral (sideways), and volatility (breakout) plays. The framework begins with market forecast, then matches strategy to outlook, magnitude, time horizon, and implied volatility environment. Every strategy is presented with Greeks profiles, adjustment techniques, and risk management.

**Core Edge:** Match strategy to market outlook + IV environment. There is no free lunch — long gamma costs theta, short theta has adverse gamma. The author's framework for strategy selection based on forecast + IV + risk tolerance is the real value.

**Key Principles:**
- If you are wrong, get out. No hoping or praying. Have exit plan before entry.
- Use synthetically equivalent positions for better exit pricing.
- Support/resistance levels serve dual purpose: strike selection AND risk management.
- Rolling positions via vertical spreads or butterflies maintains exposure while reducing risk.

---

## Implied Volatility Framework

### High IV Favors (Sell Premium)

- Credit spreads (bull put, bear call)
- Short straddles / strangles
- Covered writes
- Ratio spreads
- Short calendar spreads

### Low IV Favors (Buy Premium)

- Debit spreads (bull call, bear put)
- Long straddles / strangles
- Backspreads
- Long calendar spreads
- Long butterflies / condors

### IV Skew Usage

Sell high-IV strikes, buy low-IV strikes when skew is steep. Compare front-month vs back-month IV for calendar spread direction.

---

## Strategy 1: Covered Write (Buy-Write)

| Parameter | Value |
|-----------|-------|
| **Type** | Income / Neutral |
| **Timeframe** | 45 days or less for income |
| **Markets** | Equities, ETFs |
| **Entry** | Buy 100 shares + sell 1 ATM or OTM call |
| **Exit** | Breakeven = stock price - premium; exit if broken |
| **Position Size** | Standard (100 shares per contract) |
| **Stop Loss** | Substantial downside minus premium received |
| **Win Rate** | High in sideways/mildly bullish markets |
| **Clarity** | 9/10 |

### Strike Selection

```
NEUTRAL outlook:   Sell ATM call (maximum time decay)
MILDLY BULLISH:    Sell OTM call at expected target price
MODERATELY BULL:   Sell further OTM (more upside participation)
AVOID WHEN:        Bearish or strongly bullish; rate of return should NOT drive selection
```

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Positive (stock delta 100 minus short call delta) |
| Gamma | Negative |
| Theta | Positive (benefits from time decay) |
| Vega | Negative (benefits from falling IV) |

### Adjustments

- **Stock rises through strike:** Roll up via long call spread or diagonal up-and-out
- **Stock weakens:** Roll down via short call spread for additional protection
- **Emergency exit:** Buy put of same strike/expiry to create conversion (neutral)

> NOT a fire-and-forget strategy. Late-night TV claims of easy money are misleading.

---

## Strategy 2: Bull Call Spread (Debit Call Spread)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional |
| **Timeframe** | Matches forecast time horizon |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy lower strike call + sell higher strike call (same expiry) |
| **Exit** | Max profit at/above short strike at expiration |
| **Position Size** | Risk = debit paid |
| **Stop Loss** | Limited to debit paid |
| **Win Rate** | Best for moderate upward moves |
| **Clarity** | 9/10 |

### Entry Logic

```
FORECAST: Moderately bullish; expecting move to short strike
IV: Good when IV is high (reduces cost vs outright long call)
LONG STRIKE: Near current price
SHORT STRIKE: At price target
EXPIRY: Match to time horizon of forecast
```

### Risk/Reward

```
Max Risk:    Debit paid for spread
Max Reward:  Strike differential minus debit
Breakeven:   Lower strike + debit
```

---

## Strategy 3: Bull Put Spread (Credit Put Spread)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Income |
| **Timeframe** | Shorter duration for faster theta |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell higher strike put + buy lower strike put (same expiry) |
| **Exit** | Both puts expire worthless; keep full credit |
| **Position Size** | Risk = strike differential minus credit |
| **Stop Loss** | Strike differential minus credit received |
| **Win Rate** | High if price stays above short put |
| **Clarity** | 9/10 |

Synthetically equivalent to bull call spread. Use box pricing to determine whether call or put spread offers better value. Good for income generation with defined risk.

---

## Strategy 4: Bear Call Spread (Credit Call Spread)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Income |
| **Timeframe** | Shorter duration for faster theta |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell lower strike call + buy higher strike call (same expiry) |
| **Exit** | Both calls expire worthless; keep full credit |
| **Position Size** | Risk = strike differential minus credit |
| **Stop Loss** | Strike differential minus credit received |
| **Win Rate** | High if price stays below short call |
| **Clarity** | 9/10 |

Synthetically equivalent to bear put spread. Good for selling premium above resistance with capped risk.

---

## Strategy 5: Bear Put Spread (Debit Put Spread)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional |
| **Timeframe** | Match to expected decline window |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy higher strike put + sell lower strike put (same expiry) |
| **Exit** | Max profit at/below short strike at expiration |
| **Position Size** | Risk = debit paid |
| **Stop Loss** | Limited to debit paid |
| **Win Rate** | Best for moderate downward moves |
| **Clarity** | 9/10 |

Good for countertrend trades and limited-risk bearish positions. Roll via selling overlapping butterfly to shift to lower strikes.

---

## Strategy 6: Collar (Bearish)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Hedge |
| **Timeframe** | Imprecise timing OK |
| **Markets** | Equities, indices |
| **Entry** | Buy OTM put (below) + sell OTM call (above) for near-zero cost |
| **Exit** | Roll long put down via vertical spreads to lock in profits |
| **Position Size** | Near zero cost to enter |
| **Stop Loss** | Stop-loss on short call if resistance broken |
| **Win Rate** | Good when timing is uncertain |
| **Clarity** | 8/10 |

### Greeks (Key Advantage)

| Greek | Profile |
|-------|---------|
| Delta | Negative (0 to -100) |
| Gamma | Near zero between strikes |
| Theta | **Near zero** between strikes (time doesn't hurt) |
| Vega | **Near zero** between strikes (IV doesn't hurt) |

Choose over outright puts when timing is uncertain — theta and vega neutrality gives you time to be right.

---

## Strategy 7: Reverse Collar (Bullish)

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Hedge |
| **Timeframe** | Imprecise timing OK |
| **Markets** | Equities, indices |
| **Entry** | Buy OTM call (above) + sell OTM put (below) for near-zero cost |
| **Exit** | Roll long call up via vertical spreads |
| **Position Size** | Near zero cost to enter |
| **Stop Loss** | Stop-loss on short put if support broken |
| **Win Rate** | Good when timing uncertain; exploits IV skew |
| **Clarity** | 8/10 |

Steep IV skew (OTM puts at higher IV than OTM calls) makes this especially attractive — sell expensive puts, buy cheap calls.

---

## Strategy 8: Long Straddle

| Parameter | Value |
|-----------|-------|
| **Type** | Volatility |
| **Timeframe** | Must be fairly precise; clock is the enemy |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy ATM call + buy ATM put (same strike, same expiry) |
| **Exit** | Time stop + price stop; exit on lesser |
| **Position Size** | Risk = total debit paid |
| **Stop Loss** | Total premium paid |
| **Win Rate** | Requires large magnitude move |
| **Clarity** | 9/10 |

### Entry Logic

```
FORECAST: Large magnitude breakout in EITHER direction
CATALYSTS: Earnings, government reports, corporate events, technical breakouts
IV: Best when IV is LOW (cheaper premiums)
TIMING: Must be precise — clock is the enemy
```

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Near zero at ATM; moves in favor with large move |
| Gamma | **Positive** (delta accelerates in your favor) |
| Theta | **NEGATIVE** (time decay is the major cost) |
| Vega | Positive (benefits from rising IV) |

> Seductive due to unlimited profit potential. Traders often overlook theta/vega costs. Death by a thousand cuts from daily time decay.

---

## Strategy 9: Long Strangle

| Parameter | Value |
|-----------|-------|
| **Type** | Volatility |
| **Timeframe** | Precise timing needed |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy OTM call (above) + buy OTM put (below) |
| **Exit** | Time stop + price stop; exit on lesser |
| **Position Size** | Risk = total debit paid |
| **Stop Loss** | Total premium paid |
| **Win Rate** | Requires very large move |
| **Clarity** | 9/10 |

Less aggressive than straddle. Wider breakeven points but cheaper cost and less theta bleed. Roll profitable leg via selling vertical spreads to capture gains.

---

## Strategy 10: Short Straddle

| Parameter | Value |
|-----------|-------|
| **Type** | Income / Neutral |
| **Timeframe** | Post-volatile consolidation periods |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell ATM call + sell ATM put (same strike, same expiry) |
| **Exit** | Collect theta daily; stop on both underlying price and straddle value |
| **Position Size** | Credit received |
| **Stop Loss** | **UNLIMITED RISK** — must use stop-losses |
| **Win Rate** | High in low-volatility sideways markets |
| **Clarity** | 9/10 |

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Near zero at strike; moves against trader |
| Gamma | **NEGATIVE** (adverse delta movement) |
| Theta | **POSITIVE** (time decay earns money) |
| Vega | Negative (benefits from falling IV) |

> **UNLIMITED RISK.** Theta income can vanish in one large move. Set stop on both underlying price and straddle price. Not suitable for most retail traders.

---

## Strategy 11: Short Strangle

| Parameter | Value |
|-----------|-------|
| **Type** | Income / Neutral |
| **Timeframe** | Sideways/low-volatility periods |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell OTM call (above) + sell OTM put (below) at support/resistance |
| **Exit** | Price and straddle-value stop losses required |
| **Position Size** | Credit received |
| **Stop Loss** | **UNLIMITED RISK** |
| **Win Rate** | Higher than short straddle (wider profit zone) |
| **Clarity** | 9/10 |

Wider profit zone but smaller max profit than short straddle. Still carries unlimited risk.

---

## Strategy 12: Long Call Butterfly

| Parameter | Value |
|-----------|-------|
| **Type** | Neutral |
| **Timeframe** | Shorter-dated bears fruit faster |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy 1 lower call + sell 2 middle calls + buy 1 upper call (same expiry) |
| **Exit** | Scale out 2-3 at a time; exit on support/resistance breach |
| **Position Size** | Risk = debit paid |
| **Stop Loss** | Limited to debit paid |
| **Win Rate** | High when stock stays near middle strike |
| **Clarity** | 9/10 |

### Entry Logic

```
FORECAST: Directionless; underlying hovering near middle strike
MIDDLE STRIKE: At mean-reversion price of trading range
WINGS: At support and resistance levels
IV: Best when IV is high (short middle benefits from decline)
IDENTIFICATION: Use technical analysis for support/resistance/mean-reversion
```

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Near zero at middle strike |
| Gamma | Negative at middle strike; positive at wings |
| Theta | **POSITIVE** at middle strike (earns time decay) |
| Vega | Negative at middle strike (benefits from falling IV) |

### Adjustments

- **Range wider than expected:** Add butterfly at adjacent strikes → creates condor
- **Range narrows:** Sell embedded butterfly to tighten position
- **Breakout occurs:** EXIT the trade

> Limited-risk version of short straddle. Call, put, and iron butterflies are synthetically equivalent.

---

## Strategy 13: Long Iron Butterfly

| Parameter | Value |
|-----------|-------|
| **Type** | Neutral |
| **Timeframe** | Same as call butterfly |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy OTM put + sell ATM put + sell ATM call + buy OTM call |
| **Exit** | Same as long butterfly |
| **Position Size** | Risk = wing width minus credit |
| **Stop Loss** | Wing width minus credit received |
| **Win Rate** | Same as call/put butterfly |
| **Clarity** | 8/10 |

Iron version uses mixed puts and calls. Credit trade. Same Greeks and risk profile as call/put butterfly.

---

## Strategy 14: Long Call Condor

| Parameter | Value |
|-----------|-------|
| **Type** | Neutral |
| **Timeframe** | Sideways market |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy K1 call + sell K2 call + sell K3 call + buy K4 call (K1 < K2 < K3 < K4) |
| **Exit** | Scale out; watch for breakouts; exit on support/resistance breach |
| **Position Size** | Risk = debit paid |
| **Stop Loss** | Limited to debit paid |
| **Win Rate** | Wider profit zone than butterfly |
| **Clarity** | 9/10 |

### Entry Logic

```
FORECAST: Directionless; wider trading range than butterfly can cover
INNER STRIKES: Spanning the mean-reversion zone
OUTER STRIKES: At support and resistance levels
IV: Best when high
VS BUTTERFLY: Use when range is too wide or mean-reversion is a zone not a point
```

### Risk/Reward

```
Max Risk:     Debit paid (more than butterfly)
Max Reward:   Inner strike differential minus debit (less than butterfly)
Breakevens:   K1 + debit; K4 - debit
```

### Adjustment

Range narrows → Sell embedded butterfly from condor to tighten into butterfly.

---

## Strategy 15: Long Iron Condor

| Parameter | Value |
|-----------|-------|
| **Type** | Neutral / Income |
| **Timeframe** | Sideways market |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy OTM put + sell closer OTM put + sell OTM call + buy further OTM call |
| **Exit** | Collect premium if price stays between inner strikes |
| **Position Size** | Risk = wing width minus credit |
| **Stop Loss** | Wing width minus credit received |
| **Win Rate** | High in range-bound markets |
| **Clarity** | 8/10 |

Most popular version for retail traders. Credit trade with defined risk. Synthetically equivalent to call/put condor.

---

## Strategy 16: Long Calendar Spread (Horizontal Time Spread)

| Parameter | Value |
|-----------|-------|
| **Type** | Neutral / Directional |
| **Timeframe** | Until short option expiry |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell near-term option + buy deferred-term option (same strike) |
| **Exit** | Max value at strike at short expiry; MUST close before short option expires |
| **Position Size** | Risk = debit paid |
| **Stop Loss** | Limited to debit paid |
| **Win Rate** | Good when price stays near strike |
| **Clarity** | 9/10 |

### Entry Logic

```
SIDEWAYS USE:
    Strike = ATM (current price) for neutral trade
    IV: Best when LOW; benefits from rising IV (long vega)

DIRECTIONAL USE:
    BULLISH: Strike above current price (target for upward move)
    BEARISH: Strike below current price (target for downward move)
    Timing: Short-dated option expires at expected arrival time

TERM STRUCTURE:
    FAVORABLE: Short-dated IV > long-dated IV (sell expensive, buy cheap)
    UNFAVORABLE: Short-dated IV < long-dated (avoid)
```

### Greeks (Unique Profile)

| Greek | Profile |
|-------|---------|
| Delta | Gravitates toward strike (positive below, negative above) |
| Gamma | Negative at strike |
| Theta | **POSITIVE** at strike (earns time decay differentially) |
| Vega | **POSITIVE** (benefits from rising IV) |

> **Unique:** Positive theta AND positive vega simultaneously. Great when IV is low and market is sideways.

---

## Strategy 17: Short Calendar Spread

| Parameter | Value |
|-----------|-------|
| **Type** | Volatility / Breakout |
| **Timeframe** | Until short expiry |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy near-term option + sell deferred-term option (same strike) |
| **Exit** | Exit if breakout fails to materialize; must close before expiry |
| **Position Size** | Credit received |
| **Stop Loss** | Unquantifiable at entry |
| **Win Rate** | Good for sharp breakouts with IV decline |
| **Clarity** | 8/10 |

Better than long straddle when IV is high and expected to fall post-event. Short vega benefits from IV decline after breakout.

---

## Strategy 18: Call Ratio Spread

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Volatility |
| **Timeframe** | Limited upside move expected |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy 1 ATM call + sell 2 OTM calls (common: 1:2, 2:3, 1:4 ratios) |
| **Exit** | Scale out as position profits; iron fist risk management |
| **Position Size** | Credit or small debit |
| **Stop Loss** | **UNLIMITED to the upside** above short strike |
| **Win Rate** | Best for slow, limited moves with declining IV |
| **Clarity** | 9/10 |

### Best Conditions

```
1. Contratrend oversold bounce
2. Rally decelerating into resistance/congestion
3. Post-meltdown recovery
4. Volatility skew: buy low-IV strike, sell high-IV strike
```

### Adjustment to Cap Risk

```
BUY additional call at higher strike → CONVERTS to butterfly (limited risk)
```

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Positive (grows with mild upward move) |
| Gamma | Negative near short strike |
| Theta | Positive (benefits from time decay) |
| Vega | Negative (benefits from falling IV) |

> Essentially a one-winged butterfly. NOT for traders who cannot handle overnight risk. Convert to butterfly to cap risk if nervous.

---

## Strategy 19: Put Ratio Spread

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Volatility |
| **Timeframe** | Limited downside move expected |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Buy 1 ATM put + sell 2 OTM puts (common: 1:2, 2:3 ratios) |
| **Exit** | Scale out; exit on acceleration |
| **Position Size** | Credit or small debit |
| **Stop Loss** | **Substantial risk to downside** below short strike |
| **Win Rate** | Best for slow, limited declines |
| **Clarity** | 9/10 |

### Best Conditions

```
1. Contratrend overbought correction
2. Decline decelerating into support/congestion
3. Post-meltup correction
```

Mirror image of call ratio spread. Convert to butterfly to manage risk.

---

## Strategy 20: Call Backspread

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Volatility |
| **Timeframe** | CRITICAL — timing must be precise |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell 1 ATM call + buy 2 OTM calls (1:2, 1:3, 1:4 ratios) |
| **Exit** | If breakout doesn't materialize quickly, time decay erodes position |
| **Position Size** | Small debit or credit |
| **Stop Loss** | Max risk between strikes at short expiry |
| **Win Rate** | Requires high-magnitude, high-velocity breakout |
| **Clarity** | 9/10 |

### Entry Logic

```
FORECAST: High-magnitude, high-velocity UPWARD breakout
CATALYSTS: Bullish news, earnings, takeovers, technical breakouts
IV: Enter when LOW; benefits from rising IV (long vega)
TIMING: CRITICAL — wrong timing causes losses even with correct direction
```

### Greeks

| Greek | Profile |
|-------|---------|
| Delta | Starts near zero; becomes increasingly positive on rally |
| Gamma | **POSITIVE** (delta accelerates favorably) |
| Theta | **NEGATIVE** (time decay hurts) |
| Vega | **POSITIVE** (benefits from rising IV) |

> **Danger zone:** Price stuck between strikes near expiry — can go negative delta even if direction was correct. Timing is everything.

---

## Strategy 21: Put Backspread

| Parameter | Value |
|-----------|-------|
| **Type** | Directional / Volatility |
| **Timeframe** | CRITICAL timing |
| **Markets** | Equities, indices, ETFs |
| **Entry** | Sell 1 ATM put + buy 2 OTM puts (1:2, 1:3, 1:4 ratios) |
| **Exit** | Exit if breakout fails to materialize |
| **Position Size** | Small debit or credit |
| **Stop Loss** | Max risk between strikes |
| **Win Rate** | Best for crash/panic scenarios |
| **Clarity** | 9/10 |

Mirror image of call backspread. VIX spikes benefit via positive vega. Best for crash/panic scenarios.

---

## Strategy 22: Box Spread (Arbitrage/Pricing Tool)

| Parameter | Value |
|-----------|-------|
| **Type** | Arbitrage / Pricing Tool |
| **Timeframe** | N/A |
| **Markets** | All options markets |
| **Entry** | Bull call spread + bear put spread (same strikes, same expiry) |
| **Exit** | At expiration, box = strike differential |
| **Position Size** | N/A |
| **Stop Loss** | Near zero risk (neutral structure) |
| **Win Rate** | N/A — pricing tool |
| **Clarity** | 8/10 |

### Box Pricing Formula

```
Box Value = (K2 - K1) / (1 + r)^t

BULL SPREAD: If call ask + put bid > box → sell put spread
             If call ask + put bid < box → buy call spread

BEAR SPREAD: If call bid + put ask > box → sell call spread
             If call bid + put ask < box → buy put spread
```

Not a trading strategy per se — a critical tool for choosing between synthetically equivalent spreads.

---

## Strategy Selection Matrix

### By Market Outlook

| Outlook | Strategies |
|---------|-----------|
| **Strongly Bullish** | Call Backspread, Reverse Collar, Bull Call Spread |
| **Moderately Bullish** | Bull Call Spread, Bull Put Spread, Covered Write, Call Ratio Spread |
| **Neutral / Sideways** | Long Butterfly, Long Condor, Iron Condor, Short Straddle, Short Strangle, Long Calendar, Covered Write |
| **Moderately Bearish** | Bear Put Spread, Bear Call Spread, Put Ratio Spread |
| **Strongly Bearish** | Put Backspread, Collar, Bear Put Spread |
| **Breakout (Unknown Direction)** | Long Straddle, Long Strangle, Short Calendar Spread |

### By IV Environment

| IV Level | Strategies |
|----------|-----------|
| **High IV** | Credit spreads, Short straddle/strangle, Covered writes, Ratio spreads, Short calendar |
| **Low IV** | Debit spreads, Long straddle/strangle, Backspreads, Long calendar, Long butterfly/condor |
| **IV Declining** | Ratio spreads, Short straddle/strangle, Long butterfly/condor |
| **IV Rising** | Backspreads, Long straddle/strangle, Long calendar |

### By Risk Tolerance

| Risk Level | Strategies |
|------------|-----------|
| **Limited Risk Only** | Vertical spreads, Long butterfly/condor, Long straddle/strangle, Long calendar, Backspreads |
| **Moderate Risk** | Covered writes, Collars (with stops) |
| **Unlimited Risk Capable** | Short straddle/strangle, Ratio spreads |

---

## Common Adjustment Techniques

| Technique | Description |
|-----------|-------------|
| **Rolling Verticals** | Sell vertical spread in profitable direction to lock in gains |
| **Rolling to Butterfly** | Sell overlapping butterfly to shift strikes up or down |
| **Capping Ratio Spread** | Buy additional wing option to convert to limited-risk butterfly |
| **Calendar Rolling** | Buy calendar to roll long option; sell calendar to roll short option to next month |
| **Synthetic Exit** | Use synthetically equivalent position for better pricing (especially ITM with wide spreads) |

---

## Greeks Quick Reference

| Strategy | Delta | Gamma | Theta | Vega |
|----------|-------|-------|-------|------|
| Covered Write | + | - | + | - |
| Bull Call Spread | + | ± | ± | ± |
| Bull Put Spread | + | - | + | - |
| Bear Call Spread | - | - | + | - |
| Bear Put Spread | - | ± | ± | ± |
| Collar (Bearish) | - | ~0 | **~0** | **~0** |
| Reverse Collar | + | ~0 | **~0** | **~0** |
| Long Straddle | ~0 | + | **-** | + |
| Long Strangle | ~0 | + | - | + |
| Short Straddle | ~0 | **-** | + | - |
| Short Strangle | ~0 | - | + | - |
| Long Butterfly | ~0 | - | + | - |
| Long Condor | ~0 | - | + | - |
| Long Calendar | gravitates | - | + | **+** |
| Short Calendar | away | + | - | - |
| Call Ratio Spread | + | - | + | - |
| Put Ratio Spread | - | - | + | - |
| Call Backspread | ~0→+ | **+** | - | + |
| Put Backspread | ~0→- | + | - | + |

---

## Author Warnings

1. **There is no free lunch** — every strategy has a corresponding risk
2. **Long gamma always costs theta; short theta always has adverse gamma**
3. **Rate of return should NEVER be the deciding factor for covered writes**
4. **Short straddles/strangles are addictive but have unlimited risk**
5. **Long straddles/strangles look great on paper but time decay death is real**
6. **Ratio spreads punish the greedy** — have an iron fist risk management plan
7. **Backspreads can go negative delta between strikes if timing is wrong**
8. **Stop-loss orders do not protect when the market is closed** (gap risk)
9. **If your forecast is wrong, GET OUT. No hoping, no praying.**
10. **Covered writes are NOT fire-and-forget** despite TV advertising

---

## Codification Priority

| Strategy | Priority | Difficulty | Expected Edge |
|----------|----------|------------|---------------|
| **Bull/Bear Verticals** | HIGH | LOW | Defined risk, simple construction |
| **Iron Condor** | HIGH | LOW | Most popular retail strategy, defined risk |
| **Long Butterfly** | MEDIUM | MEDIUM | Limited risk version of short straddle |
| **Long Calendar** | MEDIUM | MEDIUM | Unique theta+/vega+ profile |
| **Collar/Reverse Collar** | MEDIUM | LOW | Near-zero theta/vega for imprecise timing |
| **Box Pricing Tool** | CRITICAL | LOW | Must-have for execution optimization |
| **Strategy Selection Matrix** | CRITICAL | LOW | Framework for matching strategy to conditions |
| **Long Straddle/Strangle** | LOW | LOW | Simple but theta death is real |
| **Ratio Spreads** | LOW | HIGH | Unlimited risk requires active management |
| **Backspreads** | LOW | HIGH | Timing-critical, complex risk profile |

---

## Source

- **Book:** Option Spread Strategies: Trading Up, Down, and Sideways Markets (2009) by Anthony J. Saliba
- **Key Chapters:** Ch. 1 (Covered Writes), Ch. 2 (Verticals), Ch. 3 (Collars), Ch. 4 (Straddles/Strangles), Ch. 5 (Butterflies/Condors), Ch. 6 (Calendars), Ch. 7 (Ratio Spreads), Ch. 8 (Backspreads)
- **JSON Analysis:** `strategy_pipeline/output/book_analyses/OPTION_SPREAD_STRATEGIES_analysis.json`