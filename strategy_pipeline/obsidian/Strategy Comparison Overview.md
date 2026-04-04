# Strategy Comparison Overview

#trading #pipeline #overview

## What This Is

This is the central hub for all strategies extracted from trading books by the pipeline. It connects every [[Master Report|book analysis]], [[Pipeline Documentation|strategy cluster]], and consensus finding into a single reference point. Use this as your starting page when exploring extracted strategies and their relevance to SBRS.

> **Pipeline Stats:** 13 books | 65 traders | 198 strategies extracted | 14 clusters | 14 Python files generated

---

## Books Analysed (13 Total)

| # | Book | Author | Year | Focus | Strategies |
|---|------|--------|------|-------|------------|
| 1 | [[Market Wizards - Book Analysis]] | Jack D. Schwager | 1989 | 16 top traders interviewed | 8 |
| 2 | [[New Market Wizards - Book Analysis]] | Jack D. Schwager | 1992 | 17 next-gen traders | 10 |
| 3 | [[Stock Market Wizards - Book Analysis]] | Jack D. Schwager | 2001 | Equity specialists | 6 |
| 4 | [[Hedge Fund Market Wizards - Book Analysis]] | Jack D. Schwager | 2012 | Hedge fund managers | 5 |
| 5 | [[Complete Turtle Trader - Book Analysis]] | Michael Covel | 2007 | Turtle Trading system deep dive | 3 |
| 6 | [[How to Make Money in Stocks - Book Analysis]] | William O'Neil | 2009 | CAN SLIM growth system | 2 |
| 7 | [[Day Trading Currency Market 1st Ed - Book Analysis]] | Kathy Lien | 2005 | Forex session & breakout strategies | 4 |
| 8 | [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]] | Kathy Lien | 2008 | Extended forex strategies + filters | 5 |
| 9 | [[Algorithmic Trading - Book Analysis]] | Ernest Chan | 2013 | Quantitative strategy frameworks | 6 |
| 10 | [[Trading in the Zone - Book Analysis]] | Mark Douglas | 2000 | Trading psychology & discipline | 0 (framework) |
| 11 | [[Fooled by Randomness - Book Analysis]] | Nassim Taleb | 2001 | Randomness, survivorship bias | 0 (framework) |
| 12 | [[Option Spread Strategies - Book Analysis]] | Anthony Saliba | 2009 | 22 options spread types | 0 (options-specific) |
| 13 | [[Option Volatility and Pricing - Book Analysis]] | Sheldon Natenberg | 2014 | Options pricing theory | 0 (options-specific) |

**Total:** 65 traders referenced, 198 strategies extracted across all books, collapsed into 14 distinct clusters.

---

## Strategy Python Files (14 Total)

All generated strategy files with source, cluster mapping, and key parameters.

