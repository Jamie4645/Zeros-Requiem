# Zero's Requiem

**Systematic Algo Trading** — Breakout-retest strategies for Gold and Forex Indices, built on 3-4 years of profitable discretionary trading.

Python 3.10+ | OANDA (Live) | IBKR (Data)

---

## What This Is

Zero's Requiem codifies a proven discretionary edge into a fully automated trading system. The core strategy — **SBRS (Sovereign Breakout Retest Strategy)** — detects structure breaks, waits for price to retest the broken level, and enters with moving average confirmation.

This is **not** AI-generated alpha or parameter-optimized curve fitting. Every parameter comes from real trading experience.

---

## Strategy: SBRS 1.1

**Edge:** Breakout + Retest + MA Confirmation

**Entry (all 5 must pass):**
1. **Trend Context** — Price above/below WMA(9) on 4H, with recent WMA/SMMA cross
2. **Structure Break** — Price closes beyond a swing high/low (20-bar lookback)
3. **Retest** — Price returns to within 0.5 ATR of the broken level
4. **MA Cross** — WMA(9) crossed SMMA(7) within last 10 bars on candle close
5. **Filters** — Not choppy, not against 4H trend, not 16-20 GMT, R:R >= 3.0

**Exit (first triggered):**
- Take Profit (3R) | Stop Loss | Breakeven at 1.5R | MA reversal | Structure break against | 40-bar max hold

**Risk:** 1% per trade, ATR-based position sizing

---

## Current Status

| Asset | Status | Data Source | Validation |
|-------|--------|-------------|------------|
| **Gold 1H** | Live on OANDA | OANDA (20Y) | 10Y walk-forward, 75% consistency, 1,152 trades |
| **S&P 500 1H** | Pending | IBKR (10Y) | Walk-forward pending |
| **NASDAQ 1H** | Pending | IBKR (10Y) | Walk-forward pending |
| **DAX 1H** | Pending | IBKR (10Y) | Walk-forward pending |

**Crypto:** Tested and rejected — no consistent edge with breakout-retest logic.

---

## Usage

```bash
# Backtest Gold
py main.py --symbol GC=F --interval 1h --period 10y

# Walk-forward validation (8 sequential windows)
py main.py --walk-forward GC=F --interval 1h --windows 8

# Backtest an index (requires IBKR Gateway or cached data)
py main.py --symbol ^GSPC --interval 1h --period 10y

# Run tests
py -m pytest tests/ -v --tb=short

# Test IBKR connection
py -m src.data.ibkr_fetcher
```

---

## Project Structure

```
main.py                         # CLI entry point
src/
  core/
    engine.py                   # Backtest engine
    risk_manager.py             # 5-layer risk management
    walk_forward.py             # Walk-forward validation
    monte_carlo.py              # Monte Carlo simulation
  regimes/
    sbrs_gold.py                # SBRS strategy implementation
  indicators/
    technical.py                # WMA, SMMA, ATR, swing detection
  execution/
    entries.py                  # Trade setup classes
  data/
    fetcher.py                  # Data routing (OANDA → IBKR → Yahoo)
    oanda_fetcher.py            # OANDA historical data (Gold, Forex)
    ibkr_fetcher.py             # IBKR historical data (Indices)
    migrate_to_sqlite.py        # JSON → SQLite migration
  live/
    runner.py                   # Hourly live trading loop
    oanda_executor.py           # OANDA order execution
    state.py                    # Trade state management + SQLite
    alerts.py                   # Trade notifications
  visualization/
    charts.py                   # Equity curves, trade maps, heatmaps
tests/                          # Pytest suite + manual analysis scripts
knowledge-base/                 # Obsidian vault (development docs)
state/                          # Live trading state (JSON)
data/                           # SQLite DB + IBKR cache
```

---

## Data Sources

| Source | Instruments | History | Purpose |
|--------|------------|---------|---------|
| **OANDA** | Gold, Forex | 20+ years | Live trading + historical data |
| **IBKR** | S&P 500, NASDAQ, DAX | 10+ years | Index walk-forward validation |
| **Yahoo Finance** | All | 1-2Y intraday | Fallback only |

---

## Validation Standards

Every strategy must pass before live deployment:

- 500+ trades over 10+ years of data
- Walk-forward: 8 windows, 75%+ profitable
- Slippage modeled at 1.5 pips
- Monte Carlo: <5% probability of 20% drawdown

**Red flags (stop and investigate):** Win rate >70%, Sharpe >3.0, Profit Factor >3.0

---

## The 5 Fundamental Truths (Mark Douglas)

1. Anything can happen.
2. You don't need to know what is going to happen next to make money.
3. There is a random distribution between wins and losses for any given set of variables that define an edge.
4. An edge is nothing more than an indication of a higher probability of one thing happening over another.
5. Every moment in the market is unique.
