# Master Report — Strategy Extraction Pipeline

#trading #pipeline #report

> **Generated:** 2026-03-24
> **Source:** [[Market Wizards - Book Analysis]] + [[New Market Wizards - Book Analysis]]
> **Method:** [[Pipeline Documentation]] — extract, cluster, compare, align

---

## Books Processed

| Book | Author | Year | Traders Interviewed | Strategies Extracted |
|------|--------|------|---------------------|----------------------|
| [[Market Wizards - Book Analysis]] | Jack D. Schwager | 1989 | 16 | 8 |
| [[New Market Wizards - Book Analysis]] | Jack D. Schwager | 1992 | 17 | 10 |
| **Total** | | | **33** | **18** |

After clustering overlapping strategies across both books, **18 raw strategies** collapsed into **8 distinct strategy clusters**.

---

## Strategy Clusters

### Overview Table

| # | Cluster | Confidence | Traders | Books | Key Mechanics |
|---|---------|------------|---------|-------|---------------|
| 1 | [[Trend Following Cluster]] | Very High | 5 | Both | MA crossovers, ATR sizing, trailing stops |
| 2 | [[Breakout Systems Cluster]] | High | 6 | Both | Channel breakouts, congestion breaks, range expansion |
| 3 | [[Moving Average Systems Cluster]] | Very High | 5+ | Both | MAs as the one reliable public indicator |
| 4 | [[Growth Momentum Stocks Cluster]] | Very High | 3 | Both | Accelerating earnings + new highs |
| 5 | [[Statistical Quantitative Cluster]] | High | 2 | Book 2 | Pure statistical edge identification |
| 6 | [[Market Age Reversal Cluster]] | High | 1 | Book 2 | Counter-trend at statistically "old" moves |
| 7 | [[Swing Pattern Trading Cluster]] | High | 1 | Book 2 | 3-push reversals, first-hour breakouts, time stops |
| 8 | [[Options Strategies Cluster]] | Medium | 3 | Book 1 | Volatility mispricing, probability-based |

### Cluster Details

#### 1. Trend Following Systems — Very High Confidence

**Traders:** Dennis, Seykota, Hite, Eckhardt, Basso (5 traders, both books)

Core mechanics:
- Moving average crossovers to define trend direction
- ATR-based position sizing to normalize risk across instruments
- Trailing stops that let winners run indefinitely
- Systematic rules with zero discretionary override

This is the most thoroughly validated edge in the dataset. Every trader who used it profitably did so over decades, not months.

#### 2. Breakout Systems — High Confidence

**Traders:** Dennis, Kovner, Jones, Sperandeo, Raschke, McKay (6 traders, both books)

Core mechanics:
- Channel breakouts (Donchian-style N-bar high/low)
- Congestion/range compression breaks
- Range expansion entries
- Volume confirmation (where available)

Breakout trading appeared across the widest variety of traders. The disagreement is not whether breakouts work, but whether to enter immediately or wait for a retest (see Contradictions below).

#### 3. Moving Average Systems — Very High Confidence

**Traders:** Schwartz, Seykota, Eckhardt, Trout, Basso (5+ traders, both books)

This cluster is notable because of the near-universal agreement: **moving averages are the one reliable public indicator**. Multiple traders independently reached this conclusion across different markets and decades.

Key insight: The specific MA period matters far less than the concept itself. Whether it is a 9 WMA, 20 EMA, or 50 SMA, the edge comes from the trend-smoothing property, not the exact parameter.

#### 4. Growth/Momentum Stocks — Very High Confidence

**Traders:** O'Neil, Ryan, Driehaus (3 traders, both books)

Core mechanics:
- Buy stocks with accelerating earnings (EPS growth quarter-over-quarter)
- Enter on new highs, not pullbacks
- Sell when momentum decelerates
- Concentrated positions in leaders

Highly relevant for equity-specific strategies. Less directly applicable to Gold/Forex but the underlying momentum principle maps well.

#### 5. Statistical/Quantitative Systems — High Confidence

**Traders:** Trout, Blake (2 traders, Book 2)

Core mechanics:
- Pure statistical edge identification (spread relationships, mean reversion)
- No discretionary override
- High trade frequency, small edge per trade
- Rigorous out-of-sample testing

The philosophical foundation for any algo trading approach. Trout's insistence on statistical validation over intuition aligns perfectly with the Mark Douglas probabilistic framework.

#### 6. Market Age/Reversal Trading — High Confidence

**Trader:** Sperandeo (1 trader, Book 2)

Core mechanics:
- Track how "old" a trend is statistically
- Counter-trend entries at extreme age readings
- Tight stops because you are fading momentum
- High selectivity (few trades, high R:R)