| # | File | Source Book(s) | Cluster(s) | Category | Markets | Key Parameters |
|---|------|---------------|------------|----------|---------|----------------|
| 1 | `turtle_breakout.py` | [[Complete Turtle Trader - Book Analysis]] | [[Trend Following Cluster]] | Trend Following | Futures (multi-market) | 20-day channel breakout, 10-day exit, 2% risk/unit |
| 2 | `turtle_s2_55day.py` | [[Complete Turtle Trader - Book Analysis]] | [[Trend Following Cluster]] | Trend Following | Futures (multi-market) | 55-day channel breakout, 20-day exit, 2% risk/unit |
| 3 | `ema_trend_following.py` | [[Market Wizards - Book Analysis]] | [[Trend Following Cluster]] / [[Moving Average Systems Cluster]] | Trend Following | Multi-market | EMA crossover (Seykota-inspired), ATR stops |
| 4 | `schwartz_ma_pullback.py` | [[Market Wizards - Book Analysis]] | [[Moving Average Systems Cluster]] | Trend Following | Equities / Futures | 10-day EMA pullback entry, trend continuation |
| 5 | `lien_london_breakout.py` | [[Day Trading Currency Market 1st Ed - Book Analysis]] | [[Breakout Systems Cluster]] / [[Forex Session Strategies Cluster]] | Breakout | Forex (majors) | London open fake-out filter, 20-pip stop, 1:2 R:R |
| 6 | `lien_inside_day_breakout.py` | [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]] | [[Breakout Systems Cluster]] / [[Volatility Breakout Cluster]] | Breakout | Forex (majors) | 2+ inside days, range expansion entry |
| 7 | `lien_asian_range_breakout.py` | [[Day Trading Currency Market 1st Ed - Book Analysis]] | [[Forex Session Strategies Cluster]] | Session Breakout | Forex (majors) | Asian range high/low, London open trigger |
| 8 | `oneil_canslim_breakout.py` | [[How to Make Money in Stocks - Book Analysis]] | [[Growth Momentum Cluster]] | Momentum | US Equities | 7-factor CAN SLIM screen, cup-with-handle, 50%+ volume |
| 9 | `driehaus_momentum.py` | [[New Market Wizards - Book Analysis]] | [[Growth Momentum Cluster]] | Momentum | US Equities | Earnings acceleration, gap-up entry, aggressive momentum |
| 10 | `chan_kalman_mean_reversion.py` | [[Algorithmic Trading - Book Analysis]] | [[Mean Reversion Cluster]] | Mean Reversion | Equities (pairs) | Kalman filter hedge ratio, half-life lookback (Sharpe 2.4) |
| 11 | `chan_bollinger_pairs.py` | [[Algorithmic Trading - Book Analysis]] | [[Mean Reversion Cluster]] | Mean Reversion | Equities (pairs) | Bollinger band binary signal, Johansen cointegration |
| 12 | `chan_momentum_copper.py` | [[Algorithmic Trading - Book Analysis]] | [[Time-Series Momentum Cluster]] | Momentum | Commodities | 40-day lookback, 40-day hold, time-series momentum |
| 13 | `sperandeo_age_reversal.py` | [[New Market Wizards - Book Analysis]] | [[Volatility Breakout Cluster]] | Contrarian | Multi-market | Trend age measurement, correction length analysis |
| 14 | `trout_risk_rules.py` | [[New Market Wizards - Book Analysis]] | [[Risk Management Cluster]] / [[Statistical Systems Cluster]] | Risk Framework | Universal | 1.5%/trade, 4%/day, 10%/month tiered limits |

### Cross-Reference: Strategies Appearing in Multiple Books

These strategy concepts are independently validated by traders in different books, giving highest confidence.

| Strategy Concept | Books Referencing | Traders | Confidence |
|-----------------|-------------------|---------|------------|
| Trend Following / Channel Breakout | Complete Turtle Trader, Market Wizards, New Market Wizards, Hedge Fund Market Wizards, Algorithmic Trading | Dennis, Eckhardt, Seykota, Hite, Parker, Basso, Abraham, Cheval, Rabar | Very High (5 books, 9 traders) |
| MA Crossover Systems | Market Wizards, New Market Wizards, Day Trading 1st Ed, Day Trading 2nd Ed | Schwartz, Seykota, Eckhardt, Trout, Lien, Hite, Basso, Raschke | Very High (4 books, 8 traders) |
| Breakout + Retest Filtering | Day Trading 1st Ed, Day Trading 2nd Ed, Market Wizards, New Market Wizards | Lien, Kovner, Dennis, Jones, Sperandeo, Raschke | High (4 books, 6 traders) |
| Momentum / Growth (Buy Strength) | How to Make Money in Stocks, Market Wizards, New Market Wizards, Stock Market Wizards | O'Neil, Ryan, Driehaus, Minervini, Walton | High (4 books, 5 traders) |
| Time-Series Momentum | Algorithmic Trading, Complete Turtle Trader, New Market Wizards | Chan, Basso, Parker | High (3 books, 3 traders) |
| Mean Reversion / Pairs | Algorithmic Trading, New Market Wizards, Hedge Fund Market Wizards | Chan, Thorp, Blake | High (3 books, 3 traders) |
| Risk Management (1-2% rule) | 9 of 13 books | Dennis, Seykota, Hite, Kovner, Jones, O'Neil, Schwartz, Trout, Basso, Chan | Very High (9 books, 10 traders) |

---

