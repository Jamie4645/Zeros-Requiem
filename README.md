# Zero's Requiem - SCAF 2.0

**Sovereign Cross-Asset Framework** -- A regime-aware algorithmic trading system for Gold, Forex, and Crypto.

Version 4.1.0 | Python 3.10+

---

## Architecture

SCAF 2.0 uses a three-layer execution protocol across three distinct market regimes:

**Execution Layers:**
1. **Liquidity Sweep** -- Detect when price pokes beyond key levels (PDH/PDL, weekly H/L, swing H/L, Asian range)
2. **Displacement Factor (Df)** -- Confirm institutional participation via candle body Z-score
3. **Fair Value Gap (FVG)** -- Enter at the imbalance zone left by the displacement candle

**Regimes:**
- **Gold** -- Asia Mean Reversion (Bollinger Band fades) + NY/Daily Momentum (sweep + displacement)
- **Forex** -- Killzone Strategy (London/NY session, Asian range trap). JPY pairs use breakout logic.
- **Crypto** -- Volatility Compression (VR < 0.8 coiled spring) + Trend Momentum (EMA cross + sweep)

## Supported Symbols

| Asset Class | Symbols |
|-------------|---------|
| Gold | GC=F |
| Forex | EURUSD=X, GBPUSD=X, USDJPY=X |
| Crypto | BTC-USD, ETH-USD |

## Usage

```bash
# Single symbol
py main.py --symbol GC=F --interval 4h --period 1y

# All symbols in a regime
py main.py --multi forex --interval 4h --period 1y

# Full portfolio (all 6 symbols)
py main.py --all --interval 4h --period 1y

# Walk-forward analysis (max available data)
py main.py --walk-forward GC=F --interval 1d --windows 8
```

## Performance (Latest Backtest)

**4H / 1 Year -- 155 trades, +$3,426 combined**
| Symbol | Trades | WR | PnL | Sharpe | PF |
|--------|--------|-----|-----|--------|-----|
| Gold | 73 | 42% | +$2,428 | 1.47 | 1.67 |
| GBP/USD | 26 | 50% | +$747 | 0.72 | 1.55 |
| ETH | 8 | 63% | +$492 | 0.61 | 2.31 |

**Walk-Forward Validated: Gold Daily -- 88% consistency over 5 years (7/8 windows profitable)**

## Risk Management

5-layer system:
1. Daily loss limit (3%)
2. Drawdown circuit breaker (10%)
3. Max concurrent risk (6-8%, timeframe-adaptive)
4. Direction concentration limits
5. Volatility-adjusted position sizing: `(Equity * 1%) / (ATR(14) * 2)`

Breakeven stop at 1.5R profit (forex/crypto only -- Gold momentum lets winners run).

## Project Structure

```
main.py                     # CLI entry point
src/
  core/
    engine.py               # Backtest engine + elite metrics
    risk_manager.py         # 5-layer risk management
    walk_forward.py         # Walk-forward testing framework
  data/
    fetcher.py              # Yahoo Finance data + symbol registry
  execution/
    liquidity.py            # Sweep detection (multi-bar, swing/weekly levels)
    displacement.py         # FVG detection (with near-FVG tolerance)
    entries.py              # Three-layer entry validation
  indicators/
    technical.py            # ATR, EMA, SMA, BB, RSI, Df, VR, sessions
    candlestick.py          # Engulfing, pin bar, expansion candle
  regimes/
    gold.py                 # Gold regime (Asia MR + NY/Daily momentum)
    forex.py                # Forex regime (killzone + JPY breakout)
    crypto.py               # Crypto regime (compression + trend momentum)
knowledge-base/             # Development documentation
```

## The 5 Fundamental Truths (Mark Douglas)

1. Anything can happen.
2. You don't need to know what is going to happen next to make money.
3. There is a random distribution between wins and losses for any given set of variables that define an edge.
4. An edge is nothing more than an indication of a higher probability of one thing happening over another.
5. Every moment in the market is unique.
