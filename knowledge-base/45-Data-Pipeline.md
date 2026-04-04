---
tags: [data, oanda, ibkr, yahoo, pipeline]
aliases: [Data Pipeline, Data Sources]
---

# Data Pipeline — Triple Source Routing

> How SBRS gets historical and live data: OANDA → IBKR → Yahoo Finance.

---

## Routing Priority

```
fetch(symbol, interval, period)
    │
    ├─ Gold/Forex? ──→ OANDA (20Y+ history, back to 2005)
    │                    └─ fails? → Yahoo fallback
    │
    ├─ Indices?    ──→ IBKR (10Y+ intraday data)
    │                    └─ fails? → Yahoo fallback
    │
    └─ Anything    ──→ Yahoo Finance (1-2Y intraday)
```

---

## Data Sources

| Source | Instruments | History | API |
|--------|------------|---------|-----|
| **OANDA** | Gold (XAUUSD) | 2005–present | v20 REST API (practice account) |
| **IBKR** | S&P 500, NASDAQ, DAX | 10Y+ intraday | `ib_insync` via TWS/IB Gateway |
| **Yahoo Finance** | All | 1-2Y intraday, 5Y+ daily | `yfinance` |

---

## OANDA Configuration

- API endpoint: `api-fxpractice.oanda.com` (practice/demo)
- Credentials: `OANDA_API_KEY` and `OANDA_ACCOUNT_ID` in `.env`
- Pagination: Auto-paginated, fetches 5000 candles per request
- Instruments: `XAU_USD` (Gold)
- File: `src/data/oanda_fetcher.py`

---

## IBKR Configuration

- Connection: `127.0.0.1:7497` (paper trading port)
- Requires: TWS or IB Gateway running with API enabled
- Client IDs: `10` (data fetches), `99` (availability check)
- Symbol mapping: `^GSPC` → SPX (CBOE), `^IXIC` → COMP (NASDAQ), `^GDAXI` → DAX (EUREX)
- Pagination: Auto-paginated in 30-day chunks (max 200 requests)
- CSV cache: `data/cache/{symbol}_{interval}.csv` (used if < 7 days old)
- File: `src/data/ibkr_fetcher.py`

---

## Supported Symbols

| Symbol | Name | Primary Source |
|--------|------|---------------|
| `GC=F` | Gold (XAUUSD) | OANDA |
| `^GSPC` | S&P 500 | IBKR |
| `^IXIC` | NASDAQ | IBKR |
| `^GDAXI` | DAX | IBKR |

---

## Status

- **OANDA**: Active, 20Y Gold data validated
- **IBKR**: Code written, IB Gateway installed and configured (Phase 2). Awaiting first data download.
- **Yahoo**: Fallback only — 1-2Y intraday limitation makes it unsuitable for walk-forward

---

## Related

- [[39-Phase-2-IBKR-Index-Data]] — IBKR fetcher implementation
- [[29-P5-P7-P8-OANDA-Portfolio]] — OANDA integration history
- [[00-MOC-Zeros-Requiem]]
