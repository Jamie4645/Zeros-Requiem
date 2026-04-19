---
name: data-refresh
description: Refresh OHLCV data for validated symbols from OANDA/IBKR/Binance (skip Yahoo for premium-only symbols). Use when the user says "refresh data", "pull ibkr", "update oanda", "get latest bars", or "update data".
user_invocable: true
argument-hint: [symbol|all] [interval]
allowed-tools: Bash(py:*), Bash(python:*), Read
---

# /data-refresh — Source-Aware Data Update

Routes each symbol to its mandatory source per `src/data/fetcher.py`:
- **Gold (`GC=F`)** → OANDA (20Y+) — **no Yahoo fallback allowed**
- **Forex** → OANDA (20Y+)
- **Indices (`^GSPC`, `^IXIC`, `^GDAXI`)** → IBKR (10Y+) — **premium only**
- **Crypto (`BTC-USD`, `ETH-USD`)** → Binance (5Y+)
- **Everything else** → Yahoo

## Protocol

### Step 1 — Parse args
| Arg | Options |
|---|---|
| Symbol | specific (e.g. `GC=F`) or `all` (Tier 1 + Tier 2 only) |
| Interval | `1h` (default), `4h`, `1d` |

### Step 2 — Check connectivity FIRST (fail fast)
```bash
py -c "from src.data.oanda_fetcher import is_oanda_available; from src.data.ibkr_fetcher import is_ibkr_available; from src.data.binance_fetcher import is_binance_available; print('OANDA:', is_oanda_available()); print('IBKR:', is_ibkr_available()); print('Binance:', is_binance_available())"
```
If a required source is down, STOP and report. Do not silently fall back to Yahoo for premium-only symbols — CLAUDE.md forbids it.

### Step 3 — Fetch (per symbol, smart cache)
```bash
py -c "from src.data.fetcher import fetch; df = fetch('<SYMBOL>', '<INT>', '10y'); print(f'{len(df)} bars, {df.index[0]} → {df.index[-1]}')"
```

For `all`, loop through the Tier 1/2 universe (from CLAUDE.md):
```
Tier 1: GC=F, ^GDAXI, ^IXIC
Tier 2: GBPUSD=X, BTC-USD, ETH-USD
```

### Step 4 — Report
```
═══════════════════════════════════════════════════════
  DATA REFRESH SUMMARY
═══════════════════════════════════════════════════════
  Symbol       Source   Bars    First Date    Last Date    Gap?
  GC=F         OANDA    XX,XXX  2014-XX-XX    2026-XX-XX   ✅
  ^GDAXI       IBKR     XX,XXX  2016-XX-XX    2026-XX-XX   ✅
  ...
═══════════════════════════════════════════════════════
```

### Step 5 — Flags
- ⚠️ Last bar >48h old → data feed possibly stale
- ❌ Source mismatch (e.g. Yahoo used for Gold) → investigate; Yahoo for `GC=F` is banned
- ⚠️ <5Y of data on a symbol being walk-forward-tested → warn user WF will be weak

## Notes
- Fetcher already handles caching — no need to clear caches unless the user explicitly asks.
- For a fresh pull (no cache), user must manually delete relevant files under `data/cache/`.
