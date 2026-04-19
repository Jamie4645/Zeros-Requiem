---
tags: [reference, infra]
aliases: [Deployment Options]
related: [[07-Guide-Python-Broker-APIs]], [[08-Guide-QuantConnect]], [[00-MOC-Zeros-Requiem]]
---

# Deployment Options & Platform Comparison

## Where Your Algorithm Currently Lives

Right now, Zeros Requiem is a **Python backtesting engine**. It can:
- Download historical price data from Yahoo Finance
- Run the algorithm over that data to simulate trades
- Show you the results (win rate, profit/loss, equity curve)

What it **cannot** do yet:
- Connect to live price data in real-time
- Place actual trades on an exchange or broker
- Run continuously without manual intervention
- Alert you when a signal appears

This page covers all the ways you can take this algorithm from "backtesting on your laptop" to "running live trades."

## The Four Main Deployment Paths

### Path 1: TradingView + Webhook Alerts (Easiest)

**Difficulty:** Beginner-friendly
**Cost:** TradingView subscription ($12.95-$49.95/month), some webhook services are free
**Best for:** Visual backtesting, semi-automated trading, learning

**How it works:**
1. Convert the Python algorithm into Pine Script (TradingView's built-in programming language)
2. Apply the script to any chart on TradingView
3. TradingView's strategy tester shows you backtest results with beautiful charts
4. Set up alerts that fire when the algorithm generates a signal
5. Connect alerts to your broker via a webhook bridge service

**What is Pine Script?**
Pine Script is TradingView's own programming language. It's simpler than Python and designed specifically for trading indicators and strategies. It runs directly on TradingView's servers, so you don't need to keep your computer on.

**What is a webhook?**
A webhook is like a notification that goes to a specific URL. When TradingView generates an alert, it can send a message to a webhook URL. Services like PineConnector or TradingConnector receive that message and translate it into a trade on your broker account.

**The full chain:**
```
TradingView Alert --> Webhook URL --> Bridge Service --> Broker API --> Trade Placed
```

**Pros:**
- Beautiful charts and visual feedback
- Easy to share strategies with others
- TradingView handles all the data and computation
- Works across commodities, forex, and crypto (depending on your TradingView plan)
- You can see every trade on the chart

**Cons:**
- Semi-automated (there's a slight delay between alert and execution)
- Pine Script has some limitations compared to Python (no complex data structures, limited loops)
- The webhook bridge adds a point of failure
- Monthly subscription cost
- Some advanced features require paid TradingView plans

**Webhook bridge services for each market:**

| Service | Market | What It Does |
|---|---|---|
| PineConnector | Forex (MT4/MT5) | Receives TradingView alerts and places trades on MetaTrader |
| TradingConnector | Forex (MT4/MT5) | Similar to PineConnector, runs locally on your PC |
| Alertatron | Crypto | Connects TradingView to Binance, Bybit, etc. |
| 3Commas | Crypto | Bot platform that can execute TradingView alerts |
| Cornix | Crypto (Telegram) | Executes signals from Telegram channels on exchanges |

### Path 2: Python + Broker APIs (Most Flexible)

**Difficulty:** Intermediate (requires coding)
**Cost:** Free (aside from broker commissions)
**Best for:** Full automation, custom logic, running across multiple markets

**How it works:**
1. Keep your existing Python codebase
2. Replace Yahoo Finance data with live data feeds from your broker
3. Add execution logic to place trades via the broker's API
4. Run the script on a VPS (Virtual Private Server) so it's always on

**What is an API?**
An API (Application Programming Interface) is a way for your code to talk to a broker's systems. Instead of clicking "Buy" on a website, your code sends a message like "Buy 1 contract of Gold at market price" and the broker executes it.

**What is a VPS?**
A VPS is a computer in the cloud that's always on, always connected to the internet. You rent it for $5-20/month from providers like DigitalOcean, AWS, or Vultr. Your algorithm runs on this server 24/7 without needing your personal computer.

**Broker APIs for each market:**

| Market | Broker/API | Language | Notes |
|---|---|---|---|
| Crypto | ccxt (library) | Python | Connects to 100+ exchanges (Binance, Bybit, Coinbase, Kraken, etc.) |
| Crypto | Binance API | Python | Direct API for the world's largest crypto exchange |
| Forex | OANDA API | Python | Popular retail forex broker with excellent API |
| Forex | Interactive Brokers TWS | Python | Professional-grade, supports forex, stocks, futures, options |
| Commodities | Interactive Brokers TWS | Python | The go-to for futures trading via API |
| Commodities | Alpaca | Python | Commission-free, good API, supports futures |
| All Markets | Interactive Brokers | Python | Single broker for all three markets |

**The full chain:**
```
Your Python Script (on VPS) --> Broker API --> Exchange --> Trade Placed
         |
         +--> Live Data Feed (WebSocket) --> Your Strategy Logic --> Signal
```

**Pros:**
- Full control over every aspect of the algorithm
- Fastest execution (no middleman)
- One codebase for all markets
- Can add any feature you want (machine learning, sentiment analysis, etc.)
- No monthly subscription (just VPS cost)

**Cons:**
- Most development work required
- You must handle errors, disconnections, and edge cases yourself
- Need to build your own monitoring and alerting
- No visual interface unless you build one
- Bugs in your code can cost real money

**Key Python libraries you'd use:**

| Library | Purpose |
|---|---|
| `ccxt` | Connect to crypto exchanges (Binance, Bybit, etc.) |
| `ib_insync` | Connect to Interactive Brokers |
| `oandapyV20` | Connect to OANDA (forex) |
| `websocket-client` | Receive live price data in real-time |
| `schedule` or `APScheduler` | Run your strategy at specific intervals |
| `logging` | Record everything your algorithm does |
| `telegram-bot` or `discord.py` | Send yourself alerts when trades are placed |

### Path 3: QuantConnect / Lean Engine (Best All-in-One)

**Difficulty:** Intermediate (their framework has a learning curve)
**Cost:** Free for backtesting, paid for live trading ($8-$20/month)
**Best for:** Professional-grade backtesting with institutional data, all three markets

**How it works:**
1. Port your strategy to QuantConnect's framework (uses Python or C#)
2. Backtest with their institutional-quality historical data (much better than Yahoo Finance)
3. Deploy live through their connected brokers
4. Everything runs in the cloud -- no VPS needed

**What is QuantConnect?**
QuantConnect is a free, cloud-based algorithmic trading platform. Think of it as a professional-grade version of what you've built, with:
- 20+ years of tick-level data for stocks, forex, futures, and crypto
- Built-in risk management and position sizing
- Paper trading mode for testing with fake money
- Live trading connections to real brokers

**What markets does it support?**

| Market | Data Available | Live Trading Via |
|---|---|---|
| Crypto | Yes (multiple exchanges) | Binance, Coinbase, Bybit |
| Forex | Yes (tick-level) | OANDA, Interactive Brokers |
| Commodities/Futures | Yes (CME data) | Interactive Brokers |
| Stocks | Yes (US, international) | Interactive Brokers, Alpaca |

**Pros:**
- Free backtesting with institutional-quality data
- Handles all infrastructure (data feeds, execution, error handling)
- Supports all three markets in one platform
- Built-in walk-forward analysis and optimisation
- Active community and documentation
- Cloud-based -- nothing to install

**Cons:**
- Learning curve for their API framework (they have specific patterns you must follow)
- Less flexibility than pure Python (you work within their framework)
- Live trading requires a paid plan
- Some broker limitations depending on your region
- Less visual than TradingView

### Path 4: Platform-Native Languages (Industry Standard)

**Difficulty:** Intermediate to Advanced
**Cost:** Platform-dependent (many are free)
**Best for:** Getting the absolute best performance in a specific market

Each market has a "native" platform that most traders use. Converting your algorithm to that platform's language gives you the tightest integration and best execution.

**Forex: MetaTrader 5 (MT5) with MQL5**

MetaTrader is the dominant retail forex platform. Over 80% of retail forex brokers support it.

| Feature | Details |
|---|---|
| Language | MQL5 (C-like syntax) |
| Built-in Backtester | Yes, with tick-level simulation |
| Live Trading | Yes, through any MT5 broker |
| Optimisation | Built-in genetic algorithm optimiser |
| Cost | Free (MT5 is free to download) |
| VPS | MT5 has built-in VPS hosting through MQL5.com |

**Commodities/Futures: NinjaTrader with NinjaScript**

NinjaTrader is the dominant platform for futures trading (Gold, Oil, etc.).

| Feature | Details |
|---|---|
| Language | NinjaScript (C#-based) |
| Built-in Backtester | Yes, very detailed |
| Live Trading | Yes, through NinjaTrader Brokerage or connected brokers |
| Market Replay | Can replay historical data tick-by-tick |
| Cost | Free for charting, $99/month or $1,499 lifetime for live trading |

**Crypto: Freqtrade (Open Source)**

Freqtrade is the most popular open-source crypto trading bot. It's written in Python, so your code converts more easily.

| Feature | Details |
|---|---|
| Language | Python |
| Built-in Backtester | Yes, with detailed reporting |
| Live Trading | Yes, via ccxt to any exchange |
| Optimisation | Built-in hyperparameter optimisation (Hyperopt) |
| Cost | Free and open source |
| Deployment | Docker container (easy to deploy on VPS) |

## Quick Comparison Table

| Feature | TradingView | Python + APIs | QuantConnect | Native Platform |
|---|---|---|---|---|
| Ease of Setup | Easy | Hard | Medium | Medium |
| Visual Feedback | Excellent | None (build your own) | Basic | Good |
| Execution Speed | Slow (webhook delay) | Fast | Fast | Fastest |
| Flexibility | Limited (Pine Script) | Unlimited | High | Medium |
| Cost | $13-50/month | $5-20/month (VPS) | $8-20/month | Varies |
| All 3 Markets | Yes | Yes | Yes | No (one per platform) |
| Best For | Beginners, visual analysis | Full control, custom features | Professional backtesting | Deep integration |
