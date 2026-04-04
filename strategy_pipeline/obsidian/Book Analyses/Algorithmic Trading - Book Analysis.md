# Algorithmic Trading - Book Analysis

#trading #book-analysis #mean-reversion #momentum #pairs-trading #statistical-arbitrage #kelly-criterion #futures

**Book:** Algorithmic Trading: Winning Strategies and Their Rationale (2013)
**Author:** Ernest P. Chan
**Focus:** Mean reversion, momentum, pairs trading, statistical arbitrage, risk management
**Link to:** [[Master Report]] | [[Strategy Comparison Overview]]

---

## Overview

A highly technical, quantitative guide to systematic trading covering mean reversion (pairs, cross-sectional, calendar spreads), momentum (time series, cross-sectional, roll return), and risk management (Kelly criterion, CPPI). Chan provides MATLAB code, full mathematical derivations, and backtest results for most strategies. The book bridges academic finance research and practical algo trading, with a strong emphasis on stationarity testing before deploying any mean-reversion strategy.

**Core Edge:** Statistical relationships (cointegration, mean reversion, momentum) exploited via rigorous testing (ADF, Johansen, Hurst exponent, half-life) with Kelly-based position sizing.

**32 strategies extracted** — 20 highly codifiable, 5 conceptual-only, 7 requiring infrastructure beyond retail. This note covers the 24 strategies with clarity score >= 7, grouped by category.

---

## Part I: Mean Reversion Strategies (1–14)

### Strategy 1: Linear Mean Reversion on Cointegrated ETF Pair (EWA-EWC)

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Pairs Trading |
| **Markets** | ETFs: EWA (Australia), EWC (Canada), IGE (Natural Resources) |
| **Timeframe** | Daily |
| **Entry** | Position = −Z-score (linear scaling, more extreme = larger) |
| **Exit** | Z-score crosses zero (spread reverts to mean) |
| **Lookback** | Half-life of OU regression (adaptive) |
| **APR** | 12.6% |
| **Sharpe** | 1.4 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

#### Entry Logic

```
hedge_ratios = johansen_eigenvector([EWA, EWC, IGE])
spread = hedge_ratios[0]*EWA + hedge_ratios[1]*EWC + hedge_ratios[2]*IGE

# Compute adaptive lookback
delta_y = lambda * y_lag + noise
halflife = -log(2) / lambda

z_score = (spread - rolling_mean(halflife)) / rolling_std(halflife)
position = -z_score  # Linear: more extreme spread = larger position
# Allocate across legs proportional to hedge ratios
```

Key innovation: Johansen over Engle-Granger for multi-leg cointegration. Half-life method eliminates arbitrary lookback selection. IGE as third leg improves cointegration stability.

---

### Strategy 2: GLD-USO Price Spread Mean Reversion (Dynamic Hedge)

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Pairs Trading |
| **Markets** | ETFs: GLD (Gold), USO (Oil) |
| **Timeframe** | Daily |
| **Entry** | Position = −Z-score when spread deviates |
| **Exit** | Z-score crosses zero |
| **Hedge Ratio** | Rolling OLS over half-life window |
| **APR** | 10.9% |
| **Sharpe** | 0.59 |
| **Period** | 2007–2012 |
| **Clarity** | 8/10 |

Lower Sharpe than EWA-EWC due to weaker cointegration between Gold and Oil. Illustrates that cointegration strength directly determines strategy quality — always test before trading.

---

### Strategy 3: Bollinger Band Mean Reversion on GLD-USO

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Pairs Trading |
| **Markets** | ETFs: GLD, USO |
| **Timeframe** | Daily |
| **Entry (Long Spread)** | Spread < lower band (Z < −1.0) |
| **Entry (Short Spread)** | Spread > upper band (Z > +1.0) |
| **Exit** | Spread crosses mean (Z crosses 0) |
| **Position Size** | Binary (full size, not scaled) |
| **Lookback** | Half-life window |
| **APR** | 17.8% |
| **Sharpe** | 0.96 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

#### Entry Logic

```
spread = GLD - hedge_ratio * USO
upper_band = rolling_mean(halflife) + 1.0 * rolling_std(halflife)
lower_band = rolling_mean(halflife) - 1.0 * rolling_std(halflife)

IF spread < lower_band:
    GO LONG spread (buy GLD, sell USO)
IF spread > upper_band:
    GO SHORT spread (sell GLD, buy USO)
IF spread crosses rolling_mean:
    EXIT
```

