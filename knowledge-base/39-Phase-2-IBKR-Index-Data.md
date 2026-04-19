---
tags: [infra, expansion, indices]
aliases: [Phase 2, IBKR Data, Index Data]
---

# Phase 2 — IBKR Historical Data Fetcher

> Unlocks the biggest validation gap: 10Y walk-forward on indices. Yahoo Finance only provides 1-2Y of intraday data for S&P 500, NASDAQ, DAX.

---

## Data Source Priority

```
Gold/Forex  → OANDA (20+ years, free practice account)
Indices     → IBKR (10+ years, free paper account) → Yahoo (fallback)
Crypto      → Yahoo Finance (only source)
```

## Prerequisites (User Must Do)

1. Create IBKR paper trading account at interactivebrokers.com
2. Download and install TWS or IB Gateway on Windows
3. Enable API: TWS → Configure → API → Enable ActiveX and Socket Clients
4. Set API port to 7497 (paper trading)
5. `pip install ib_insync`

## Implementation

### `src/data/ibkr_fetcher.py`
- `is_ibkr_available()` — check TWS connection
- `fetch_ibkr(symbol, interval, period)` — download with auto-pagination
- Symbol mapping: `^GSPC` → SPX, `^IXIC` → COMP, `^GDAXI` → DAX
- CSV caching in `data/cache/` for offline walk-forward

### `src/data/fetcher.py`
- Updated routing: OANDA → IBKR → Yahoo (triple fallback)

### CSV Cache
Data cached to `data/cache/{symbol}_{interval}.csv` so walk-forward works without TWS running. Cache used if < 7 days old.

---

## Status

- **Code:** Written, not yet tested (blocked on TWS installation)
- **S&P 500 1H:** Need 10Y for walk-forward (currently only 1Y from Yahoo)
- **NASDAQ 1H:** Same
- **DAX 1H:** Same

---

## Validation Plan

1. Download 10Y of each index at 1H
2. Run walk-forward: `py main.py --walk-forward ^GSPC --strategy sbrs --interval 1h --windows 8`
3. Compare Yahoo 1Y results to IBKR 1Y results for overlap period
4. Target: 500+ trades, 75%+ walk-forward consistency per index

---

## Related

- [[29-P5-P7-P8-OANDA-Portfolio]] — current portfolio tiers
- [[25-Walk-Forward-Full-Results]] — walk-forward methodology
- [[00-MOC-Zeros-Requiem]]
