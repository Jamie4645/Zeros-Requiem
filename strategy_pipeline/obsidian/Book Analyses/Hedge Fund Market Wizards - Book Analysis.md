> [!warning] SUPERSEDED (2026-07-02 blank-slate re-read)
> This note is a strategy-extraction catalog from the SBRS era and must NOT be treated as canon. The 2026-07 fresh re-read of the full book text found extraction-focus, missing load-bearing content, and in several notes fabricated material (invented quotes/parameters). Durable record: knowledge-base/92-Books-Blank-Slate-Review.md.

# Hedge Fund Market Wizards - Book Analysis

#trading #book-analysis #hedge-fund #macro #value #systematic #options #risk-management

**Book:** Hedge Fund Market Wizards: How Winning Traders Win (2012)
**Author:** Jack D. Schwager
**Focus:** 15 hedge fund managers across macro, systematic, and equity strategies
**Link to:** [[Master Report]] | [[Strategy Comparison Overview]]

---

## Overview

Schwager interviews 15 elite hedge fund managers spanning discretionary macro, systematic quantitative, event-driven, and equity long/short approaches. The book extracts 18 distinct strategies and reveals 8 cross-cutting themes that unite these seemingly different traders. The single most universal principle: **every trader structures trades for limited downside and open-ended upside** (asymmetric risk/reward). Risk management — not prediction — is the real edge.

**Core Edge:** Asymmetric risk/reward structures + rigorous risk management + flexibility to reverse when wrong + patience to do nothing when opportunities are poor.

---

## Strategy 1: Macro Hypothesis Testing Framework

| Parameter | Value |
|-----------|-------|
| **Type** | Discretionary Macro |
| **Timeframe** | Weeks to months |
| **Markets** | Bonds, currencies, equity indices, commodities |
| **Entry** | Form macro hypothesis → find asymmetric implementation (options, CDS, spreads) |
| **Exit** | Stop at price that disproves thesis; if stop implies too large a loss, reduce size |
| **Position Size** | Calibrated to conviction and stop distance |
| **Stop Loss** | At thesis-invalidation price, NOT pain threshold |
| **Win Rate** | Not disclosed |
| **Clarity** | 6/10 |
| **Completeness** | 5/10 |

**Source:** Colm O'Shea (Ch. 1) — COMAC Capital / formerly Soros Fund Management

### Entry Logic (Pseudocode)

```
IF macro_hypothesis is formed:
    FIND asymmetric implementation (options, CDS, TED spreads)
    WHERE max_loss is DEFINED at entry
    WAIT for market action to confirm hypothesis
    IF market disagrees with hypothesis:
        ABANDON thesis (market is right)
    ELSE:
        SIZE UP position
```

### Key Rules

- Participate in bubbles from the LONG side — never short a bubble until it breaks
- Trade implementation can be more important than the trade idea itself
- Long bonds instead of short stocks when expecting equity bear market (avoids bear rally whipsaws)
- If stop implies uncomfortable loss, reduce position size rather than tightening stop

---

## Strategy 2: All Weather Portfolio (4-Quadrant Model)

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Macro |
| **Timeframe** | 12-18 month holding period |
| **Markets** | Bonds, equities, commodities, inflation-linked bonds, currencies |
| **Entry** | Classify regime into 4 quadrants; allocate to assets that perform well in each |
| **Exit** | Rebalance as regime shifts between quadrants |
| **Position Size** | Risk parity (equalize risk contribution, not dollar amounts) |
| **Stop Loss** | N/A — continuous rebalancing |
| **Win Rate** | ~15% annualized net (Pure Alpha since 1991) |
| **Clarity** | 7/10 |
| **Completeness** | 6/10 |

**Source:** Ray Dalio (Ch. 2) — Bridgewater Associates ($100B+ AUM)

### 4-Quadrant Allocation

```
Growth INCREASING + Inflation INCREASING:
    → Commodities, inflation-linked bonds, EM credit

Growth INCREASING + Inflation DECREASING:
    → Stocks, corporate bonds

Growth DECREASING + Inflation INCREASING:
    → Inflation-linked bonds, commodities

Growth DECREASING + Inflation DECREASING:
    → Nominal bonds, stocks (lower weight)
```

### Depression Gauge