## Strategy Clusters (14 Total)

Strategies grouped by similarity across all 13 books. Higher overlap = higher confidence the concept is battle-tested.

### Quick Reference

| # | Cluster | Confidence | Books | Traders | Strategies | SBRS Relevance |
|---|---------|------------|-------|---------|------------|----------------|
| 1 | [[Trend Following Cluster]] | Very High | 5/13 | 9 | 3 | HIGH — core SBRS approach |
| 2 | [[Moving Average Systems Cluster]] | Very High | 4/13 | 8 | 2 | CRITICAL — core SBRS signal |
| 3 | [[Breakout Systems Cluster]] | High | 4/13 | 6 | 3 | VERY HIGH — closest to SBRS |
| 4 | [[Growth Momentum Cluster]] | High | 4/13 | 5 | 2 | LOW (equity-only) |
| 5 | [[Time-Series Momentum Cluster]] | High | 3/13 | 3 | 1 | MEDIUM — supports timeframe |
| 6 | [[Mean Reversion Cluster]] | High | 3/13 | 3 | 2 | LOW — different strategy type |
| 7 | [[Forex Session Strategies Cluster]] | High | 2/13 | 1 | 2 | MEDIUM — supports session filter |
| 8 | [[Volatility Breakout Cluster]] | High | 4/13 | 4 | 2 | MEDIUM — informs choppy filter |
| 9 | [[Risk Management Cluster]] | Very High | 8/13 | 8+ | 1 | CRITICAL — foundation of SBRS risk |
| 10 | [[Market Psychology Cluster]] | Very High | 6/13 | 5+ | 0 | CRITICAL — core project philosophy |
| 11 | [[Statistical Systems Cluster]] | High | 3/13 | 4 | 1 | MEDIUM — validates methodology |
| 12 | [[Options Strategies Cluster]] | High | 5/13 | 5 | 0 | LOW — different instrument |
| 13 | [[Gap Trading Cluster]] | Medium | 2/13 | 2 | 0 | LOW — informational |
| 14 | [[Macro Systematic Cluster]] | Medium | 3/13 | 4 | 0 | LOW now, HIGH for future portfolio |
| 15 | [[Deep Value Cluster]] | Medium | 2/13 | 4 | 0 | NONE — different asset class |

### Cluster Detail

#### 1. [[Trend Following Cluster]] — Very High Confidence

- **Books:** Complete Turtle Trader, Market Wizards, New Market Wizards, Hedge Fund Market Wizards, Algorithmic Trading
- **Traders:** Dennis, Eckhardt, Seykota, Hite, Parker, Basso, Abraham, Cheval, Rabar
- **Python:** `turtle_breakout.py`, `turtle_s2_55day.py`, `ema_trend_following.py`
- **SBRS Relevance:** Direct alignment — WMA/SMMA cross is a trend-following signal, ATR-based stops mirror classic trend-following risk management. This is the backbone of SBRS entry logic (Step 1: Trend Context, Step 4: MA Cross Confirmation).

#### 2. [[Moving Average Systems Cluster]] — Very High Confidence

- **Books:** Market Wizards, New Market Wizards, Day Trading 1st Ed, Day Trading 2nd Ed
- **Traders:** Schwartz, Seykota, Eckhardt, Trout, Lien, Hite, Basso, Raschke
- **Python:** `ema_trend_following.py`, `schwartz_ma_pullback.py`
- **SBRS Relevance:** CRITICAL — SBRS uses WMA(9)/SMMA(7) cross as a required gate (Step 4). Multiple Market Wizards rely on MAs as their primary trend filter. Validates SBRS's core signal mechanism.

#### 3. [[Breakout Systems Cluster]] — High Confidence

- **Books:** Day Trading 1st Ed, Day Trading 2nd Ed, Market Wizards, New Market Wizards
- **Traders:** Lien, Kovner, Dennis, Jones, Sperandeo, Raschke
- **Python:** `lien_london_breakout.py`, `lien_inside_day_breakout.py`, `lien_asian_range_breakout.py`
- **SBRS Relevance:** VERY HIGH — Lien's "Filtering False Breakouts" is nearly identical to SBRS. The breakout → retest → continuation framework is shared. SBRS adds MA cross confirmation that these strategies lack.

