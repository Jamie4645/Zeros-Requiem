---
tags: [architecture, live-runner, oanda, sbrs]
aliases: [Live Runner, Runner Architecture]
---

# Live Runner Architecture

> How SBRS executes trades on OANDA — the hourly loop, state management, and broker integration.

---

## Overview

The live runner is a stateless hourly script that:
1. Loads state from disk (`state/sbrs_state.json`)
2. Syncs with OANDA (detects trades closed by broker between runs)
3. Fetches latest 1H data (300 bars of history for indicator computation)
4. Runs SBRS entry logic on the current bar
5. Manages open trades (breakeven stops, MA cross exits, timeouts)
6. Executes orders via OANDA REST API
7. Saves state and writes to SQLite
8. Sends alerts

Triggered by Windows Task Scheduler every hour.

```
Run: py -m src.live.runner
```

---

## Module Map

```
src/live/
├── runner.py           # Hourly loop (Steps 1-8 above)
├── oanda_executor.py   # OANDA REST API wrapper
├── state.py            # State management (JSON + SQLite)
└── alerts.py           # Trade notifications
```

---

## State Management

### JSON State (`state/sbrs_state.json`)
Fast read/write for the hourly loop. Contains:
- `pending_setups[]` — Structure breaks waiting for retest
- `open_trades[]` — Active trades with SL/TP/entry info
- `closed_trades[]` — Historical trades with PnL
- `daily_stats` — Daily loss tracking for risk management
- `last_run` — Timestamp of last successful run

### SQLite (`data/zeros_requiem.db`)
Analytical store. Written to on each trade close via `state.py:close_trade()`.
Tables: `trades`, `strategies`, `backtest_runs`, `daily_snapshots`.
Queried interactively via `/trades` skill.

---

## OANDA Executor Functions

| Function | Purpose |
|----------|---------|
| `is_connected()` | Check API connectivity |
| `get_account_balance()` | Current equity for position sizing |
| `get_current_price()` | Bid/ask for spread-aware BE stops |
| `place_market_order()` | Open new trade with SL/TP |
| `modify_stop_loss()` | Move SL (breakeven, trailing) |
| `close_trade()` | Close a trade by OANDA trade ID |
| `get_open_trades()` | List broker-side open positions |
| `sync_positions()` | Detect trades closed between runs |
| `get_closed_trade_details()` | Get actual P&L for broker-closed trades |

---

## Key Parameters

```python
HISTORY_BARS = 300     # ~12.5 days of 1H data
RISK_PCT = 0.01        # 1% of account equity per trade
```

All SBRS parameters are imported from `sbrs_gold.py` — WMA(9), SMMA(7), swing lookback(20), etc.

---

## Known Considerations

1. **Breakeven spread buffer**: BE stop adds 60% of current spread as buffer to prevent immediate SL hits (Phase 0 fix)
2. **Session filter**: 16-20 GMT entries are blocked (`is_session_blocked()`)
3. **Broker sync**: On each run, `sync_positions()` checks if any trades were closed by OANDA (SL/TP hit between hourly runs). Actual P&L is queried from the broker, not estimated.

---

## Related

- [[37-Phase-0-Live-Runner-Bug-Fixes]] — Critical bugs fixed before deployment
- [[38-Phase-1-SQLite-Trade-Database]] — SQLite integration
- [[30-Tool-Live-Status]] — `/live-status` skill
- [[00-MOC-Zeros-Requiem]]