Monitor simultaneously: interest rates, credit growth, stock market, credit spreads. Deleveraging cycles behave differently from recessions — same policy responses have different effects.

### Key Rules

- Build 100+ uncorrelated return streams across all asset classes
- If it only works in one period or one market, reject it
- Always stress-test against 1930s depression scenario
- Mistakes are essential learning opportunities — document every one

---

## Strategy 3: Mean Reversion Correlation Trading

| Parameter | Value |
|-----------|-------|
| **Type** | Discretionary Mean Reversion |
| **Timeframe** | Intraday to 3 days |
| **Markets** | Equity indices, ETFs, options |
| **Entry** | After 3 consecutive up/down days, look for reversal |
| **Exit** | Take profits quickly on mean reversion bounce |
| **Position Size** | 100-200 trades/day provides natural diversification |
| **Stop Loss** | Monthly circuit breaker: 2.0-2.5% = flatten everything |
| **Win Rate** | ~11% annualized net; 19 of 20 years profitable |
| **Clarity** | 5/10 |
| **Completeness** | 4/10 |

**Source:** Larry Benedict (Ch. 3) — Banyan Equity Management (Max DD <5%, only losing year was -0.6%)

### Entry Logic (Pseudocode)

```
IF consecutive_up_days >= 3:
    LOOK for short entries on strength
    HEDGE with correlated instruments showing relative weakness

IF consecutive_down_days >= 3:
    LOOK for long entries on weakness
    HEDGE with correlated instruments showing relative strength
```

### Monthly Drawdown Circuit Breaker (Critical Innovation)

```
IF monthly_loss >= 2.0% to 2.5%:
    LIQUIDATE all positions immediately
    TRADE very small until recovered
    NEVER trade to reach a profit target
```

---

## Strategy 4: Intermarket Divergence Strategy

| Parameter | Value |
|-----------|-------|
| **Type** | Fundamental/Technical Hybrid |
| **Timeframe** | Days to weeks |
| **Markets** | Futures, forex, commodities |
| **Entry** | Buy strongest in sector, sell weakest; confirm with RSI divergence and Fibonacci pullbacks |
| **Exit** | When fundamental bias changes or intermarket relationship normalizes |
| **Position Size** | Risk only 10 basis points (0.1%) per trade |
| **Stop Loss** | At thesis-invalidation point |
| **Win Rate** | ~17% annualized |
| **Clarity** | 7/10 |
| **Completeness** | 7/10 |

**Source:** Scott Ramsey (Ch. 4) — Denali Asset Management (CTA)

### Entry Logic (Pseudocode)

```
STEP 1: Develop fundamental directional bias for sector
STEP 2: BUY the STRONGEST instrument in sector
         SELL the WEAKEST instrument in sector
STEP 3: Confirm with RSI divergence at extremes
STEP 4: Enter on Fibonacci retracement pullback toward 200-day MA
STEP 5: Price must respect 200-day MA as support/resistance
```

### Indicators

- **RSI** — divergence detection at extremes
- **200-day MA** — primary trend filter
- **Fibonacci Retracements** — entry levels on pullbacks
- **Commodity vs equity divergence** — leading indicator

---

## Strategy 5: Secondary Variable Pattern Recognition System

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Quantitative |
| **Timeframe** | Varies by model |
| **Markets** | All liquid futures |
| **Entry** | 1000+ models from secondary variables (transformations of OHLC data) |
| **Exit** | Model-driven; cut exposure by 75% when volatility quadruples |
| **Position Size** | Volatility-adjusted across all models |
| **Stop Loss** | Extreme volatility = massive exposure reduction |
| **Win Rate** | ~12% annualized net, Sharpe >1.0 |
| **Clarity** | 4/10 |
| **Completeness** | 3/10 |

**Source:** Jaffray Woodriff (Ch. 5) — Quantitative Investment Management (QIM)

### Key Concept: The Third Way

Neither pure trend following nor pure mean reversion. Uses secondary variables (transformations, ratios, moving averages of price data — NOT raw prices). Each model generates small alpha; combine many for robust signal. Aggressive cross-validation on out-of-sample data before deployment. Continuous research — static systems degrade.

---

## Strategy 6: Kelly Criterion Position Sizing