Bollinger approach outperforms linear on this pair (17.8% vs 10.9% APR) but can miss gradual reversions. Linear is better for smooth mean reversion; Bollinger better for sharp dislocations.

---

### Strategy 4: Kalman Filter Mean Reversion on EWA-EWC

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Pairs Trading |
| **Markets** | ETFs: EWA, EWC |
| **Timeframe** | Daily |
| **Kalman delta** | 0.0001 (state transition variance) |
| **Kalman Ve** | 0.001 (observation noise) |
| **Entry** | Forecast error exceeds threshold × √Q |
| **Exit** | Forecast error crosses zero |
| **APR** | 26.2% |
| **Sharpe** | 2.4 |
| **Period** | 2007–2012 |
| **Clarity** | 8/10 |

**Best-performing mean reversion strategy in the book.**

#### Entry Logic

```
# Kalman Filter state: hedge_ratio
# Observation: EWA = hedge_ratio * EWC + intercept + noise

forecast_error = EWA_actual - EWA_predicted
sqrt_Q = sqrt(forecast_error_variance)

IF forecast_error < -entry_threshold * sqrt_Q:
    LONG spread
IF forecast_error > entry_threshold * sqrt_Q:
    SHORT spread

position_size = -forecast_error / sqrt_Q
```

Eliminates the lookback window selection problem entirely. The Kalman Filter adapts the hedge ratio in real-time, self-correcting to regime changes. The `delta` parameter controls how fast the hedge ratio can change — too high = noisy, too low = slow to adapt.

---

### Strategy 5: Buy-on-Gap Model (Long SPX Stocks)

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Gap Trading |
| **Markets** | US Equities (S&P 500 components) |
| **Timeframe** | Daily (overnight gaps, intraday hold) |
| **Entry** | Buy stocks with largest negative gaps at open |
| **Exit** | Sell at market close (MOC orders) |
| **Hold Period** | Intraday only |
| **APR** | 8.7% |
| **Sharpe** | 1.5 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

```
gap = (open - prev_close) / prev_close

IF gap < -threshold:
    BUY at open
    SELL at close (MOC)
```

Works because overnight gaps in liquid stocks partially revert during the trading day due to order flow imbalances. Equal weight across selected stocks. No overnight risk.

---

### Strategy 6: Short-on-Gap Model

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Gap Trading |
| **Markets** | US Equities (S&P 500 components) |
| **Timeframe** | Daily (overnight gaps, intraday hold) |
| **Entry** | Short stocks with largest positive gaps at open |
| **Exit** | Cover at market close (MOC) |
| **APR** | 46% |
| **Sharpe** | 1.27 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

Very high APR but likely inflated by 2008 crisis period. Author warns about survivorship bias and stock borrow availability. Real-world execution harder than the long side due to locate requirements.

---

### Strategy 8: Cross-Sectional Mean Reversion (Khandani-Lo Long-Short)

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Cross-Sectional / Long-Short Equity |
| **Markets** | US Equities (S&P 500 or Russell 1000) |
| **Timeframe** | Daily rebalance |
| **Entry (Long)** | Bottom decile by prior-day return (worst performers) |
| **Entry (Short)** | Top decile by prior-day return (best performers) |
| **Exit** | Rebalance next day (close all, re-enter) |
| **Weighting** | Equal weight, dollar-neutral |
| **APR** | 13.7% |
| **Sharpe** | 1.3 |
| **Period** | 2001–2012 |
| **Clarity** | 8/10 |

```
FOR each trading day:
    rank all stocks by yesterday's return
    LONG = bottom 10% (yesterday's losers)
    SHORT = top 10% (yesterday's winners)
    equal_weight within each side
    dollar_neutral (equal long and short notional)
    HOLD 1 day, then rebalance
```

**Critical warning:** This strategy type suffered massive drawdowns during the August 2007 quant crisis when many hedge funds ran the same strategy simultaneously. Key lesson about **crowded trades** — when everyone runs the same mean-reversion signal, the exit becomes the risk.

---