#### 4. [[Growth Momentum Cluster]] — High Confidence

- **Books:** How to Make Money in Stocks, Market Wizards, New Market Wizards, Stock Market Wizards
- **Traders:** O'Neil, Ryan, Driehaus, Minervini, Walton
- **Python:** `oneil_canslim_breakout.py`, `driehaus_momentum.py`
- **SBRS Relevance:** LOW for direct overlap (equity-only). MEDIUM for principles: breakout-from-base concept parallels SBRS swing breaks. O'Neil's loss-cutting discipline aligns with SBRS risk management.

#### 5. [[Time-Series Momentum Cluster]] — High Confidence

- **Books:** Algorithmic Trading, Complete Turtle Trader, New Market Wizards
- **Traders:** Chan, Basso, Parker
- **Python:** `chan_momentum_copper.py`
- **SBRS Relevance:** MEDIUM — Chan's finding that shorter lookbacks work better for commodities supports SBRS's use of 1H/4H timeframes on Gold.

#### 6. [[Mean Reversion Cluster]] — High Confidence

- **Books:** Algorithmic Trading, New Market Wizards, Hedge Fund Market Wizards
- **Traders:** Chan, Thorp, Blake
- **Python:** `chan_kalman_mean_reversion.py`, `chan_bollinger_pairs.py`
- **SBRS Relevance:** LOW for direct overlap. Chan's risk management (Kelly criterion, half-Kelly) and stationarity testing principles are applicable.

#### 7. [[Forex Session Strategies Cluster]] — High Confidence

- **Books:** Day Trading 1st Ed, Day Trading 2nd Ed
- **Traders:** Lien
- **Python:** `lien_london_breakout.py`, `lien_asian_range_breakout.py`
- **SBRS Relevance:** MEDIUM — SBRS's session filter (skip 16-20 GMT) is directly validated by Lien's session research. The US/Europe overlap as peak activity supports SBRS timing.

#### 8. [[Volatility Breakout Cluster]] — High Confidence

- **Books:** Day Trading 1st Ed, Day Trading 2nd Ed, Market Wizards, Algorithmic Trading
- **Traders:** Lien, Jones, Raschke, Sperandeo, Chan
- **Python:** `lien_inside_day_breakout.py`, `sperandeo_age_reversal.py`
- **SBRS Relevance:** MEDIUM — SBRS's choppy consolidation filter (range < 1 ATR) is the inverse of this concept. Understanding volatility expansion helps time SBRS entries.

#### 9. [[Risk Management Cluster]] — Very High Confidence

- **Books:** Complete Turtle Trader, Market Wizards, New Market Wizards, Hedge Fund Market Wizards, How to Make Money in Stocks, Algorithmic Trading, Fooled by Randomness, Trading in the Zone
- **Traders:** Dennis, Hite, Chan, Trout, O'Neil, Taleb, Dalio, Basso
- **Python:** `trout_risk_rules.py`
- **SBRS Relevance:** CRITICAL — 1% per trade + ATR stops match the most widely endorsed framework across 8/13 books. Gaps: drawdown-based reduction (Turtle rule) and tiered daily/monthly limits (Trout).

#### 10. [[Market Psychology Cluster]] — Very High Confidence

- **Books:** Trading in the Zone, Fooled by Randomness, Market Wizards, New Market Wizards, Stock Market Wizards, Hedge Fund Market Wizards
- **Traders:** Douglas, Taleb, Van Tharp, Faulkner, Krausz
- **Python:** None (mental framework)
- **SBRS Relevance:** CRITICAL — SBRS's CLAUDE.md incorporates Douglas's 5 Fundamental Truths. Taleb's warnings about overfitting motivate walk-forward validation and sacred parameters.

#### 11. [[Statistical Systems Cluster]] — High Confidence

- **Books:** New Market Wizards, Hedge Fund Market Wizards, Algorithmic Trading
- **Traders:** Trout, Blake, Chan, Thorp
- **Python:** `trout_risk_rules.py`
- **SBRS Relevance:** MEDIUM — Validates walk-forward methodology and Monte Carlo testing. Trout's insistence on statistical validation aligns with SBRS's 500-trade minimum.

