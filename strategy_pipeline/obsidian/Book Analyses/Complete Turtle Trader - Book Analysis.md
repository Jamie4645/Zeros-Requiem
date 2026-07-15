> [!warning] SUPERSEDED (2026-07-02 blank-slate re-read)
> This note is a strategy-extraction catalog from the SBRS era and must NOT be treated as canon. The 2026-07 fresh re-read of the full book text found extraction-focus, missing load-bearing content, and in several notes fabricated material (invented quotes/parameters). Durable record: knowledge-base/92-Books-Blank-Slate-Review.md.

# Complete Turtle Trader - Book Analysis

#trading #book-analysis #turtle #trend-following #channel-breakout

**Book:** The Complete Turtle Trader (2007)
**Author:** Michael W. Covel
**Focus:** Trend following via channel breakouts with ATR-based position sizing
**Link to:** [[Master Report]] | [[Strategy Comparison Overview]]

---

## Overview

Documents Richard Dennis's 1983-1988 experiment where he trained novice traders ("Turtles") using systematic trend-following rules. The Turtles collectively made $150 million for Dennis. Several went on to manage billions independently. This book contains the most completely documented proprietary trading system ever published.

**Core Edge:** Systematic channel breakout entries + ATR-based position sizing + aggressive pyramiding into winners + cutting losses at 2N stops.

---

## Strategy 1: Turtle System One (S1) - 20-Day Breakout

| Parameter | Value |
|-----------|-------|
| **Type** | Trend Following / Channel Breakout |
| **Timeframe** | Daily (end-of-day signals) |
| **Markets** | Any liquid futures, stocks, forex, commodities |
| **Entry (Long)** | Price makes new 20-day high |
| **Entry (Short)** | Price makes new 20-day low |
| **Exit (Long)** | Price makes new 10-day low OR 2N stop hit |
| **Exit (Short)** | Price makes new 10-day high OR 2N stop hit |
| **Position Size** | 2% account risk per "unit" |
| **Stop Loss** | 2 x ATR(20) from entry |
| **First Day Stop** | 0.5N on day 1 |
| **Win Rate** | ~35-40% |
| **Clarity** | 9/10 |
| **Completeness** | 8/10 |

### S1 Filter Rule (Critical)

- **Skip** the S1 breakout if the previous S1 breakout was a **winner** (even theoretical)
- If previous breakout was a **2N loss**, take the current signal
- Direction of previous breakout is **irrelevant** for the filter
- **Failsafe:** If filtered signal is missed and market keeps trending, enter at the S2 (55-day) breakout

### S1 Entry Logic (Pseudocode)

```
IF price > highest_high(20 days):
    IF last_S1_breakout was a LOSER (or 2N loss):
        GO LONG
    ELSE:
        SKIP (but monitor for S2 55-day breakout as failsafe)

IF price < lowest_low(20 days):
    IF last_S1_breakout was a LOSER (or 2N loss):
        GO SHORT
    ELSE:
        SKIP
```

---

## Strategy 2: Turtle System Two (S2) - 55-Day Breakout

| Parameter | Value |
|-----------|-------|
| **Type** | Trend Following / Channel Breakout (Longer-term) |
| **Timeframe** | Daily (end-of-day signals) |
| **Markets** | Same as S1 |
| **Entry (Long)** | Price makes new 55-day high |
| **Entry (Short)** | Price makes new 55-day low |
| **Exit (Long)** | Price makes new 20-day low OR 2N stop hit |
| **Exit (Short)** | Price makes new 20-day high OR 2N stop hit |
| **Position Size** | 2% account risk per "unit" |
| **Filter Rule** | **NONE** - every breakout is taken |
| **Clarity** | 9/10 |
| **Completeness** | 9/10 |

S2 is simpler and more robust. No filter rule means more trades but also more whipsaws. Jerry Parker emphasized that **core simple breakout/moving average systems are the real edge.**

---

## Position Sizing: The N/ATR System (CRITICAL)

This is the heart of Turtle trading. The entry rules are almost irrelevant compared to position sizing.

### Step 1: Calculate N (ATR)

```
True Range = MAX(
    High - Low,
    ABS(High - Previous Close),
    ABS(Low - Previous Close)
)

N = 20-day Moving Average of True Range
```

### Step 2: Calculate Unit Size

```
Dollar Volatility = N x Dollar_Per_Point
Account Risk = Account Equity x 2%
Contracts = FLOOR(Account Risk / (2 x Dollar Volatility))
```

**Example:**
- Account: $100,000
- Corn: N = 7 cents, $50 per cent
- Dollar Volatility = 0.07 x $50 = $3.50 per contract per N
- 2N stop = $7.00 per contract risk = $700
- Account Risk = $100,000 x 2% = $2,000
- Contracts = FLOOR($2,000 / $700) = **2 contracts**