### Strategy 10: AUD/USD vs CAD/USD Forex Pair (Johansen Cointegration)

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Forex Pairs Trading |
| **Markets** | Forex: AUD/USD, CAD/USD |
| **Timeframe** | Daily |
| **Entry** | Position = −Z-score (linear) |
| **Exit** | Z-score crosses zero |
| **Lookback** | Half-life (adaptive) |
| **APR** | 11% |
| **Sharpe** | 1.6 |
| **Period** | 2007–2012 |
| **Clarity** | 8/10 |

Fundamentally motivated: both AUD and CAD are commodity currencies correlated to resource prices, so their exchange rates vs USD should be cointegrated. This is a structural economic relationship, not just a statistical artifact.

---

### Strategy 11: AUD/CAD Cross Rate with Rollover Interest

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Forex / Carry |
| **Markets** | Forex: AUD/CAD (cross rate) |
| **Timeframe** | Daily |
| **Entry** | Long AUD/CAD when Z < −1, Short when Z > +1 |
| **Exit** | Z-score crosses zero |
| **APR** | 6.2% |
| **Sharpe** | 0.54 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

Simpler execution (single instrument) but rollover/swap costs eat into profit. The two-leg version (Strategy 10, Sharpe 1.6) significantly outperforms. **Lesson:** always account for carry costs when comparing single-instrument vs multi-leg implementations.

---

### Strategy 12: Crude Oil (CL) Calendar Spread Mean Reversion

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Futures Calendar Spread |
| **Markets** | Futures: CL (Crude Oil) — near vs far month |
| **Timeframe** | Daily |
| **Entry** | Z-score of calendar spread exceeds threshold |
| **Exit** | Z-score crosses zero; roll before expiry |
| **APR** | 8.3% |
| **Sharpe** | 1.3 |
| **Period** | 2007–2012 |
| **Clarity** | 8/10 |

Calendar spreads are naturally mean-reverting because they reflect cost of carry (storage, interest, convenience yield). Margin requirements much lower than outright positions. Author's futures pricing model:

```
F(t,T) = S(t) * exp(gamma * (T - t))
# gamma = annualized roll return
# Positive gamma = backwardation = bullish
```

---

### Strategy 13: VIX Futures (VX) Calendar Spread Mean Reversion

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Volatility Calendar Spread |
| **Markets** | Futures: VX (VIX Futures) — near vs far month |
| **Timeframe** | Daily |
| **Entry (Long Spread)** | Abnormally low spread (steep contango) |
| **Entry (Short Spread)** | Abnormally high spread (flat/backwardation) |
| **Exit** | Spread reverts to mean; stop if VIX spikes |
| **APR** | 17.7% |
| **Sharpe** | 1.5 |
| **Period** | 2007–2012 |
| **Clarity** | 8/10 |

VIX term structure is in contango ~80% of the time, providing a structural edge. However, backwardation during crises (2008, 2011, 2020) can cause large losses. **Risk management is critical** — this is a risk premium, not a free lunch.

---

### Strategy 14: VX-ES Cross-Asset Mean Reversion

| Parameter | Value |
|-----------|-------|
| **Type** | Mean Reversion / Cross-Asset |
| **Markets** | Futures: VX (VIX), ES (S&P 500 E-mini) |
| **Timeframe** | Daily |
| **Entry** | When VIX spikes excessively vs ES drop: short VX, long ES |
| **Exit** | Spread reverts to mean |
| **APR** | 12.3% |
| **Sharpe** | 1.4 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

Exploits the well-known negative correlation between VIX and S&P 500. Profits from temporary dislocations in that relationship. Risk: correlation can break during extreme events.

---

### Skipped Mean Reversion Strategies

| # | Strategy | Clarity | Why Skipped |
|---|----------|---------|-------------|
| 7 | SPY vs Component Stocks Arbitrage | 6/10 | Index arb is HFT territory; edge eroded since 2008 |
| 9 | Intraday Cross-Sectional Mean Reversion | 6/10 | Requires tick data infrastructure; 73% APR / 4.7 Sharpe is pre-cost fantasy |

---

## Part II: Momentum Strategies (15–26)

### Strategy 15: Time Series Momentum — 2-Year Treasury (TU)

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Time Series / Trend Following |
| **Markets** | Futures: TU (2-Year Treasury Note) |
| **Timeframe** | Daily |
| **Lookback** | 250 days |
| **Holding Period** | 25 days |
| **Signal** | Binary: long if 250-day return > 0, short if < 0 |
| **APR** | 1.7% |
| **Sharpe** | 1.0 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