Interesting contrarian approach. Not directly compatible with SBRS (which is trend-following), but worth studying for a future mean-reversion strategy.

#### 7. Swing/Pattern Trading — High Confidence

**Trader:** Raschke (1 trader, Book 2)

Core mechanics:
- 3-push reversal patterns
- First-hour breakouts
- Time-based stops (exit if trade does not work within N bars)
- Pattern recognition combined with momentum confirmation

Raschke's time-stop concept (exit if the trade does not move in your favor within a set number of bars) is already implemented in SBRS as the 40-bar max hold rule.

#### 8. Options Strategies — Medium Confidence

**Traders:** Saliba, Hull, Yass (3 traders, Book 1)

Core mechanics:
- Volatility mispricing identification
- Probability-based position construction
- Delta-neutral hedging
- Edge from pricing model accuracy

Lowest confidence for direct application because options strategies require fundamentally different infrastructure. Noted for future portfolio diversification.

---

## Consensus Rules

These rules appeared across multiple independent traders. The number in parentheses is how many of the 33 traders explicitly endorsed the rule.

| # | Rule | Traders | Universality |
|---|------|---------|-------------|
| 1 | Risk 1-2% max per trade | 11 | Very High |
| 2 | **Cut losses fast** | **13** | **Most universal rule in the dataset** |
| 3 | Let winners run | 9 | High |
| 4 | Moving averages are the one reliable public indicator | 6 | High |
| 5 | RSI/stochastics/Fibonacci provide no meaningful edge | 2 (Eckhardt, Trout) | Moderate but significant |
| 6 | Mechanical systems beat discretionary overrides long-term | 7 | High |
| 7 | Buy strength, not weakness | 5 | Moderate |

### Rule Analysis

**Rule 2 (Cut losses fast)** is the single most agreed-upon principle across both books — 13 of 33 traders stated it explicitly, and virtually none contradicted it. This is the closest thing to a universal law in discretionary and systematic trading alike.

**Rule 5 (RSI/stochastics/Fibonacci)** has fewer explicit endorsements but comes from two of the most rigorous quantitative traders in the dataset. Eckhardt (co-creator of the Turtle system) and Trout (pure statistician) both independently concluded these indicators add no edge. SBRS correctly excludes all three.

**Rule 6 (Mechanical beats discretionary)** is the philosophical foundation for building SBRS in the first place — codifying a proven discretionary edge into a mechanical system.

---

## Contradictions

Three significant areas of disagreement emerged across the 33 traders:

### 1. Buy Breakouts Immediately vs Wait for Retest

| Camp | Traders | Argument |
|------|---------|----------|
| Buy immediately | Eckhardt, Dennis | Hesitation costs money; the best breakouts never retrace |
| Wait for retest | Schwartz, Kovner | Retests filter false breakouts; better R:R from tighter stops |

**SBRS Position:** Takes the retest approach. This is an intentional divergence from the majority view, justified by Jamie's 3-4 years of profitable discretionary Gold trading. Gold's structure (high liquidity, institutional participation) makes retests more reliable than in thinner markets.

### 2. Fundamentals Matter vs Pure Technicals

| Camp | Traders | Argument |
|------|---------|----------|
| Fundamentals matter | ~5 traders | Understanding why gives conviction to hold |
| Pure technicals | ~5 traders | Price contains all information; fundamentals are noise |

**SBRS Position:** Pure technicals. For algorithmic trading, technical-only approaches have stronger evidence of systematic replicability. Fundamental analysis introduces subjectivity that cannot be backtested reliably.

### 3. Fixed Stops vs Mental Stops

| Camp | Traders | Argument |
|------|---------|----------|
| Fixed stops | 6 traders | Removes emotion; guaranteed execution |
| Mental stops | 3 traders | Avoids stop-hunting; allows context-based exits |

**SBRS Position:** Fixed stops, but with ATR-buffered placement at non-obvious levels. This synthesizes both camps — the stop is mechanical (no discretion), but the placement accounts for market structure (not round numbers or recent swing points where stops cluster).

---

## SBRS Alignment

### Alignment Score: 6/7 Consensus Rules

| Rule | SBRS Status | Notes |
|------|-------------|-------|
| 1. Risk 1-2% per trade | Aligned | 1% per trade standard |
| 2. Cut losses fast | Aligned | ATR-buffered stops, max 40-bar hold |
| 3. Let winners run | Partially aligned | Fixed 3R TP may cut winners short |
| 4. MAs as primary indicator | Aligned | WMA(9) + SMMA(7) are the core signal |
| 5. No RSI/stochastics/Fibonacci | Aligned | None used in SBRS |
| 6. Mechanical over discretionary | Aligned | Entire purpose of the project |
| 7. Buy strength, not weakness | Intentional divergence | Retest approach = buying temporary weakness within strength |

