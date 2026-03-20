---
tags: [guide, platform, QuantConnect]
aliases: [QuantConnect Guide]
related: [[05-Deployment-Options-Platform-Comparison]], [[07-Guide-Python-Broker-APIs]], [[00-MOC-Zeros-Requiem]]
---

# Guide: QuantConnect

## What Is QuantConnect?

QuantConnect is a free, cloud-based algorithmic trading platform. It provides everything you need to research, backtest, and deploy trading algorithms -- all from your web browser.

Think of it as a professional-grade version of what you've built with Zeros Requiem, but with:
- Institutional-quality data (much better than Yahoo Finance)
- Built-in execution infrastructure
- Cloud computing (no need for your own server for backtesting)
- Support for stocks, forex, futures (commodities), crypto, and options

## Why Consider QuantConnect?

### The Data Problem

Your current algorithm uses Yahoo Finance for data. While this works for basic backtesting, it has significant limitations:

| Issue | Yahoo Finance | QuantConnect |
|---|---|---|
| Data quality | Occasional gaps, adjusted data can be wrong | Institutional-grade, cleaned and verified |
| Intraday data | Limited to last 60 days for some intervals | Full history, tick-level data going back 20+ years |
| Forex volume | Unreliable (not a forex data provider) | Actual forex volume from multiple providers |
| Futures data | Basic daily/hourly | Tick data, continuous contracts, roll management |
| Crypto data | Basic OHLCV | Order book data, multiple exchanges |
| Cost | Free but unreliable | Free for backtesting |

### The Infrastructure Problem

With Python + Broker APIs, you need to build and maintain:
- Data feed connections
- Order management
- Error handling and retry logic
- Position tracking
- Risk management
- Logging and monitoring

QuantConnect handles ALL of this for you. You focus on the strategy logic, they handle everything else.

## How QuantConnect Works

### The Framework

QuantConnect uses a framework called "Lean" (which is open source). Your algorithm follows a specific structure:

```python
class ZerosRequiemAlgorithm(QCAlgorithm):
    
    def Initialize(self):
        # Set up your algorithm
        self.SetStartDate(2024, 1, 1)
        self.SetEndDate(2025, 1, 1)
        self.SetCash(10000)
        
        # Add the assets you want to trade
        self.gold = self.AddFuture(Futures.Metals.Gold)
        self.eurusd = self.AddForex("EURUSD")
        self.btc = self.AddCrypto("BTCUSD")
    
    def OnData(self, data):
        # This runs every time new data arrives
        # Put your strategy logic here
        pass
```

**Key concepts:**
- `Initialize()`: Runs once when the algorithm starts. Set your dates, capital, and assets here.
- `OnData()`: Runs every time a new candle/tick arrives. This is where your strategy logic goes.
- `self.AddFuture()`, `self.AddForex()`, `self.AddCrypto()`: Tell QuantConnect which assets you want to trade.

### Converting Your Strategy

Your Zeros Requiem strategies would map like this:

**Structure Reversal:**
```python
def OnData(self, data):
    # Get price data as a pandas DataFrame (familiar!)
    history = self.History(self.gold.Symbol, 100, Resolution.Hour)
    
    # Your swing point detection works the same way
    swing_highs = self.detect_swing_highs(history)
    swing_lows = self.detect_swing_lows(history)
    
    # Place orders using QuantConnect's built-in functions
    if retest_signal == "long":
        self.SetHoldings(self.gold.Symbol, 0.02)  # Risk 2% of portfolio
        self.StopMarketOrder(self.gold.Symbol, -quantity, stop_price)
        self.LimitOrder(self.gold.Symbol, -quantity, take_profit_price)
```

**Key differences from your current code:**
1. Data arrives automatically (no need to call `yfinance`)
2. Orders use QuantConnect's built-in methods
3. Position sizing can use `SetHoldings()` for percentage-based allocation
4. Stop losses and take profits are placed as separate orders

### Supported Markets

| Market | Asset Class | Data Resolution | Live Trading Broker |
|---|---|---|---|
| Gold, Silver, Oil | Futures | Tick, Second, Minute, Hour, Daily | Interactive Brokers |
| EUR/USD, GBP/USD | Forex | Tick, Second, Minute, Hour, Daily | OANDA, Interactive Brokers |
| BTC, ETH, SOL | Crypto | Tick, Second, Minute, Hour, Daily | Binance, Coinbase, Bybit |
| AAPL, SPY, etc. | Equities | Tick, Second, Minute, Hour, Daily | Interactive Brokers, Alpaca |

## Getting Started with QuantConnect

### Step 1: Create a Free Account
1. Go to quantconnect.com
2. Sign up (free)
3. You get access to the Algorithm Lab (cloud IDE) and all historical data

### Step 2: Explore the Algorithm Lab
The Algorithm Lab is a web-based code editor where you write, backtest, and deploy algorithms. It looks similar to VS Code but runs in your browser.

### Step 3: Start with a Template
QuantConnect has hundreds of example algorithms. Start by modifying one that's close to what you want:
- Search for "breakout" or "swing trading" in their documentation
- Copy the template and replace the strategy logic with yours

### Step 4: Backtest
Click "Backtest" and QuantConnect runs your algorithm against historical data. Results include:
- Sharpe Ratio (risk-adjusted return)
- Total return and drawdown
- Trade list with entry/exit details
- Interactive equity curve chart

### Step 5: Paper Trade
When you're happy with backtest results:
1. Connect a broker account (Interactive Brokers, OANDA, etc.)
2. Deploy to paper trading
3. The algorithm runs in the cloud using live data but fake money

### Step 6: Go Live
When paper trading results match your backtest:
1. Switch from paper to live mode
2. Set risk limits (max position size, max drawdown, etc.)
3. Monitor via the dashboard and mobile app

## QuantConnect Pricing

| Plan | Cost | What You Get |
|---|---|---|
| Free | $0 | Backtesting, 1 live algorithm, community data |
| Research | $8/month | Jupyter notebooks, more compute time |
| Team | $20/month | Multiple live algorithms, priority support |
| Institution | Custom | Enterprise features |

The free plan is enough to get started and run your first live algorithm.

## Pros and Cons Summary

**Pros:**
- Free backtesting with institutional-quality data
- Handles all infrastructure (data, execution, monitoring)
- Supports all three markets you care about (commodities, forex, crypto)
- Python-based, so your existing knowledge transfers
- Active community with thousands of example algorithms
- Built-in walk-forward analysis and parameter optimisation

**Cons:**
- Learning curve for their specific framework and API
- Less flexibility than pure Python (you work within their patterns)
- Live trading requires a connected broker account
- Cloud-based means you depend on their servers being up
- Some advanced features require paid plans
- Community discussion can expose your strategy ideas

## Resources

- **Documentation**: quantconnect.com/docs
- **Tutorials**: quantconnect.com/learning
- **Example Algorithms**: quantconnect.com/terminal (search the community)
- **Lean Engine (open source)**: github.com/QuantConnect/Lean
- **Discord**: Active community for questions and discussion