```
lookback_return = (price - price[250 days ago]) / price[250 days ago]

IF lookback_return > 0:
    GO LONG
ELSE:
    GO SHORT

REBALANCE every 25 days
```

Baseline time-series momentum example. The 250/25 (lookback/hold) is the standard academic parameterization. Low returns due to low volatility of short-duration treasuries, but very consistent.

---

### Strategy 16: Brazilian Real (BR) Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Time Series / EM FX |
| **Markets** | Futures: BR (Brazilian Real) |
| **Timeframe** | Daily |
| **Lookback** | 100 days |
| **Holding Period** | 10 days |
| **APR** | 17.7% |
| **Sharpe** | 1.09 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

Momentum works better on trending, volatile instruments. EM FX often trends due to carry trade flows and macro themes. Shorter lookback (100 vs 250) captures faster EM trends.

---

### Strategy 17: Copper (HG) Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Time Series / Commodity |
| **Markets** | Futures: HG (Copper) |
| **Timeframe** | Daily |
| **Lookback** | 40 days |
| **Holding Period** | 40 days |
| **APR** | 18% |
| **Sharpe** | 1.05 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

Symmetric 40/40 lookback/hold works better for commodities than the academic 250/25. **Key insight:** commodity trends are shorter-lived than financial asset trends due to supply-demand cycles.

---

### Strategy 18: Roll Return Signal for TU Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Roll Return / Carry |
| **Markets** | Futures: TU (2-Year Treasury Note) |
| **Timeframe** | Daily |
| **Signal** | gamma > 0 (backwardation): long; gamma < 0 (contango): short |
| **APR** | 2.5% |
| **Sharpe** | 2.1 |
| **Period** | 2007–2012 |
| **Clarity** | 9/10 |

```
gamma = (F_near - F_far) / F_near / (T_far - T_near)

IF gamma > 0:  # Backwardation = excess demand = bullish
    GO LONG
ELSE:           # Contango = oversupply = bearish
    GO SHORT
```

Very high Sharpe (2.1) for low APR — roll return is an exceptionally clean signal. **Key insight:** futures term structure encodes supply/demand information that spot price alone misses. Positive gamma (backwardation) = excess demand for near-term delivery = bullish.

---

### Strategy 19: XLE-USO Roll Return Arbitrage

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Roll Return / Cross-Asset |
| **Markets** | ETFs/Futures: XLE (Energy Sector), USO (Oil ETF), CL (Crude) |
| **Timeframe** | Daily |
| **Signal (Backwardation)** | Long XLE, Short USO |
| **Signal (Contango)** | Short XLE, Long USO |
| **Rebalance** | Monthly or at roll dates |
| **APR** | 16% |
| **Sharpe** | ~1.0 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

**Structural insight:** commodity ETFs like USO lose value in contango due to negative roll yield (buying expensive far contracts, selling cheap near contracts). Energy equities (XLE) don't suffer this drag. This creates a persistent, structural arbitrage opportunity.

---

### Strategy 20: VX-ES Roll Return Strategy

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Roll Return / Volatility |
| **Markets** | Futures: VX (VIX), ES (S&P 500 E-mini) |
| **Timeframe** | Daily |
| **Default Position** | Short VX, Long ES (harvest contango) |
| **Reversal** | When VX flips to backwardation: Long VX, Short ES |
| **APR** | 6.9% |
| **Sharpe** | 1.0 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

Harvests the VIX contango premium (short vol). Author emphasizes this is a **risk premium**, not a free lunch — you are compensated for bearing tail risk from VIX spikes. Must have stop loss for extreme vol events. Size conservatively using Kelly fraction.

---

### Strategy 21: Cross-Sectional Futures Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Cross-Sectional / Multi-Asset |
| **Markets** | 20–50 liquid futures (commodities, rates, FX, indices) |
| **Timeframe** | Monthly rebalance |
| **Entry (Long)** | Top quintile by trailing 12-month return |
| **Entry (Short)** | Bottom quintile by trailing 12-month return |
| **Weighting** | Equal weight, dollar-neutral |
| **APR** | 18% |
| **Sharpe** | 1.37 |
| **Period** | 1990–2007 |
| **Clarity** | 8/10 |