#### 12. [[Options Strategies Cluster]] — High Confidence

- **Books:** Option Spread Strategies, Option Volatility & Pricing, Market Wizards, Hedge Fund Market Wizards, Fooled by Randomness
- **Traders:** Saliba, Natenberg, Tony Saliba (MW), Jamie Mai, Taleb
- **Python:** None (different instrument infrastructure)
- **SBRS Relevance:** LOW for direct overlap. Defined-risk concept aligns with SBRS pre-defined stops. Options could hedge SBRS positions in future.

#### 13. [[Gap Trading Cluster]] — Medium Confidence

- **Books:** Algorithmic Trading, Day Trading 2nd Ed
- **Traders:** Chan, Lien
- **Python:** None (requires intraday execution infrastructure)
- **SBRS Relevance:** LOW — Informational for understanding Gold session opens.

#### 14. [[Macro Systematic Cluster]] — Medium Confidence

- **Books:** Hedge Fund Market Wizards, Algorithmic Trading, New Market Wizards
- **Traders:** Dalio, O'Shea, Druckenmiller, Chan
- **Python:** None (requires cross-asset infrastructure)
- **SBRS Relevance:** LOW now, HIGH for future portfolio expansion. Dalio's 4-quadrant framework could inform Gold allocation based on inflation regime.

#### 15. [[Deep Value Cluster]] — Medium Confidence

- **Books:** Stock Market Wizards, Hedge Fund Market Wizards
- **Traders:** Lauer, Okumus, Greenblatt, Platt
- **Python:** None (fundamental equity analysis)
- **SBRS Relevance:** NONE — Different asset class and methodology entirely.

---

## Consensus Rules (12 Total)

Rules that multiple traders independently arrived at across all 13 books. The more supporters, the higher the confidence.

| # | Rule | Supporters | Books | SBRS Alignment |
|---|------|-----------|-------|----------------|
| 1 | Never risk more than 1-2% per trade | Dennis, Seykota, Hite, Kovner, Jones, O'Neil, Schwartz, Trout, Basso, Chan | 9 | ✅ 1% per trade |
| 2 | Cut losses quickly and mechanically | Dennis, Seykota, O'Neil, Schwartz, Douglas, Eckhardt, Kovner, Driehaus | 8 | ✅ ATR-based stops |
| 3 | Let winners run — don't cut profits short | Dennis, Seykota, Hite, Marcus, Kovner, Driehaus, O'Neil | 7 | ⚠️ Fixed 3R TP may limit upside |
| 4 | MAs are the most useful public indicator | Seykota, Schwartz, Eckhardt, Trout, Hite, O'Neil, Lien | 7 | ✅ WMA(9)/SMMA(7) cross |
| 5 | Think in probabilities over 100+ trades | Douglas, Taleb, Dennis, Eckhardt, Seykota, Chan | 6 | ✅ Walk-forward over 1000+ trades |
| 6 | Diversify across uncorrelated markets | Hite, Dalio, Parker, Dennis, Basso, Chan | 6 | ⚠️ Gold only (indices in progress) |
| 7 | Trade in direction of higher TF trend | Seykota, Lien, O'Neil, Schwartz, Eckhardt | 5 | ✅ 4H trend check before 1H entry |
| 8 | Reduce position size during drawdowns | Dennis, Jones, Schwartz, Marcus, Trout | 5 | ❌ Not yet implemented |
| 9 | Mechanical systems > discretionary overrides | Eckhardt, Trout, Basso, Blake, Dennis | 4 | ✅ Fully mechanical SBRS |
| 10 | Volume/ATR confirms breakout quality | O'Neil, Lien, Dennis, Kovner | 4 | ⚠️ ATR for stops, not breakout validation |
| 11 | Use half-Kelly or less for leverage | Chan, Taleb, Thorp | 3 | ✅ Conservative 1% (well below Kelly) |
| 12 | RSI/stochastics/Fibonacci have near-zero edge | Eckhardt, Trout | 2 | ✅ None used in SBRS |