### Strengths

- **MA-based trend confirmation** matches the single most agreed-upon indicator class
- **Mechanical execution** aligns with 7 traders' insistence on systematic over discretionary
- **1% risk per trade** sits perfectly within the 1-2% consensus range
- **ATR-based stop placement** matches the Trend Following cluster's position sizing philosophy
- **No lagging oscillators** (RSI, stochastics) — correctly excluded per Eckhardt/Trout

### Area for Improvement

**Fixed TP (3R) may be cutting winners short.** Nine traders across both books emphasized letting winners run with trailing stops rather than fixed targets. SBRS currently uses a fixed 3:1 R:R target.

**Possible enhancement:** Test a hybrid exit — take partial profit at 3R, trail the remainder with a 2-ATR trailing stop. This would need walk-forward validation before implementation.

### Intentional Divergence: The Retest Requirement

SBRS requires a retest of the broken level before entry. This contradicts Dennis and Eckhardt (who say buy breakouts immediately) but aligns with Schwartz and Kovner (who prefer confirmation).

**Justification:**
- Jamie's 3-4 years of profitable discretionary trading on Gold uses retests
- Gold's market structure (deep liquidity, institutional flow) produces reliable retests
- Retests allow tighter stop placement, improving R:R from ~2:1 to 3:1+
- The retest filter eliminates a significant percentage of false breakouts

This is not a flaw — it is a market-specific adaptation backed by real trading results.

---

## Recommended Backtest Order

Priority order for testing strategy clusters from this pipeline against SBRS-compatible markets (Gold, Forex, Indices):

| Priority | Strategy Cluster | Rationale | Estimated Effort |
|----------|-----------------|-----------|-----------------|
| 1 | [[Trend Following Cluster]] | Closest to SBRS; shared MA + ATR mechanics; highest confidence | Low — mostly parameter comparison |
| 2 | [[Breakout Systems Cluster]] | SBRS is a breakout system; validate channel breakout variants | Low — test Donchian overlay |
| 3 | [[Swing Pattern Trading Cluster]] | Raschke's time stops already in SBRS; test 3-push pattern | Medium — new pattern detection code |
| 4 | [[Moving Average Systems Cluster]] | Test pure MA crossover (no structure break) as a simpler alternative | Low — remove structure requirement |
| 5 | [[Market Age Reversal Cluster]] | Mean reversion complement to SBRS trend-following | High — entirely new strategy logic |
| 6 | [[Statistical Quantitative Cluster]] | Spread/statistical arb on Gold vs correlated assets | High — new data requirements |
| 7 | [[Growth Momentum Stocks Cluster]] | Equity-specific; not applicable to Gold/Forex | N/A unless expanding to stocks |
| 8 | [[Options Strategies Cluster]] | Requires different infrastructure entirely | N/A for current project scope |

**Immediate action:** Priorities 1-2 can be validated against existing SBRS walk-forward data with minimal new code. Priority 3 is the first genuinely new strategy candidate.

---

## Cross-Book Patterns

### What Both Books Agree On
- Risk management is more important than entry signals
- Most traders blow up at least once before succeeding
- Simplicity beats complexity (the best systems have few rules)
- Conviction + patience = edge (not prediction accuracy)
- Markets change, but human psychology does not

### What Changed Between 1989 and 1992
- More emphasis on systematic/quantitative approaches in Book 2
- Options traders only appeared in Book 1
- Pattern/swing trading (Raschke) emerged as a distinct category in Book 2
- Statistical edge identification (Trout, Blake) became more prominent

### Implications for SBRS Development
The trajectory from Book 1 to Book 2 shows increasing rigor and systematization — exactly the direction SBRS is heading. The most durable edges across both decades were trend-following and breakout systems, which is precisely what SBRS combines.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Books processed | 2 |
| Traders analyzed | 33 |
| Raw strategies extracted | 18 |
| Strategy clusters formed | 8 |
| Consensus rules identified | 7 |
| Contradictions documented | 3 |
| SBRS alignment score | 6/7 rules |
| Clusters applicable to SBRS markets | 6/8 |

---

## Links

- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Strategy Comparison Overview]]
- [[Pipeline Documentation]]
- [[Trend Following Cluster]]
- [[Breakout Systems Cluster]]
- [[Moving Average Systems Cluster]]
- [[Growth Momentum Stocks Cluster]]
- [[Statistical Quantitative Cluster]]
- [[Market Age Reversal Cluster]]
- [[Swing Pattern Trading Cluster]]
- [[Options Strategies Cluster]]