```
FOR each rebalance date (monthly):
    rank all futures by 12-month trailing return
    LONG = top 20% (strongest momentum)
    SHORT = bottom 20% (weakest momentum)
    equal_weight within each quintile
    dollar_neutral
```

Based on Moskowitz, Ooi, Pedersen (2012). **Warning:** pre-2008 results. Author notes significant performance degradation post-crisis. Strategy is correlated to equity momentum and suffered during risk-off events.

---

### Strategy 22: Cross-Sectional Stock Momentum (Jegadeesh-Titman)

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Cross-Sectional / Equity Long-Short |
| **Markets** | US Equities |
| **Timeframe** | Monthly rebalance |
| **Entry (Long)** | Top decile by 12-month return (skip most recent month) |
| **Entry (Short)** | Bottom decile |
| **Hold Period** | 1 month |
| **APR** | 37% |
| **Sharpe** | 4.1 |
| **Period** | 1990–2007 |
| **Clarity** | 8/10 |

The 12-1 formulation (skip most recent month) is standard to avoid short-term reversal contaminating the momentum signal. **Warning:** 37% APR / 4.1 Sharpe is pre-2008 and pre-transaction-costs. Post-2008 returns are materially lower. Strategy crashed in 2009 momentum reversal.

---

### Strategy 23: Euro Stoxx (FSTX) Opening Gap Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Gap Trading / Intraday |
| **Markets** | Futures: FSTX (Euro Stoxx 50) |
| **Timeframe** | Intraday (open to close) |
| **Entry** | Buy if gap > threshold, Sell if gap < −threshold |
| **Exit** | Close at end of day (MOC) |
| **APR** | 13% |
| **Sharpe** | 1.4 |
| **Period** | 2007–2012 |
| **Clarity** | 7/10 |

**Key insight:** Gaps in FSTX are **momentum** (continue through the day) while gaps in SPX are **mean-reverting**. This may be because FSTX opens after US overnight news is already priced in, creating genuine information-driven gaps rather than noise.

---

### Strategy 25: Post-Earnings Announcement Drift (PEAD)

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Event-Driven |
| **Markets** | US Equities |
| **Timeframe** | Daily (hold 1–60 days post-earnings) |
| **Entry** | Buy on positive SUE, Short on negative SUE |
| **Exit** | Hold 60 trading days or trailing stop |
| **APR** | 6.7% |
| **Sharpe** | 1.5 |
| **Period** | 2000–2012 |
| **Clarity** | 7/10 |

```
SUE = (actual_EPS - consensus_EPS) / historical_surprise_std

IF SUE > threshold:
    BUY on first trading day after announcement
IF SUE < -threshold:
    SHORT on first trading day after announcement

HOLD for 60 trading days (one quarter)
EXIT before next earnings announcement
```

One of the most robust anomalies in academic finance. Persists because: (1) institutions can't trade small-caps fast enough, (2) analyst estimates are anchored to priors, (3) behavioral underreaction to new information.

---

### Strategy 26: Leveraged ETF Rebalancing Momentum

| Parameter | Value |
|-----------|-------|
| **Type** | Momentum / Structural / ETF |
| **Markets** | Leveraged ETFs: DRN (3x Real Estate Bull), DRV (3x Bear) |
| **Timeframe** | Daily (near close, 15:45–16:00) |
| **Entry** | Trade in direction of predicted rebalancing flow |
| **Exit** | Market close or next day open |
| **APR** | 15% |
| **Sharpe** | 1.8 |
| **Period** | 2009–2012 |
| **Clarity** | 8/10 |

```
# Leveraged ETFs MUST rebalance daily to maintain target leverage
estimated_rebalance_volume = ETF_AUM * leverage * daily_return

IF underlying_index UP today:
    leveraged_bull_ETF must BUY more -> trade LONG near close
IF underlying_index DOWN today:
    leveraged_bull_ETF must SELL -> trade SHORT near close

ENTER at 15:45, EXIT at 16:00 or next open
```

**Structural edge:** leveraged ETFs mechanically buy high and sell low to maintain leverage ratios. This creates predictable end-of-day flows. Capacity limited by ETF AUM. Author notes the edge was well-known by 2013 and may have eroded.

---

### Skipped Momentum Strategies

| # | Strategy | Clarity | Why Skipped |
|---|----------|---------|-------------|
| 24 | GBPUSD Opening Gap Momentum | 6/10 | Sparse implementation details; threshold unspecified |

