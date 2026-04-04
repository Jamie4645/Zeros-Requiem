--
tags: [priority, OANDA, portfolio, tiers, gold-1h-removed, core, critical]
aliases: [OANDA Portfolio, Portfolio Tiers, P5-P8]
related: [[CLAUDE]], [[07-Guide-Python-Broker-APIs]], [[25-Walk-Forward-Full-Results]], [[28-P4-Monte-Carlo]], [[30-Tool-Live-Status]], [[00-MOC-Zeros-Requiem]]
---

# P5: OANDA Integration + P7: Gold 1H Removal + P8: Portfolio Tiers

**Date:** 2026-02-12

---

## P5: OANDA v20 API Integration

### What Changed

Added dual data source: OANDA for Gold + Forex (20+ years), Yahoo Finance for Crypto.

**New files:**
- `src/data/oanda_fetcher.py` — OANDA v20 REST API client with automatic pagination
- `.env` — API credentials (NEVER committed, in .gitignore)
- `.gitignore` — Excludes .env, __pycache__, IDE files

**Modified files:**
- `src/data/fetcher.py` — `fetch()` now auto-routes to OANDA for Gold/Forex, Yahoo for Crypto
- `main.py` — Walk-forward uses 10Y period when OANDA is available
- `requirements.txt` — Added python-dotenv, requests

### Data Available via OANDA

| Instrument | Candles (4H, 10Y) | From | To |
|---|---|---|---|
| Gold (XAU_USD) | **15,457** | 2016-02-15 | 2026-02-12 |
| GBP/USD | **15,553** | 2016-02-15 | 2026-02-12 |
| EUR/USD | Similar | 2005+ | Present |
| USD/JPY | **12,430** (1H, 2Y) | 2024-02-13 | 2026-02-12 |

### 10-Year Walk-Forward Results

#### Gold 4H — 10 Years, 10 Windows, 624 Trades

| Window | Period | Trades | WR | PnL | PF | Sharpe |
|---|---|---|---|---|---|---|
| W1 | 2016-2017 | 14 | 14% | -$1,091 | 0.18 | -1.94 |
| **W2** | **2017-2018** | **96** | **42%** | **+$3,255** | **1.57** | **1.51** |
| W3 | 2018-2019 | 65 | 26% | -$559 | 0.89 | -0.26 |
| W4 | 2019-2020 | 12 | 17% | -$1,003 | 0.15 | -1.80 |
| W5 | 2020-2021 | 74 | 34% | +$983 | 1.21 | 0.51 |
| W6 | 2021-2022 | 82 | 32% | -$133 | 0.98 | -0.10 |
| W7 | 2022-2023 | 76 | 36% | +$212 | 1.04 | 0.16 |
| W8 | 2023-2024 | 51 | 29% | -$470 | 0.88 | -0.30 |
| W9 | 2024-2025 | 82 | 34% | +$830 | 1.15 | 0.41 |
| **W10** | **2025-2026** | **72** | **36%** | **+$1,994** | **1.48** | **1.03** |

**Summary:** 50% consistency, +$4,018 combined, edge improving (+$83/window).
**624 total trades — PASSES the 500-trade Elite Benchmark.**

#### GBP/USD 4H — 10 Years, 10 Windows, 486 Trades

| Window | Period | Trades | WR | PnL | PF | Sharpe |
|---|---|---|---|---|---|---|
| W1 | 2016-2017 | 41 | 37% | -$491 | 0.83 | -0.43 |
| W2 | 2017-2018 | 64 | 42% | +$288 | 1.07 | 0.21 |
| **W3** | **2018-2019** | **72** | **56%** | **+$2,681** | **1.72** | **1.52** |
| W4 | 2019-2020 | 18 | 28% | -$1,009 | 0.20 | -1.94 |
| W5 | 2020-2021 | 69 | 54% | +$750 | 1.22 | 0.41 |
| W6 | 2021-2022 | 65 | 37% | +$86 | 1.02 | 0.12 |
| W7 | 2022-2023 | 52 | 42% | +$821 | 1.26 | 0.60 |
| W8 | 2023-2024 | 20 | 20% | -$1,315 | 0.38 | -1.34 |
| W9 | 2024-2025 | 63 | 48% | +$881 | 1.23 | 0.53 |
| W10 | 2025-2026 | 22 | 36% | -$964 | 0.46 | -1.05 |

**Summary:** 60% consistency, +$1,728 combined, edge degrading (-$92/window).
**486 total trades — close to 500 threshold.**

---

## P7: Gold 1H Removed

### Decision

Gold 1H has been removed from the active portfolio and quick_test.

### Rationale

1. **No edge exists**: 78 trades, 33% WR, PF 0.98, -$104, 11.6% DD
2. **Architecture mismatch**: Sweep+FVG detects institutional flow on 4H+ cadence. On 1H, it detects micro-sweeps of the same levels multiple times within one real move.
3. **Signal clustering**: 79 trades blocked by risk manager = system generating 157 signals where only 78 execute, and even those lose money.
4. **Validated alternatives exist**: Gold 4H (Sharpe 1.49) and Gold Daily (88% WF) are both proven.
5. **Elite trader alignment**: ICT/institutional Gold traders use 4H for structure, Daily for bias. 1H is for entry timing in discretionary trading, not for signal generation in systematic trading.

---

## P8: Portfolio Tiers

### Core (Full Allocation — Validated)

| Market | Timeframe | Sharpe | PF | WF Consistency | MC (20% DD) |
|---|---|---|---|---|---|
| **Gold** | **4H** | **1.49** | **1.71** | 50% (10Y) | **0.28%** |
| **Gold** | **Daily** | 1.09 | **2.05** | **88%** (5Y) | **0.02%** |
| **GBP/USD** | **4H** | 0.83 | **1.68** | **60%** (10Y) | **0.02%** |

### Satellite (Reduced Allocation — Accumulating Evidence)

| Market | Timeframe | Status | Next Step |
|---|---|---|---|
| USD/JPY | 1H | Sharpe 1.36 in one window | WF validate with OANDA |
| BTC | 4H | PF 1.18, 11 trades | Accumulate more trades |
| BTC | 1H | PF 1.52, 11 trades | Promising, needs more data |
| ETH | 4H | PF 2.31, 8 trades | Exceptional quality, tiny sample |
| EUR/USD | Daily | 60% WR, 5 trades | Sparse but safe |

### Dropped (No Edge — Do Not Trade)

| Market | Timeframe | Reason |
|---|---|---|
| Gold | 1H | PF 0.98, sweep+FVG doesn't suit 1H |
| EUR/USD | 4H | PF 1.03, breakeven |
| EUR/USD | 1H | PF 1.02, EUR/USD too liquid for killzone traps |
| USD/JPY | 4H | Asian range fades lose money, PDH/PDL too sparse |
| AUD/USD | All | Pacific currency, Asian session is real move |
| NZD/USD | All | Same as AUD/USD |
| Crypto | Daily | Walk-forward: 12% consistency, no edge |
| GBP/USD | Daily | Walk-forward: 38% consistency, no edge |
