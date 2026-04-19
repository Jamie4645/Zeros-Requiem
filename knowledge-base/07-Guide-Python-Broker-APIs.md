---
tags: [reference, infra, broker]
aliases: [Broker API Guide]
related: [[05-Deployment-Options-Platform-Comparison]], [[08-Guide-QuantConnect]], [[29-P5-P7-P8-OANDA-Portfolio]], [[00-MOC-Zeros-Requiem]]
---

# Guide: Python + Broker APIs

## What This Approach Means

Instead of converting your algorithm to another language, you keep it in Python and connect it directly to a broker's systems. Your Python script:
1. Receives live price data from the broker
2. Runs your strategy logic on each new candle
3. Sends buy/sell orders to the broker via their API
4. Manages open positions (trailing stops, take profits)

This is the most flexible approach and what most professional quant traders use.

## Architecture Overview

A production-ready algo trading system has several components:

```
+-----------------+     +------------------+     +----------------+
|  Data Feed      | --> |  Strategy Engine  | --> |  Order Manager |
|  (Live Prices)  |     |  (Your Algorithm) |     |  (API Calls)   |
+-----------------+     +------------------+     +----------------+
        |                       |                        |
        v                       v                        v
+-----------------+     +------------------+     +----------------+
|  Data Storage   |     |  Risk Manager    |     |  Broker/       |
|  (Database)     |     |  (Position Size) |     |  Exchange      |
+-----------------+     +------------------+     +----------------+
        |                       |                        |
        +----------+------------+------------------------+
                   |
                   v
         +------------------+
         |  Monitoring &    |
         |  Alerting        |
         |  (Telegram/Email)|
         +------------------+
```

## Broker-by-Broker Setup Guide

### For Crypto: ccxt Library

**What is ccxt?**
ccxt (CryptoCurrency eXchange Trading) is a Python library that provides a unified API for over 100 cryptocurrency exchanges. Write your code once and it works on Binance, Bybit, Coinbase, Kraken, and many more.

**Installation:**
```
pip install ccxt
```

**Basic usage example:**
```python
import ccxt

# Connect to Binance
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET_KEY',
})

# Get live price data
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '4h', limit=100)

# Place a market buy order
order = exchange.create_market_buy_order('BTC/USDT', amount=0.001)

# Place a limit order with stop loss
order = exchange.create_order(
    symbol='BTC/USDT',
    type='stop_loss_limit',
    side='sell',
    amount=0.001,
    price=29000,
    params={'stopPrice': 29100}
)
```

**Getting API keys:**
1. Create an account on your chosen exchange (e.g., Binance)
2. Go to API Management in your account settings
3. Create a new API key
4. Enable "Spot Trading" permissions (do NOT enable withdrawal permissions)
5. Save the API key and secret securely

**Important security rules:**
- NEVER share your API keys
- NEVER enable withdrawal permissions on your trading API key
- Use IP whitelisting (only your VPS IP can use the key)
- Start with testnet/sandbox mode before going live

### For Forex: OANDA API

**What is OANDA?**
OANDA is a well-known forex broker with one of the best APIs for retail traders. They offer a practice (demo) account where you can test with fake money.

**Installation:**
```
pip install oandapyV20
```

**Getting started:**
1. Create an OANDA account at oanda.com
2. Go to "Manage API Access" in your account settings
3. Generate a personal access token
4. Note your account ID

**Basic usage example:**
```python
import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.orders as orders

# Connect to OANDA (practice account)
client = API(access_token="YOUR_TOKEN", environment="practice")

# Get live price data
params = {"granularity": "H4", "count": 100}
r = instruments.InstrumentsCandles(instrument="EUR_USD", params=params)
client.request(r)
candles = r.response['candles']

# Place a market order
order_data = {
    "order": {
        "type": "MARKET",
        "instrument": "EUR_USD",
        "units": "1000",  # 1000 units = 0.01 lot
        "stopLossOnFill": {"price": "1.0800"},
        "takeProfitOnFill": {"price": "1.1000"}
    }
}
r = orders.OrderCreate(accountID="YOUR_ACCOUNT_ID", data=order_data)
client.request(r)
```

### For Commodities/All Markets: Interactive Brokers

**What is Interactive Brokers (IBKR)?**
Interactive Brokers is a professional brokerage that offers access to virtually every market in the world -- stocks, forex, futures (commodities), options, and even crypto. It's the go-to choice if you want one broker for everything.

**Installation:**
```
pip install ib_insync
```

**Requirements:**
1. An Interactive Brokers account (minimum deposit varies by account type)
2. TWS (Trader Workstation) or IB Gateway running on your computer/VPS
3. API connections enabled in TWS settings

**Basic usage example:**
```python
from ib_insync import *

# Connect to TWS
ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

# Define Gold Futures contract
gold = Future('GC', exchange='COMEX')

# Get historical data
bars = ib.reqHistoricalData(
    gold,
    endDateTime='',
    durationStr='1 Y',
    barSizeSetting='4 hours',
    whatToShow='TRADES',
    useRTH=False
)

# Place a market order
order = MarketOrder('BUY', 1)  # 1 contract
trade = ib.placeOrder(gold, order)

# Place a bracket order (entry + stop loss + take profit)
bracket = ib.bracketOrder(
    'BUY', 
    1,           # 1 contract
    limitPrice=2650,   # Entry
    takeProfitPrice=2700,  # Take profit
    stopLossPrice=2620     # Stop loss
)
for o in bracket:
    ib.placeOrder(gold, o)

ib.disconnect()
```

## Running Your Algorithm 24/7 on a VPS

### What is a VPS?

A VPS (Virtual Private Server) is a computer in the cloud that runs 24/7. You rent it for a monthly fee, and it's always on, always connected to the internet, with a fixed IP address.

### Why do you need one?

- Your algo needs to run continuously to catch signals
- Forex and crypto markets run 24/7 (or close to it)
- If your home internet goes down, your algo keeps running
- You can IP-whitelist your API keys to the VPS IP

### Recommended VPS Providers

| Provider | Cheapest Plan | Best For |
|---|---|---|
| DigitalOcean | $6/month (1GB RAM) | Beginners, good documentation |
| Vultr | $5/month (1GB RAM) | Low-latency locations worldwide |
| AWS EC2 | Free tier (1 year) | If you want to learn cloud computing |
| Hetzner | $4/month (2GB RAM) | Best value for money (EU-based) |

**Recommended specs for running Zeros Requiem:**
- 2GB RAM
- 1 vCPU
- 25GB storage
- Ubuntu 22.04 (Linux)

### Essential Components for Production

Beyond just running the algorithm, a production system needs:

**1. Logging** -- Record every decision the algorithm makes
```python
import logging
logging.basicConfig(filename='trading.log', level=logging.INFO)
logging.info(f"Signal detected: BUY GC=F at $2650")
```

**2. Alerting** -- Send yourself notifications
```python
# Telegram bot for trade notifications
import requests
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})
```

**3. Error Handling** -- What happens when the API is down?
```python
import time
def place_order_with_retry(order, max_retries=3):
    for attempt in range(max_retries):
        try:
            return broker.place_order(order)
        except ConnectionError:
            time.sleep(5 * (attempt + 1))  # Wait longer each retry
    send_telegram("ALERT: Order failed after 3 attempts!")
```

**4. Paper Trading First** -- Always test with fake money before going live
- Most brokers offer demo/practice accounts
- Run your algo on the demo for at least 1-3 months
- Compare live results to backtest results
- Only go live when you're confident in the system
