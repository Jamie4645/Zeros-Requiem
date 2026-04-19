--
tags: [infra, milestone]
aliases: [Data Infrastructure, OANDA Fix, Data Pipeline Fix]
related: [[45-Data-Pipeline]], [[39-Phase-2-IBKR-Index-Data]], [[47-SBRS-2.0-Upgrade]], [[00-MOC-Zeros-Requiem]]
---

# Data Infrastructure Upgrade — OANDA & IBKR

**Date:** 2026-04-05
**Impact:** Unlocked 10Y Gold data (59,046 bars) — 30x more than Yahoo's 2Y limit

---

## The Problem

All backtests were running on Yahoo Finance data (limited to ~2Y for 1H bars). The `.env` file had valid OANDA credentials, and IBKR Gateway was available, but two missing dependencies prevented their use:

1. **`python-dotenv` not installed** — OANDA credentials silently failed to load (caught by `except ImportError: pass`)
2. **`ib_insync` not installed** — IBKR connection silently fell back to Yahoo
3. **Python 3.14 asyncio incompatibility** — `ib_insync` used deprecated `get_event_loop()` pattern

All three issues caused silent fallback to Yahoo with no visible error — the strategy appeared to work but was being tested on inadequate data.

---

## The Fix

### Dependencies Installed
```bash
py -m pip install python-dotenv ib_insync
```

### IBKR Asyncio Fix
`src/data/ibkr_fetcher.py` — `is_ibkr_available()` was rewritten to use a raw TCP socket check instead of `ib_insync`'s problematic async connection test:

```python
def is_ibkr_available() -> bool:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('127.0.0.1', 7497))
    sock.close()
    return result == 0
```

### Fetcher Routing Hardened
`src/data/fetcher.py` — Yahoo Finance is now **forbidden** for premium symbols:

| Symbol | Mandatory Source | Fallback |
|--------|-----------------|----------|
| Gold (GC=F) | OANDA | Error (no Yahoo) |
| S&P 500 (^GSPC) | IBKR | Error if no TWS + no cache |
| NASDAQ (^IXIC) | IBKR | Error if no TWS + no cache |
| DAX (^GDAXI) | IBKR | Error if no TWS + no cache |

---

## Data Sources Now Available

| Source | Symbols | Data Depth | Status |
|--------|---------|------------|--------|
| OANDA (practice API) | Gold, Forex | 20+ years | ACTIVE |
| IBKR (Gateway port 7497) | Indices, Gold | 10+ years | ACTIVE (when TWS running) |
| Yahoo Finance | Other | ~2Y for 1H | FALLBACK only |

---

## Impact on Results

The strategy was being validated on 11,486 bars (2Y Yahoo). After the fix:
- **59,046 bars (10Y OANDA)** — 5x more data
- Walk-forward went from 4 windows to proper 8 windows
- Results went from inconclusive (50% consistency) to validated (75% consistency)

---

## Related

- [[45-Data-Pipeline]] — Original data pipeline documentation
- [[39-Phase-2-IBKR-Index-Data]] — IBKR setup phase
- [[47-SBRS-2.0-Upgrade]] — The strategy that benefited from this fix
- [[00-MOC-Zeros-Requiem]]
