---
tags: [archive, expansion, forex]
aliases: [P3-P4 New Pairs]
related: [[20-Priority-2-Gold-Daily-Fix]], [[22-Priority-5-6-Metrics-WalkForward]], [[27-P3-P6-Forex-Fixes]], [[00-MOC-Zeros-Requiem]]
---

# Priority 3 & 4: Add More Trading Pairs

**Date:** 2026-02-11
**Goal:** Increase signal count through diversification — more symbols = more data = more statistical power.

---

## Changes

### Priority 3: New Forex Pairs

Added **GBP/USD** and **USD/JPY** alongside the existing EUR/USD.

- **GBP/USD (`GBPUSD=X`)** — The "Cable". Second most traded forex pair globally. Shares the London/NY killzone dynamics with EUR/USD but has its own personality (wider ranges, more volatile during London session).
- **USD/JPY (`USDJPY=X`)** — The "Gopher". Third most traded pair. Heavily influenced by Bank of Japan policy. Has distinct Asian session dynamics that should work well with the killzone strategy.

**No code changes needed in `forex.py`** — the `analyze_forex()` function is already symbol-agnostic. It processes whatever OHLCV DataFrame is passed in. The Asian range trap, killzone timing, and sweep + FVG detection all work identically across forex pairs.

### Priority 4: Add ETH to Crypto

Added **ETH-USD** alongside the existing BTC-USD.

- **ETH (`ETH-USD`)** — Second largest crypto by market cap. Different volatility profile to BTC — tends to have more explosive compression breakouts.

**No code changes needed in `crypto.py`** — `analyze_crypto()` is already symbol-agnostic.

### Infrastructure: Multi-Symbol Runner

**Files modified:**
- `src/data/fetcher.py` — Added symbol registry (`SYMBOLS` dict), `get_symbol_name()`, `get_symbols_for_class()`, and `fetch_all()` batch function.
- `main.py` — Complete rewrite to support three run modes:
  - `--symbol GC=F` (single symbol, original behavior)
  - `--multi forex` (all symbols in a regime)
  - `--all` (all symbols across all regimes)
- `src/__init__.py` — Version bumped to 4.1.0

---

## Symbol Registry

```
SYMBOLS = {
    'gold':   ['GC=F'],
    'forex':  ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'],
    'crypto': ['BTC-USD', 'ETH-USD'],
}
```

Total: **6 symbols** across 3 asset classes (up from 3).

---

## Usage Examples

```bash
# Single symbol (original)
py main.py --symbol GC=F --interval 4h --period 1y

# All forex pairs
py main.py --multi forex --interval 4h --period 1y

# All crypto
py main.py --multi crypto --interval 4h --period 1y

# Everything (full portfolio backtest)
py main.py --all --interval 4h --period 1y
```

---

## Expected Impact

| Before | After |
|--------|-------|
| 3 symbols | 6 symbols |
| ~18 trades/year | ~36+ trades/year (from diversification alone) |
| EUR/USD only for forex validation | 3 pairs for statistical power |
| BTC only for crypto validation | 2 assets for crypto validation |

Combined with Priority 1 (signal relaxation) and Priority 2 (Gold Daily fix), the total expected trade count rises from ~18 to potentially 500+ per year across all markets.

---

## Notes

- GBP/USD may show stronger killzone signals than EUR/USD due to Cable's higher volatility during London session
- USD/JPY's Asian session dynamics may generate unique sweep patterns not seen in EUR-based pairs
- ETH tends to have more dramatic VR compression/expansion cycles than BTC
- Each symbol gets its own capital allocation in multi-mode ($10k default per symbol)