### SBRS Alignment Score: 9/12 Rules Aligned

- **8 fully aligned** ✅ (rules 1, 2, 4, 5, 7, 9, 11, 12)
- **3 partially aligned** ⚠️ (fixed TP, diversification in progress, ATR usage)
- **1 not yet implemented** ❌ (drawdown-based position reduction)

### Alignment Notes

**Rule 3 — Let winners run ⚠️:** SBRS uses a fixed 3R take profit, guaranteeing known expectancy but potentially leaving money on the table in strong trends. The Market Wizards consensus suggests trailing stops instead. This is a deliberate SBRS design choice — fixed TP provides more consistent walk-forward results. Worth testing a hybrid: partial profit at 3R, trail remainder.

**Rule 6 — Diversification ⚠️:** Currently Gold only, but indices (S&P, NASDAQ, DAX) are in testing. Long-term goal: 5-10 strategies at 0.15-0.2% each.

**Rule 8 — Drawdown reduction ❌:** The Turtle rule (reduce risk by 20% for every 10% portfolio drawdown) is endorsed by 5 traders. This should be implemented without changing entry logic.

---

## Contradictions (5 Total)

Where the 65 traders across 13 books disagree with each other — and the design decisions SBRS made.

### 1. Buy Breakouts Immediately vs Wait for Retest

| Camp | Traders | Argument |
|------|---------|----------|
| Buy immediately | Eckhardt, Dennis, Driehaus, O'Neil | Hesitation costs money; the best breakouts never retrace |
| Wait for retest | Schwartz, Kovner, Lien, SBRS | Retests filter false breakouts; better R:R from tighter stops |

**SBRS Position:** Retest approach. Gold-specific edge — false breakouts on Gold are frequent, and the retest filter eliminates the majority of them. Validated over 10Y walk-forward. Both camps are profitable; this is a valid middle ground.

### 2. Fixed Take-Profit vs Ride the Trend

| Camp | Traders | Argument |
|------|---------|----------|
| Never use fixed TP | Dennis, Seykota, Hite, Basso | A few huge winners pay for all losers. Fixed targets cap best trades. |
| Take defined profits | O'Neil, Lien, Schwartz | Most trades don't become huge winners. Taking profits maintains high win rate. |

**SBRS Position:** Fixed 3R take-profit. Appropriate for 1H timeframe and 40-bar max hold. Produces more consistent walk-forward results. Consider hybrid: partial profit at 3R, trail remainder.

### 3. Simple vs Complex Systems

| Camp | Traders | Argument |
|------|---------|----------|
| 3-4 parameters max | Eckhardt, Basso, Dennis | More parameters = more overfitting. Simplicity is robustness. |
| Multiple factor confirmation | O'Neil, Lien, Weinstein | Multiple independent confirmations reduce false signals. |

**SBRS Position:** 5 entry conditions but only 2 parameterized (MA periods, ATR lookback). The rest are structural (breakout, retest, trend direction). Aligns with Eckhardt's intent — few optimizable parameters with structural filters.

### 4. Mean Reversion vs Momentum as Primary Edge

| Camp | Traders | Argument |
|------|---------|----------|
| MR dominates short timeframes | Chan, Schwartz, Blake | Intraday to days favors mean reversion. Highest Sharpe ratios. |
| Momentum/trend dominates | Dennis, Seykota, Hite, Eckhardt | Trends persist at all timeframes. Biggest profits from riding extended moves. |

**SBRS Position:** Trend-following on 1H/4H which straddles the boundary. Chan resolves this: the timeframe determines which edge dominates. SBRS's 1H timeframe may benefit from elements of both.

### 5. Concentration vs Diversification

| Camp | Traders | Argument |
|------|---------|----------|
| Concentrate in 4-7 best ideas | O'Neil, Driehaus, Druckenmiller, Soros | Diversification hedges against ignorance. Bet big with conviction. |
| Diversify across 30-60+ markets | Hite, Dalio, Parker, Dennis, Basso | No single trade should matter. Diversification is the only free lunch. |

**SBRS Position:** Currently concentrated (Gold only) but expanding to indices. Long-term goal: 5-10 strategies at 0.15-0.2% each. Aligns with the diversification camp for systematic trading.