---

## Part III: Risk Management & Hybrid Frameworks (27–29)

### Strategy 27: Combined Mean Reversion + Momentum on Crude Oil (CL)

| Parameter | Value |
|-----------|-------|
| **Type** | Hybrid / Multi-Signal |
| **Markets** | Futures: CL (Crude Oil) |
| **Timeframe** | Daily |
| **APR** | 12% |
| **Sharpe** | 1.1 |
| **Period** | 2007–2012 |
| **Clarity** | 6/10 |

Combines calendar spread Z-score (mean reversion) and trailing return (momentum) on the same instrument. When both signals agree: full position. When they disagree: reduced or flat. More robust than either signal alone because different timeframes favor different approaches — short-term tends to mean-revert, long-term tends to trend. Exact combination weights are left flexible by the author.

---

### Strategy 28: Kelly Criterion Optimal Leverage

| Parameter | Value |
|-----------|-------|
| **Type** | Risk Management / Position Sizing Framework |
| **Markets** | Any |
| **Timeframe** | Any |
| **Clarity** | 9/10 |

Not a trading strategy — a **position sizing framework** applicable to any strategy.

#### Kelly Formulas

```
# Continuous returns (preferred for algo trading):
f = mean_excess_return / variance_of_returns
f = m / s²

# Discrete bets:
f = (p * b - q) / b
# p = win probability, q = loss probability, b = win/loss ratio

# IN PRACTICE: Use half-Kelly or less
f_practical = f / 2
```

#### Kelly Leverage Recommendations

| Fraction | Use Case | Risk |
|----------|----------|------|
| **Full Kelly** | Theoretical maximum geometric growth | Unacceptable drawdowns |
| **Half-Kelly (f/2)** | Recommended for most traders | ~75% of full Kelly growth, much less variance |
| **Quarter-Kelly (f/4)** | Very risk-averse | Smooth equity curve, lower returns |

**Author's strong recommendation:** Use half-Kelly or less because: (1) return distributions are not stationary, (2) fat tails increase ruin risk, (3) parameter estimation error means true Kelly is unknown. The continuous formula `f = m/s²` is elegant and easy to implement on a rolling basis.

---

### Strategy 29: CPPI (Constant Proportion Portfolio Insurance)

| Parameter | Value |
|-----------|-------|
| **Type** | Risk Management / Drawdown Control Framework |
| **Markets** | Any |
| **Timeframe** | Any |
| **Clarity** | 8/10 |

Systematic drawdown control overlay for any strategy.

```
floor = maximum_acceptable_loss  # e.g., 80% of initial capital
cushion = portfolio_value - floor
multiplier = desired_leverage_when_fully_invested  # e.g., 5

risky_allocation = min(multiplier * cushion, portfolio_value)

# As portfolio drops toward floor:
#   cushion shrinks -> allocation to risky assets decreases automatically
# If portfolio hits floor:
#   100% in risk-free asset (locked out)
```

Tradeoff: you give up upside in exchange for guaranteed drawdown protection. The "lock-out" effect (hitting the floor) can be mitigated by using a partial floor reset. Gap risk can breach the floor in extreme moves (flash crashes, limit-down events).

---

## Part IV: HFT Concepts (30–32) — Not Implementable

These are included in the book for conceptual understanding only. All require co-location, sub-millisecond infrastructure, and direct market access.

| # | Strategy | Clarity | Key Concept |
|---|----------|---------|-------------|
| 30 | HFT Market Making | 5/10 | Quote bid/ask around fair value, manage inventory, detect adverse selection |
| 31 | Momentum Ignition / Stop Hunting | 4/10 | Detect stop clusters at technical levels; regulatory concerns. Relevant for understanding WHY stops get hit |
| 32 | News Sentiment Momentum | 5/10 | NLP-based sentiment scoring. More relevant now (2026) with modern LLMs than when written |

---

## Cross-Cutting Themes

### Mean Reversion vs Momentum: It's About Timeframe

Most instruments exhibit **both** mean reversion and momentum at different timeframes:
- **Short-term** (intraday to days) → tends to mean-revert
- **Long-term** (weeks to months) → tends to trend

The key is matching strategy type to the appropriate timeframe.

### Stationarity Testing is Non-Negotiable

Before trading ANY mean-reversion strategy, test for stationarity using:

