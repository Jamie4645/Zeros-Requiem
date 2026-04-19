--
tags: [infra, live, strategy]
aliases: [Live Runner, Runner Architecture]
related: [[37-Phase-0-Live-Runner-Bug-Fixes]], [[38-Phase-1-SQLite-Trade-Database]], [[60-Phase2-Algo-Improvements]]
---

# Live Runner Architecture

> How SBRS 2.0 executes trades on OANDA — multi-symbol hourly loop, state management, and broker integration.

---

## Overview

The live runner is a stateless hourly script that processes **all configured symbols** sequentially:

For each symbol:
1. Loads per-symbol state from disk (`state/sbrs_state_{key}.json`)
2. Syncs with OANDA (detects trades closed by broker between runs)
3. Fetches latest 1H data (300 bars via OANDA/IBKR/Binance routing)
4. Verifies the latest candle is closed (timing guard)
5. Runs SBRS 2.0 entry logic (confluence scoring, ATR filter, adaptive R:R)
6. Manages open trades (BE, MA cross exit, structure exit, trailing, timeout)
7. Executes orders via OANDA REST API (multi-instrument)
8. Saves per-symbol state to disk + SQLite
9. Sends consolidated daily summary at 16:30 GMT

Triggered by Windows Task Scheduler every hour (recommend HH:05 past the hour).

```
Run: py -m src.live.runner
```

---

## Active Symbols (Paper Trading)

| Symbol | OANDA Instrument | Asset Class | Risk | Data Source |
|--------|-----------------|-------------|------|-------------|
| Gold (GC=F) | XAU_USD | gold | 0.5% | OANDA |
| DAX (^GDAXI) | DE30_EUR | indices | 0.25% | IBKR cache |
| NASDAQ (^IXIC) | NAS100_USD | indices | 0.25% | IBKR cache |
| GBP/USD | GBP_USD | forex | 0.25% | OANDA |

---

## Module Map

```
src/live/
├── runner.py           # Multi-symbol hourly loop (SBRS 2.0)
├── oanda_executor.py   # OANDA REST API (multi-instrument: Gold, Forex, Index CFDs)
├── state.py            # Per-symbol state management (JSON + SQLite)
└── alerts.py           # Telegram alerts (entries/exits/errors only, no noise)
```

---

## State Management

### Per-Symbol JSON State (`state/sbrs_state_{key}.json`)
Each symbol gets its own state file:
- `sbrs_state_GCF.json` — Gold
- `sbrs_state_GDAXI.json` — DAX
- `sbrs_state_IXIC.json` — NASDAQ
- `sbrs_state_GBPUSD.json` — GBP/USD

Contains: pending setups, open trades, trade history, daily PnL, v2.0 fields (confluence_score, is_counter_trend, asset_class).

### SQLite (`data/zeros_requiem.db`)
Analytical store. Written to on each trade close.
Queried interactively via `/trades` skill.

---

## OANDA Executor (Multi-Instrument)

All functions accept an `instrument` parameter for correct price formatting and unit sizing:

| Function | Purpose |
|----------|---------|
| `get_current_price(instrument)` | Bid/ask/mid for any OANDA instrument |
| `place_market_order(..., instrument)` | Market order with SL/TP, correct decimals |
| `modify_stop_loss(id, sl, instrument)` | Move SL with correct price precision |
| `close_trade(id)` | Close at market |
| `sync_positions(trades)` | Detect broker-closed trades |

### Price Precision

| Instrument | Decimals | Unit Type |
|-----------|----------|-----------|
| XAU_USD | 2 | Integer |
| GBP_USD | 5 | Integer |
| EUR_USD | 5 | Integer |
| USD_JPY | 3 | Integer |
| DE30_EUR | 1 | Decimal |
| NAS100_USD | 1 | Decimal |

---

## Timing Guard

The runner includes a candle-close guard to prevent processing incomplete bars:
```
if df.index[-1].hour == now.hour: skip (candle not closed yet)
```
Set Task Scheduler to run at HH:05 for safety. The guard provides a second layer of protection.

---

## Telegram Alerts

Only important events are sent to Telegram (reduced from v1.1 which sent everything):
- Trade entries (with symbol tag, confluence score, R:R)
- Trade exits (with PnL, reason)
- Daily summary (all symbols consolidated)
- Errors

Structure breaks, bar processing, and SL modifications go to the log file only.

---

## Related

- [[37-Phase-0-Live-Runner-Bug-Fixes]] — Critical bugs fixed before deployment
- [[38-Phase-1-SQLite-Trade-Database]] — SQLite integration
- [[60-Phase2-Algo-Improvements]] — ATR filter, adaptive R:R, indices exit optimization
- [[30-Tool-Live-Status]] — `/live-status` skill
- [[00-MOC-Zeros-Requiem]]