---

## SBRS Validation Summary

Based on the analysis of 65 traders across 13 books:

- **8 of 12** consensus rules fully aligned with SBRS ✅
- **3 of 12** have justified divergences ⚠️ (fixed TP, diversification, ATR usage)
- **1 of 12** not yet implemented ❌ (drawdown-based position reduction)
- **5 of 15** strategy clusters directly validate SBRS components (Trend, Breakout, MA, Session, Volatility)
- **3 of 15** validate SBRS methodology and philosophy (Risk, Psychology, Statistical)
- **All 5** contradictions have documented SBRS design decisions with rationale

### SBRS Strengths (Confirmed by Multi-Book Consensus)

- **MA-based trend confirmation** — matches the most agreed-upon indicator class (7 traders, 7 books)
- **Breakout + retest entry** — validated by Lien's near-identical "Filtering False Breakouts" strategy
- **Mechanical execution** — aligns with consensus that systematic beats discretionary
- **1% risk per trade** — sits within the 1-2% consensus range (10 traders, 9 books)
- **ATR-based stops** — matches Turtle/Basso volatility normalization philosophy
- **No lagging oscillators** — correctly excludes RSI/stochastics/Fibonacci per Eckhardt/Trout
- **Session filter** — supported by Lien's session research (16-20 GMT is a proven dead zone)
- **Probabilistic philosophy** — directly implements Douglas's 5 Fundamental Truths + Taleb's anti-overfit warnings

### SBRS Gaps (Potential Enhancements from Cross-Book Analysis)

1. **Drawdown-based position reduction** — Turtle rule (reduce 20% per 10% drawdown). Endorsed by 5 traders.
2. **Tiered daily/monthly limits** — Trout's cascading safety net (4% daily, 10% monthly).
3. **Trailing stop component** — 9 traders advocate letting winners run. Test hybrid: partial at 3R, trail remainder.
4. **Inside day pre-filter** — Lien's volatility compression detection could improve SBRS breakout timing.
5. **Volume/ATR breakout validation** — O'Neil and Lien use volume to confirm breakout quality. Could use ATR expansion as proxy for Gold.

---

## Related Project Notes

- [[00-MOC-Zeros-Requiem]] — Main project map of content
- [[19-Priority-1-Signal-Generation]] — SBRS signal generation context
- [[CLAUDE]] — Master strategy specification and sacred parameters

---

## Links

### Book Analyses
- [[Market Wizards - Book Analysis]]
- [[New Market Wizards - Book Analysis]]
- [[Stock Market Wizards - Book Analysis]]
- [[Hedge Fund Market Wizards - Book Analysis]]
- [[Complete Turtle Trader - Book Analysis]]
- [[How to Make Money in Stocks - Book Analysis]]
- [[Day Trading Currency Market 1st Ed - Book Analysis]]
- [[Day Trading Swing Trading Currency 2nd Ed - Book Analysis]]
- [[Algorithmic Trading - Book Analysis]]
- [[Trading in the Zone - Book Analysis]]
- [[Fooled by Randomness - Book Analysis]]
- [[Option Spread Strategies - Book Analysis]]
- [[Option Volatility and Pricing - Book Analysis]]

### Strategy Clusters
- [[Trend Following Cluster]]
- [[Moving Average Systems Cluster]]
- [[Breakout Systems Cluster]]
- [[Growth Momentum Cluster]]
- [[Time-Series Momentum Cluster]]
- [[Mean Reversion Cluster]]
- [[Forex Session Strategies Cluster]]
- [[Volatility Breakout Cluster]]
- [[Risk Management Cluster]]
- [[Market Psychology Cluster]]
- [[Statistical Systems Cluster]]
- [[Options Strategies Cluster]]
- [[Gap Trading Cluster]]
- [[Macro Systematic Cluster]]
- [[Deep Value Cluster]]

### Other
- [[Pipeline Documentation]] — How the extraction pipeline works
- [[Master Report]] — Full cross-book analysis output

---

*Generated by Strategy Extraction Pipeline v3 — 2026-03-25*