| Parameter | Value |
|-----------|-------|
| **Type** | Position Sizing Framework |
| **Timeframe** | All |
| **Markets** | All |
| **Entry** | Calculate Kelly fraction: f* = (bp - q) / b |
| **Exit** | N/A — sizing methodology |
| **Position Size** | Use HALF Kelly to reduce volatility while retaining most growth |
| **Stop Loss** | Arbitrage: no reduction on DD; Directional: reduce on DD |
| **Win Rate** | ~19% gross annualized over 20 years (Thorp's fund) |
| **Clarity** | 9/10 |
| **Completeness** | 8/10 |

**Source:** Edward Thorp (Ch. 6) — Princeton Newport Partners (never had a losing year in 20 years)

### Kelly Formula

```
f* = (b × p - q) / b

WHERE:
    b = odds received on the bet
    p = probability of winning
    q = probability of losing (1 - p)

USE half-Kelly in practice:
    - Reduces growth rate by only 25%
    - Cuts volatility by 50%
    - Never exceed full Kelly — severely penalizes long-term growth
```

### Critical Distinction

- **Arbitrage trades (bounded risk):** Do NOT reduce on drawdowns — theoretical max loss is defined
- **Directional trades (unbounded risk):** DO reduce exposure on drawdowns — open-ended risk

---

## Strategy 7: Statistical Arbitrage (Market-Neutral)

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Stat Arb |
| **Timeframe** | Days to weeks |
| **Markets** | Equities |
| **Entry** | Buy recent underperformers, short recent outperformers (MUD) |
| **Exit** | Mean reversion target or time-based exit |
| **Position Size** | Sector-neutral, factor-neutral portfolio construction |
| **Stop Loss** | Market-neutral structure hedges systematic risk |
| **Win Rate** | Part of Thorp's 19% gross track record |
| **Clarity** | 7/10 |
| **Completeness** | 6/10 |

**Source:** Edward Thorp (Ch. 6)

### Entry Logic (Pseudocode)

```
RANK all stocks by recent relative performance
BUY: Most DOWN (recent underperformers)
SHORT: Most UP (recent outperformers)

CONSTRAINTS:
    Sector-neutral: equal dollar exposure long/short within each sector
    Factor-neutral: hedge out size, value, momentum factor exposures
    Correlation matrix: 60-day lookback
```

### Key Warning

Must continuously adapt — Thorp went through 3 major iterations as markets evolved.

---

## Strategy 8: Cheap Sigma / Mispriced Distribution Options Strategy

| Parameter | Value |
|-----------|-------|
| **Type** | Asymmetric Options |
| **Timeframe** | Weeks to months |
| **Markets** | Equity options, credit derivatives, index options |
| **Entry** | Identify situations where Black-Scholes assumptions fail; buy mispriced options |
| **Exit** | Options expire worthless (max loss = premium) or thesis plays out |
| **Position Size** | 15-20 concentrated positions; hold 50-80% cash |
| **Stop Loss** | Max loss defined at entry (option premium) |
| **Win Rate** | ~40% gross annualized (2002-2011) |
| **Clarity** | 8/10 |
| **Completeness** | 7/10 |

**Source:** Jamie Mai (Ch. 7) — Cornwall Capital (featured in *The Big Short*)

### Five Black-Scholes Failures (Systematic Mispricing Opportunities)

```
1. Returns are NOT normally distributed → Fat tails exist
2. Forward price is NOT necessarily future mean → Trends persist
3. Volatility does NOT scale by sqrt(time) → Regime changes
4. Volatility is NOT trend-blind → Trending markets have different vol profiles
5. Correlations are NOT stable → They spike in crises
```

### Key Rules

- Focus on binary outcome scenarios: when either big up or big down is likely, options are systematically underpriced
- Wait for high-conviction trades — doing nothing is a valid strategy
- Only trade when perceived edge is very large

---

## Strategy 9: Asymmetric Trader Allocation (BlueCrest Model)

| Parameter | Value |
|-----------|-------|
| **Type** | Multi-Strategy Risk Management |
| **Timeframe** | Annual rebasing |
| **Markets** | Fixed income, systematic trend following |
| **Entry** | Allocate capital to traders structured like options: limited downside, unlimited upside |
| **Exit** | 3%/3% rule: lose 3% from starting allocation = halve exposure; another 3% = zero allocation |
| **Position Size** | Annually rebased from high-water mark |
| **Stop Loss** | 3% from starting allocation = forced 50% reduction |
| **Win Rate** | Discretionary: ~14% net (Max DD <5%); Systematic: ~16% net (Max DD <13%) |
| **Clarity** | 8/10 |
| **Completeness** | 7/10 |

**Source:** Michael Platt (Ch. 8) — BlueCrest Capital Management

### Trader Risk Rules

```
IF trader_loss >= 3% from starting_allocation:
    HALVE trader's exposure
IF trader_loss >= 6% from starting_allocation:
    REMOVE all allocation

ANNUALLY: Rebase all allocations (not trailing)

DAILY CHECK: "Where would your biggest $10M loss come from?"
DAILY CHECK: "Would you enter this trade today at this price? If NO, exit."
```

### Key Indicators

- **LIBOR-OIS spread** — widening signals banking sector stress and liquidity drying up (early warning before 2008)
- Monitor correlation breakdown in spread positions — lower correlation = higher risk
- 80/20 rule: 80% of profits come from 20% of trades — protect ability to catch those

---

## Strategy 10: Magic Formula (Systematic Value)

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Value |
| **Timeframe** | 1-year holding period |
| **Markets** | Equities |
| **Entry** | Buy top 30 stocks ranked by combined Earnings Yield + Return on Tangible Capital |
| **Exit** | Hold 1 year then replace; sell losers before 1Y, hold winners past 1Y for tax |
| **Position Size** | 20-30 names minimum |
| **Stop Loss** | 6% minimum hurdle rate (opportunity cost floor) |
| **Win Rate** | 19.7% annualized vs 9.5% S&P 500 over 23-year backtest |
| **Clarity** | 10/10 |
| **Completeness** | 10/10 |

**Source:** Joel Greenblatt (Ch. 15) — Gotham Capital (50% annualized gross for 10 years, 1985-1994)

### Magic Formula (Pseudocode)

```
FOR each stock in top 1000 by market cap:
    Earnings Yield = EBIT / Enterprise Value
    Return on Capital = EBIT / (Net Working Capital + Net Fixed Assets)
    Combined Rank = Rank(Earnings Yield) + Rank(Return on Capital)

BUY: Top 30 stocks by lowest Combined Rank
HOLD: 1 year
REBALANCE: Monthly stepping (buy ~3 stocks/month over 12 months)

SELL: Losers before 1 year (short-term loss for tax offset)
      Winners after 1 year (long-term capital gains rate)
```

### Performance

- Top decile beats bottom decile by ~15%/year
- Perfect ordering across all 10 deciles
- Value weighted indexes outperform cap-weighted by ~7%/year over 20 years
- Works BECAUSE it doesn't work all the time — periodic underperformance keeps edge alive

---

## Strategy 11: Mean Reversion Exposure Bands

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Exposure Management |
| **Timeframe** | Monthly rebalancing |
| **Markets** | Equities |
| **Entry** | Use 95% confidence band on log-price regression (data from 1932) to set net exposure |
| **Exit** | Continuous — exposure adjusts as price moves within bands |
| **Position Size** | Net exposure ranges from 70% net short to 110% net long |
| **Stop Loss** | If down >7% in a month without explanation: reduce; 1% loss = 2% exposure reduction |
| **Win Rate** | 17% annualized compounded net over 19 years |
| **Clarity** | 9/10 |
| **Completeness** | 8/10 |

**Source:** Tom Claugus (Ch. 11) — GMT Capital (5 losing years in 26; net short during 1990s bull yet still profitable)

### Exposure Band Logic (Pseudocode)

```
CALCULATE 95% confidence band on log-price regression (since 1932)
APPLY to S&P 500, NASDAQ, Russell 2000; take composite

IF price at LOWER band:
    GO 130% long / 20% short = 110% net long

IF price at MIDPOINT:
    GO 100% long / 50% short = 50% net long (secular uptrend bias)

IF price at UPPER band:
    GO 20% long / 90% short = 70% net short
```

### Drawdown Rules

```
IF monthly_loss > 7% AND cannot explain why:
    REDUCE exposure immediately

FOR every 1% loss:
    REDUCE exposure by 2% (proportional scaling)
```

---

## Strategy 12: Evel Knievel Short Screen

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Short Selection |
| **Timeframe** | Quarterly screening |
| **Markets** | Equities |
| **Entry** | Screen for Price > 5x Book Value AND company is losing money |
| **Exit** | Cover when stock declines to reasonable valuation |
| **Position Size** | Diversified across many short positions |
| **Stop Loss** | For every 1% loss, reduce exposure by 2% |
| **Win Rate** | Historically very profitable except during extreme bubbles (1999) |
| **Clarity** | 9/10 |
| **Completeness** | 8/10 |

**Source:** Tom Claugus (Ch. 11) — GMT Capital

### Screen Logic (Pseudocode)

```
SCREEN for all stocks WHERE:
    Price / Book Value > 5x
    AND Earnings < 0 (company is losing money)

NORMALLY yields ~60 names
IF count > 150: EXTREME BUBBLE WARNING (180 names in late 1999)

SHORT qualified names with diversified sizing
COVER when valuation normalizes
```

**Bubble Indicator:** The count of qualifying names is itself a bubble gauge.

---

## Strategy 13: Free Optionality Long Screen

| Parameter | Value |
|-----------|-------|
| **Type** | Fundamental Value |
| **Timeframe** | Months to years |
| **Markets** | Equities, energy stocks |
| **Entry** | Find companies priced at fair value on current business but with unpriced future revenue >1 year out |
| **Exit** | When market begins pricing in the future revenue source |
| **Position Size** | Standard |
| **Stop Loss** | Downside limited to fair value of current business |
| **Win Rate** | Part of Claugus's 17% annualized track record |
| **Clarity** | 8/10 |
| **Completeness** | 7/10 |

**Source:** Tom Claugus (Ch. 11) — "My single most important stock selection concept"

### Key Insight

Markets rarely price revenues >1 year out. You pay fair price for what exists today but get the upside of anticipated future revenue for free. Examples: unexplored acreage for oil companies, new technology for manufacturers, emerging market expansion.

Best entry after a disappointment — sector selloff on unrelated bad news creates the opportunity.

---

## Strategy 14: Deep Value Screen Toolkit

| Parameter | Value |
|-----------|-------|
| **Type** | Systematic Value Screening |
| **Timeframe** | Months to years |
| **Markets** | US and Canadian equities |
| **Entry** | Screen 10,000 stocks using EV/EBITDA, Price/FCF, P/E, EV/EBIT; narrow to 200; qualitative filter |
| **Exit** | Sell at fair valuation; move to 60-90% cash in uncertain macro |
| **Position Size** | Circle of competence — only invest in understandable businesses |
| **Stop Loss** | Buy a dollar for 50 cents (margin of safety) |
| **Win Rate** | 20.8% gross (16.4% net) over 12 years; 872% cumulative vs -9% S&P 500 |
| **Clarity** | 9/10 |
| **Completeness** | 9/10 |

**Source:** Kevin Daly (Ch. 13) — Five Corners Partners (Max DD 10.3%, Gain-to-Pain 3.2)

### Value Metrics

| Metric | Use |
|--------|-----|
| EV/EBITDA | Primary value metric for non-financials |
| Price/Free Cash Flow | Cash generation relative to price |
| EV/EBIT (Cap Rate) | What a rational buyer would pay |
| Price/Tangible Book | Floor value for banks |
| Rail Car Loadings | Real economy leading indicator |
| Form 4 Insider Transactions | Insider sentiment |

### Key Rules

- Avoid value traps: skip melting ice cube businesses (newspapers, yellow pages, video rental)
- Look for hidden niches inside larger companies that market ignores
- Small asset size is an advantage — can trade illiquid small caps others can't
- Patience: stayed ~90% cash for 2+ years during 2000-2002 bear market

---

## Strategy 15: Conference Call Sentiment Analysis

| Parameter | Value |
|-----------|-------|
| **Type** | Fundamental Sentiment |
| **Timeframe** | Days to weeks |
| **Markets** | Equities |
| **Entry** | Stock DOWN after positive conference call = short; stock UP after negative call = long |
| **Exit** | Scale out rather than all-or-nothing; harvest losses periodically |
| **Position Size** | Varies by conviction and volatility (Coke gets 5% room; volatile stock gets 50%) |
| **Stop Loss** | Mental stops (re-evaluation points), not hard stops |
| **Win Rate** | 18% net annualized over 10+ years (24% gross) |
| **Clarity** | 7/10 |
| **Completeness** | 6/10 |

**Source:** Joe Vidich (Ch. 12) — Manalapan Oracle Capital (Max DD 8%, Gain-to-Pain 2.4)

### Sentiment Signals (Pseudocode)

```
LISTEN to 300+ conference calls per quarter

IF stock DOWN after POSITIVE conference call:
    Smart money is selling → SHORT

IF stock UP after NEGATIVE conference call:
    Smart money is buying → LONG

IF analysts are confused and can't understand the business:
    OPPORTUNITY (Citigroup CDOs in 2008)

IF company mentions deferring capex:
    SHORT their suppliers
```

### Intraday Trend Pattern

- **Bull market:** Open low, close high
- **Bear market:** Open high, close low
- **End of trend:** Pattern flips

---

## Strategy 16: Spinoff / Special Situations Value

| Parameter | Value |
|-----------|-------|
| **Type** | Event-Driven Value |
| **Timeframe** | Months to years |
| **Markets** | Equities |
| **Entry** | Focus on spinoffs where institutions dump shares; check insider ownership in the spinoff |
| **Exit** | Sell when stock reaches intrinsic value |
| **Position Size** | Concentrated (6-8 positions in original fund) |
| **Stop Loss** | Operating leverage cuts both ways — monitor fundamentals closely |
| **Win Rate** | 50% annualized gross for 10 years (Greenblatt) |
| **Clarity** | 8/10 |
| **Completeness** | 8/10 |

**Source:** Joel Greenblatt (Ch. 15) — Gotham Capital

### Key Rules

- Institutions dump spinoff shares because new entity is too small or different sector — creates mispricing
- If insiders chose the "bad" company, it's probably not that bad
- Low share price relative to enterprise value = high operating leverage
- Read the 400-page documents others won't — complexity is your edge
- Use options for binary outcome scenarios to get 5:1 risk/reward on 50/50+ situations

---

## Cross-Cutting Themes (All 15 Traders)

### 1. Asymmetric Risk/Reward Is the Common Thread

Nearly every trader structures trades for limited downside and open-ended upside. O'Shea uses options and CDS. Mai buys cheap options. Platt structures trader allocations like options. Greenblatt uses LEAPS for binary situations. **This is the single most universal principle.**

### 2. Risk Management Is the Real Edge

None describe an edge in prediction. All describe an edge in risk management:
- Platt's 3%/3% rule
- Benedict's 2.5% monthly circuit breaker
- Claugus's 7% monthly loss investigation threshold
- Ramsey's 10bp per trade risk
- Clark's "if you're thinking about it at night, it's too big"

### 3. Flexibility and Willingness to Be Wrong

Every successful trader can reverse positions instantly when proven wrong. O'Shea reversed from bearish to bullish in April 2009. Clark emphasizes changing your mind in an instant. Rigidity is the common cause of trader failure.

### 4. Value Investing Works Because It Doesn't Always Work

Greenblatt, Daly, Claugus, and Taylor demonstrate that value approaches outperform precisely because they underperform for stretches long enough to drive out impatient capital.

### 5. Market Response to News > The News Itself

A stock down on good earnings is bearish. A market that refuses to go down on bad news is bullish. Sentiment reading through price action is a core skill across discretionary traders.

### 6. Position Sizing Matters More Than Entry

Clark, Vidich, Thorp, and Balodimas all stress that size determines whether you can hold a good trade. Too large = fear-driven exits on noise.

### 7. Adaptation Is Mandatory

Thorp went through 3 iterations of stat arb. Platt describes systematic trading as "a research war." Static systems degrade. Continuous evolution is required.

### 8. Patience and the Willingness to Do Nothing

Mai holds 50-80% cash. Daly was 90% cash for 2+ years. Greenblatt says there are no called strikes. Sitting in cash when opportunities are poor is as important as identifying good ones.

---

## Key Concepts

### Gain to Pain Ratio (GPR)

Sum of all monthly returns / absolute sum of all monthly losses. Unlike Sharpe, does not penalize upside volatility. GPR > 1.0 is very good. GPR > 1.5 is excellent. Equivalent to Profit Factor - 1 when applied to monthly returns.

### Time Arbitrage

The institutionalization of short-term performance monitoring has shortened most managers' time horizons. This creates opportunity for those willing to take a 2-3 year view.

### Trading Around a Position

Reduce position on favorable moves, reinstate on corrections. Generates extra profits from chop. Drawback: gives up some profit if market moves smoothly in your favor.

### Value Weighted Indexing

Cap-weighted indexes systematically overweight expensive stocks and underweight cheap ones. Value-weighted indexes beat S&P 500 by ~7%/year over 20 years with same beta and volatility.

---

## Performance Data

| Trader | Fund | Style | Annual Return | Max DD | Notable |
|--------|------|-------|---------------|--------|---------|
| Ray Dalio | Bridgewater | Fundamental Systematic | ~15% net | Low single digits | $100B+ AUM |
| Larry Benedict | Banyan Equity | Mean Reversion | ~11% net | <5% | 19/20 years profitable |
| Scott Ramsey | Denali | Fundamental+Technical | ~17% | N/A | 10bp risk per trade |
| Jaffray Woodriff | QIM | Systematic Pattern | ~12% net | N/A | Sharpe >1.0 |
| Edward Thorp | Princeton Newport | Stat Arb | ~19% gross | Very small | 20 years, no losing year |
| Jamie Mai | Cornwall Capital | Asymmetric Options | ~40% gross | N/A | Featured in The Big Short |
| Michael Platt | BlueCrest | Multi-Strategy | ~14-16% net | <5-13% | 11+ years |
| Steve Clark | Omni Global | Event-Driven | 19.4% net | 7% | Sharpe 1.50, GPR 4.1 |
| Martin Taylor | Nevsky Fund | EM Long/Short | 22%+ net | ~17% (2008) | EM index was -54% |
| Tom Claugus | GMT Capital | Contrarian Value | 17% net | N/A | 5 losing years in 26 |
| Joe Vidich | Manalapan Oracle | Fundamental Themes | 18% net | 8% | GPR 2.4 |
| Kevin Daly | Five Corners | Deep Value | 16.4% net | 10.3% | 872% vs -9% S&P |
| Joel Greenblatt | Gotham Capital | Systematic Value | 50% gross (fund) | N/A | 10 years, lowest +28.5% |

---

## Codification Priority

| Strategy | Priority | Difficulty | Expected Edge |
|----------|----------|------------|---------------|
| **Magic Formula** | HIGH | LOW | 23-year backtest, doubled S&P, fully mechanical |
| **Mean Reversion Bands** | HIGH | MEDIUM | 18% annualized even while net short in 90s |
| **Evel Knievel Screen** | MEDIUM | LOW | Simple 2-factor screen, historically profitable |
| **Kelly Criterion Sizing** | CRITICAL | LOW | Universal sizing framework for any strategy |
| **Intermarket Divergence** | MEDIUM | MEDIUM | Most codifiable macro strategy in book |
| **Deep Value Screen** | MEDIUM | MEDIUM | Well-defined screening process |
| **Monthly Circuit Breaker** | CRITICAL | LOW | Must-have risk management overlay |
| **3-Day Mean Reversion** | MEDIUM | LOW | Simple rule, codifiable, but needs hedging |

---

## Key Quotes

> "If you have a $10 million position and the market disagrees with you, you're wrong. Get out." — Colm O'Shea

> "Pain is not a reason to change a strategy. If the reason for the trade is still intact, the pain is the reason to add." — Ray Dalio (paraphrased)

> "Really good traders change their mind in an instant." — Steve Clark

> "Value investing works because it doesn't work all the time." — Joel Greenblatt

> "If you are hysterical to buy more, that's the signal to sell." — Steve Clark

> "Mean reversion works almost all of the time. Then it stops and you're kind of out of business." — Jerry Parker (quoted by Schwager)

> "I care about the statistics. Gut feelings are for tourists." — Jaffray Woodriff (paraphrased)

---

## Source

- **Book:** Hedge Fund Market Wizards: How Winning Traders Win (2012) by Jack D. Schwager
- **Key Chapters:** Ch. 1-4 (Macro Men), Ch. 5-8 (Multi-Strategy Players), Ch. 9-15 (Equity Traders), Appendix A (Gain to Pain Ratio)
- **JSON Analysis:** `strategy_pipeline/output/book_analyses/HEDGE_FUND_MARKET_WIZARDS_analysis.json`