### Step 3: Equalize Risk

One unit of Corn has the **same risk** as one unit of Gold, one unit of Yen, or one unit of any market. This is how Turtles traded 30+ markets without fundamental expertise in any of them.

---

## Pyramiding Rules

| Rule | Detail |
|------|--------|
| **Add interval** | Every 1N (one ATR) the market moves in your favor |
| **Max units** | 5 per market |
| **Stop adjustment** | Move ALL stops to new unit's 2N stop level |
| **Effect** | Locks in profit on earlier units as new units are added |

### Pyramiding Example (Live Cattle)

| Unit | Entry | Stop | Open P/L | Risk to Equity |
|------|-------|------|----------|----------------|
| 1 | 74.00 | 72.40 | $0 | 1.28% |
| 2 | 74.80 | 73.20 | $320 | 1.92% total |
| 3 | 75.60 | 74.20 | $960 | 1.60% total |
| 4 | 76.30 | 74.90 | $1,800 | 1.68% total |
| 5 | 77.00 | 75.30 | $2,920 | 2.40% total |

**Exit at 84.50:** Total profit = **$17,920 (35.8% of $50,000 account)** from a single trade.

This is how the Turtles turned 35% win rates into massive returns.

---

## Unit Limits (Correlation Management)

| Limit | Maximum Units |
|-------|---------------|
| Single market | 4-5 units |
| Closely correlated markets (e.g., Gold + Silver) | 6 units |
| Loosely correlated markets | 10 units |
| Single direction (all longs or all shorts) | 12 units |
| Total portfolio | 20-24 units |

### Correlation Examples

**HIGH correlation (treat as same market):**
- Corn + Soybeans
- Gold + Silver
- 5-Year Notes + 10-Year Notes
- S&P 500 + Dow Jones

**LOW correlation (good diversification):**
- Japanese Yen + Crude Oil
- Gold + Live Cattle
- Sugar + Five-Year Notes

### Long/Short Offset Formula

```
Net Risk = Larger side - (Smaller side / 2)

Example: 4 longs + 3 shorts = 4 - (3/2) = 2.5 net units of risk
```

This allowed Turtles to hold MORE total positions without exceeding risk limits.

---

## Drawdown Reduction Rule

| Account Drawdown | Unit Size Reduction |
|-----------------|---------------------|
| -10% | Reduce by 20% (2.0% -> 1.6%) |
| -20% | Reduce by another 20% (1.6% -> 1.28%) |
| -30% | Reduce again (1.28% -> 1.02%) |

**Restoration:** Increase unit sizes back as account recovers.

Key insight: This prevents the **arithmetic progression toward ruin**. A small exponential recovery from one big trend will always surpass the steepest linear drawdown from small losses.

---

## Markets Traded by Original Turtles

| Sector | Markets |
|--------|---------|
| **Bonds** | 30-Year T-Bond, 10-Year T-Bond, 90-Day T-Bill, Eurodollar |
| **Currencies** | British Pound, French Franc, Japanese Yen, Canadian Dollar, Swiss Franc, Deutschmark |
| **Metals** | Gold, Silver, Copper |
| **Softs** | Cotton, Sugar, Cocoa, Coffee |
| **Energy** | Crude Oil, Heating Oil, Unleaded Gas |
| **Index** | S&P 500 |
| **Grains** | Corn, Soybeans, Wheat |
| **Meats** | Live Cattle, Lean Hogs |

**Total: ~30 markets.** Modern implementations trade 30-65+ markets including forex, ETFs, and stock indices.

---

## Performance Data

### During Experiment (1984-1988)

| Turtle | 1984 | 1985 | 1986 | 1987 |
|--------|------|------|------|------|
| Stig Ostgaard | +20% | **+297%** | +108% | +87% |
| Liz Cheval | -21% | +52% | +135% | **+178%** |
| Jerry Parker | -10% | +129% | +124% | +37% |
| Jim DiMaria | - | +71% | +132% | +97% |
| Paul Rabar | - | +170% | **+185%** | +135% |
| Mike Cavallo | -14% | +100% | +34% | +111% |
| Howard Seidler | -16% | +100% | +96% | +80% |

**Total for Dennis:** $150M gross profit. $110M net to Dennis (85/15 split).

### Post-Experiment Trader Expectations (Through 2006)

| Trader | Avg Win Month | Avg Loss Month | Win % | Monthly Expectation |
|--------|---------------|----------------|-------|---------------------|
| Salem Abraham | 8.50% | -5.77% | 55.4% | **2.13%** |
| Liz Cheval | 12.45% | -6.64% | 49.6% | **2.83%** |
| Paul Rabar | 9.26% | -4.89% | 52.5% | **2.54%** |
| Howard Seidler | 6.57% | -4.90% | 55.6% | **1.47%** |
| Jerry Parker | 5.06% | -3.59% | 57.4% | **1.38%** |
| Jim DiMaria | 4.16% | -3.17% | 54.3% | **0.81%** |