| Test | What It Tells You |
|------|-------------------|
| **ADF Test** | Reject null (p < 0.05) to confirm mean reversion |
| **Hurst Exponent** | H < 0.5 = mean reverting, H = 0.5 = random walk, H > 0.5 = trending |
| **Variance Ratio** | VR < 1 = mean reverting, VR = 1 = random walk, VR > 1 = trending |
| **Half-Life** | If > 100 days, the strategy is impractical |

### Cointegration Over Correlation

Correlation is **not sufficient** for pairs trading. Two assets can be highly correlated but NOT cointegrated — they can drift apart permanently. Cointegration means the spread is stationary and will revert. **Always use Johansen or CADF test**, not just correlation.

### Roll Return as Signal

Futures term structure (contango vs backwardation) is a powerful signal that spot price alone misses:
- **Backwardation** (positive gamma) = excess demand for near-term delivery = bullish
- **Contango** (negative gamma) = oversupply / storage costs = bearish

### Transaction Costs Destroy Paper Profits

Higher frequency = more costs. Author repeatedly demonstrates strategies with 40%+ APR that become marginal after realistic slippage and commissions. **Always include realistic costs in backtests.**

### Capacity vs Sharpe Tradeoff

| Frequency | Sharpe | Capacity |
|-----------|--------|----------|
| HFT (sub-second) | 3–5+ | < $10M |
| Intraday | 1.5–3 | $10–100M |
| Daily | 1.0–2.0 | $100M–1B |
| Weekly/Monthly | 0.5–1.5 | $1B+ |

**Retail traders should exploit the high-Sharpe, low-capacity niche** that institutions can't access.

### Regime Changes Break Strategies

Many strategies that worked pre-2008 failed post-2008. Causes:
1. **Crowded trades** (2007 quant crisis — everyone ran the same mean-reversion signal)
2. **Correlation breakdowns** during crises
3. **Structural market changes** (HFT, regulation, ETF growth)

Walk-forward testing is essential. Single-period backtests prove nothing.

### Kelly Criterion: Use Half or Less

Full Kelly maximizes geometric growth but assumes stationary, known distributions — **never true in practice**. Half-Kelly delivers ~75% of the growth rate with dramatically less drawdown risk. The formula `f = m/s²` is simple, powerful, and should be computed on a rolling basis.

---

## Key Concepts Reference

| Concept | Formula / Definition |
|---------|---------------------|
| **ADF Test** | Tests null hypothesis of unit root (non-stationarity). Reject at p < 0.05. |
| **Hurst Exponent** | H < 0.5: mean reverting, H = 0.5: random walk, H > 0.5: trending |
| **Half-Life** | `halflife = -log(2) / lambda` from OU regression `delta_y = lambda * y_lag + noise` |
| **Johansen Test** | Multi-leg cointegration test returning eigenvectors (hedge ratios) and eigenvalues |
| **Ornstein-Uhlenbeck** | `dX = theta * (mu - X) * dt + sigma * dW` — mean-reverting stochastic process |
| **Kalman Filter** | Recursive state estimation: dynamically estimates hedge ratio without fixed lookback |
| **Kelly Criterion** | `f = m / s²` (continuous) or `f = (p*b - q) / b` (discrete) |
| **Sharpe Ratio** | `(annual_return - risk_free_rate) / annual_std` — target > 1.0 viable, > 2.0 excellent |
| **Max Drawdown** | Largest peak-to-trough decline. Author considers > 25% unacceptable. |
| **Roll Return (gamma)** | `F(t,T) = S(t) * exp(gamma * (T-t))` — positive gamma = backwardation = bullish |

---

## Source

- **Book:** Algorithmic Trading: Winning Strategies and Their Rationale (2013) by Ernest P. Chan
- **Publisher:** John Wiley & Sons | **ISBN:** 978-1-118-46014-6 | **Pages:** 225
- **Key Chapters:** Ch. 2 (Price Mean Reversion), Ch. 3 (Stock/ETF Mean Reversion), Ch. 4 (Currency/Futures MR), Ch. 5 (Time Series Momentum), Ch. 6 (Cross-Sectional Momentum), Ch. 7 (Risk Management), Ch. 8 (HFT)
- **JSON Analysis:** `strategy_pipeline/output/book_analyses/ALGORITHMIC_TRADING_analysis.json`