Compare to buy-and-hold:
| Index | Avg Win Month | Avg Loss Month | Win % | Monthly Expectation |
|-------|---------------|----------------|-------|---------------------|
| S&P 500 | 3.83% | -3.92% | 58.4% | **0.60%** |
| NASDAQ | 4.98% | -4.61% | 57.8% | **0.93%** |

---

## Why Some Turtles Failed

1. **Could not handle losing 60-70% of trades** - psychologically crushed by small losses
2. **Broke position sizing rules** - especially Curtis Faith who traded far larger than allowed
3. **Let ego override discipline** - competed with other Turtles instead of following the system
4. **Failed to build a real business** - relied on Turtle fame, not entrepreneurial drive
5. **Switched to mean reversion** - strategies that "felt" better but have fatal tail risk
6. **Could not handle boredom** - no trading for weeks/months when markets are flat
7. **Lacked killer instinct** - couldn't pull the trigger at all-time highs or after losing streaks

### The Dennis Paradox

Dennis himself violated his own rules. In April 1988, he lost **55% in one month** while his Turtles only lost 10-12%. His Turtles calculated that Dennis was taking **100x more risk** than they were allowed. The creator of the system couldn't follow his own rules.

---

## Key Risk Finding: The 1986 Memo

Four Turtles (Shanks, Rabar, Keefer, Svoboda) spent a year building backtesting software and discovered:

- **Expected worst-case drawdown was 50%** (what Dennis told them)
- **Actual worst-case drawdown was 80%** (what really happened)
- **Cause:** When S1 and S2 generate signals simultaneously, position size doubles
- **Fix:** All Turtles ordered to reduce position sizes by 50%

**Lesson:** Even system creators can miscalculate risk. Always validate independently.

---

## Modern Applicability

### What Still Works

- Channel breakout / trend following remains profitable across decades
- ATR-based position sizing is universal best practice
- Pyramiding into winners is still the key to outsized returns
- Diversification across uncorrelated markets reduces drawdown
- The psychology is timeless - most traders still can't follow simple rules

### What Needs Adaptation

- **Lower returns** - markets are more efficient, expect 10-20% vs 100%+
- **More markets** - need 30-65+ for adequate diversification
- **Lower leverage** - institutional capital demands smoother returns
- **Automated execution** - no more phone calls to the floor
- **Shorter lookbacks** - modern markets may require 10-40 day breakouts vs 20-55
- **Lower transaction costs** - benefits trend followers significantly

### Modern Practitioners Using Turtle-Style Methods

- Chesapeake Capital (Jerry Parker) - $1B+
- Eckhardt Trading (William Eckhardt)
- Abraham Trading Company (Salem Abraham)
- Man AHL, Winton Group, and hundreds of CTAs globally

---

## Codification Priority

| Strategy | Priority | Difficulty | Expected Edge |
|----------|----------|------------|---------------|
| **S2 (55-day breakout)** | HIGH | LOW | Robust, simple, proven 40+ years |
| **S1 (20-day with filter)** | HIGH | MEDIUM | More trades, filter adds complexity |
| **Parker Adaptation** | MEDIUM | LOW | Lower leverage, institutional-grade |
| **N-based position sizing** | CRITICAL | LOW | Must-have for any trend system |
| **Pyramiding** | HIGH | MEDIUM | Key profit multiplier |

---

## Key Quotes

> "We found that liquidations are vastly more important than initiations. If you initiate purely randomly, you do surprisingly well with a good liquidation criterion." - William Eckhardt

> "Pure price systems are close enough to the North Pole that any departure tends to bring you farther south." - William Eckhardt

> "The minute it takes too much thinking and too much fancy work, it is going to be a very bad situation." - Jerry Parker

> "Mean reversion works almost all of the time. Then it stops and you're kind of out of business." - Jerry Parker

> "Good traders apply every ounce of intelligence they have into the creation of their systems, but then they're dumbbells in following them." - Richard Dennis

> "I care about the statistics. Just because I don't understand it doesn't mean I'm not going to bet on it." - Salem Abraham

---

## Source

- **Book:** The Complete Turtle Trader (2007) by Michael W. Covel
- **Key Chapters:** Ch. 4 (Philosophy), Ch. 5 (The Rules), Ch. 7 (Performance), Ch. 9-12 (Post-Experiment), Ch. 13 (Second-Generation), Appendix III-IV (Performance Data)
- **JSON Analysis:** `strategy_pipeline/output/book_analyses/COMPLETE_TURTLE_TRADER_analysis.json`
