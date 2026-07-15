---
tags: [expansion, milestone, multi-asset]
aliases: [Multi-Asset Expansion, Asset Expansion, SBRS Multi-Market]
related: [[47-SBRS-2.0-Upgrade]], [[56-Risk-Manager-Calibration]], [[57-Monte-Carlo-Gold-v2]], [[58-GBP-USD-Discovery]]
date: 2026-04-05
---

> ⛔ **VOID/RETIRED (see root `CLAUDE.md`).** Multi-asset SBRS 2.0 numbers below are phantom-fill
> artifacts (2026-06-01 audit); realistic-fill re-validation found no edge on any instrument, and
> SBRS is now fully retired (ZTT rebuild is Gold-only, does not inherit SBRS logic). Retained as
> historical record only.

# 55 — SBRS 2.0 Multi-Asset Expansion

> *"You don't need to know what will happen next to make money."* — Mark Douglas

## Summary

On 2026-04-05, SBRS 2.0 was tested across **10 instruments** in 4 asset classes. Three new walk-forward validated assets were discovered (DAX, NASDAQ, GBP/USD shows promise), and crypto showed unexpected strength on limited data.

**Key result:** The SBRS breakout-retest edge is NOT Gold-specific. It generalises to trending instruments with clean structure.

---

## Master Results Table

| Asset | Class | Data | Trades | WR | PnL | PF | Sharpe | DD | WF | Tier |
|-------|-------|------|--------|----|-----|----|--------|----|----|------|
| **Gold** | Commodity | 10Y OANDA | 2,252 | 38.9% | $146,256 | 1.97 | 1.77 | 9.17% | 75% (6/8) | **1** |
| **GBP/USD** | Forex | 10Y OANDA | 1,323 | 35.8% | $152,680 | 2.69 | 2.00 | 7.84% | 62% (5/8) | **2** |
| **NASDAQ** | Index | 10Y IBKR | 888 | 45.3% | $27,910 | 1.57 | 1.11 | 17.84% | 88% (7/8) | **1** |
| **DAX** | Index | 10Y IBKR | 1,096 | 41.8% | $33,912 | 1.53 | 1.18 | 11.41% | 88% (7/8) | **1** |
| **USD/JPY** | Forex | 10Y OANDA | 1,228 | 34.5% | $21,811 | 1.27 | 0.84 | 15.65% | — | 3 |
| **EUR/USD** | Forex | 10Y OANDA | 501 | 32.5% | $2,532 | 1.08 | 0.23 | 20.14% | — | 3 |
| **Bitcoin** | Crypto | 2Y Yahoo | 747 | 34.7% | $31,539 | 1.59 | 2.76 | 9.56% | — | 2 |
| **Ethereum** | Crypto | 2Y Yahoo | 748 | 32.2% | $33,890 | 1.63 | 2.63 | 9.70% | — | 2 |
| **S&P 500** | Index | 10Y IBKR | 64 | 32.8% | -$1,654 | 0.63 | -0.39 | 20.40% | — | 4 |
| **AUD/USD** | Forex | 10Y OANDA | 153 | 28.8% | -$1,197 | 0.89 | -0.15 | 21.29% | — | 4 |

---

## Tier Classification

### Tier 1 — Walk-Forward Validated
- **Gold** — 75% WF (6/8), 7/7 benchmarks. The flagship. See [[47-SBRS-2.0-Upgrade]].
- **DAX** — 88% WF (7/8), PF 1.53, DD 11.41%. Most consistent index.
- **NASDAQ** — 88% WF (7/8), PF 1.57, 45.3% WR. Edge IMPROVING over time.

### Tier 2 — Promising, Needs More Validation
- **GBP/USD** — Highest single-test PF (2.69) but WF only 62% (5/8). W7 collapse (21.5% WR). See [[58-GBP-USD-Discovery]].
- **Bitcoin** — PF 1.59, Sharpe 2.76, but only 2Y data. Red flag: Sharpe > 2.5 on short data.
- **Ethereum** — PF 1.63, Sharpe 2.63. Same 2Y caveat.

### Tier 3 — Marginal Edge
- **USD/JPY** — PF 1.27, positive but thin. 19-bar max losing streak.
- **EUR/USD** — PF 1.08, barely profitable. 22-bar max losing streak.

### Tier 4 — No Edge (Reject)
- **S&P 500** — PF 0.63 even with relaxed risk manager. No edge.
- **AUD/USD** — PF 0.89. Low WR (28.8%), heavy blocking.

---

## Walk-Forward Results

### Gold 1H (10Y, 8 Windows)
```
W1 2016-04→2017-07: $7,715  PF 1.48  ✅
W2 2017-07→2018-10: $940    PF 1.17  ✅
W3 2018-10→2020-01: $1,634  PF 1.21  ✅
W4 2020-01→2021-04: $7,604  PF 1.51  ✅
W5 2021-04→2022-07: -$608   PF 0.88  ❌
W6 2022-07→2023-10: -$76    PF 0.99  ❌
W7 2023-10→2025-01: $328    PF 1.06  ✅
W8 2025-01→2026-04: $1,229  PF 1.22  ✅
Consistency: 75% (6/8)  Combined: $18,765
```

### DAX 1H (10Y, 8 Windows)
```
W1 2016-03→2017-06: $2,217  PF 1.25  ✅
W2 2017-06→2018-09: $2,546  PF 1.39  ✅
W3 2018-09→2019-12: $4,946  PF 1.60  ✅
W4 2019-12→2021-03: $2,079  PF 1.28  ✅
W5 2021-03→2022-06: $1,218  PF 1.18  ✅
W6 2022-06→2023-09: $358    PF 1.05  ✅
W7 2023-09→2024-12: $3,647  PF 1.46  ✅
W8 2024-12→2026-03: -$218   PF 0.97  ❌
Consistency: 88% (7/8)  Combined: $16,794
```

### NASDAQ 1H (10Y, 8 Windows)
```
W1 2016-03→2017-06: $948    PF 1.15  ✅
W2 2017-06→2018-09: $60     PF 1.01  ✅
W3 2018-09→2019-12: $2,888  PF 1.62  ✅
W4 2019-12→2021-03: -$681   PF 0.89  ❌
W5 2021-03→2022-06: $3,946  PF 1.80  ✅
W6 2022-06→2023-09: $5,726  PF 1.82  ✅
W7 2023-09→2024-12: $5,053  PF 1.94  ✅
W8 2024-12→2026-03: $1,556  PF 1.27  ✅
Consistency: 88% (7/8)  Combined: $19,496
Edge slope: +$504/window (IMPROVING)
```

### GBP/USD 1H (10Y, 8 Windows)
```
W1 2016-04→2017-07: $7,373  PF 1.77  ✅
W2 2017-07→2018-10: $2,288  PF 1.22  ✅
W3 2018-10→2020-01: $712    PF 1.08  ✅
W4 2020-01→2021-04: -$1     PF 1.00  ❌
W5 2021-04→2022-07: $3,404  PF 1.31  ✅
W6 2022-07→2023-10: -$281   PF 0.98  ❌
W7 2023-10→2025-01: -$2,012 PF 0.59  ❌  ← regime shift?
W8 2025-01→2026-04: $1,810  PF 1.21  ✅
Consistency: 62% (5/8)  Combined: $13,293
```

---

## Code Changes Made

1. **[[56-Risk-Manager-Calibration]]** — DD cap 10%→20% for non-Gold, wider concurrency limits
2. **Asset-specific R:R** — Gold 3.0, Forex 2.5, Indices 2.0, Crypto 2.5
3. **Forex/crypto symbol registration** — `fetcher.py` updated with 4 forex + 2 crypto
4. **Slippage fix** — Sub-$1 forex pairs (AUD/USD) were getting 100x intended slippage
5. **Engine update** — `sbrs_v2_crypto` regime tag for trade management

See [[56-Risk-Manager-Calibration]] for full technical details.

---

## What This Means for the Portfolio

**Before (April 5 AM):** 1 validated strategy (Gold), 3 untested (indices)
**After (April 5 PM):** 3 validated strategies (Gold + DAX + NASDAQ), 3 promising (GBP/USD + BTC + ETH)

The path to the 5-strategy portfolio is now clear:
1. Gold 1H SBRS 2.0 — **live ready**
2. DAX 1H SBRS 2.0 — **paper trade ready** (88% WF)
3. NASDAQ 1H SBRS 2.0 — **paper trade ready** (88% WF)
4. GBP/USD 1H SBRS 2.0 — **needs tuning** (62% WF, investigate W7)
5. BTC 1H SBRS 2.0 — **needs 5Y+ data** (2Y is insufficient for WF)

---

## Related Notes

- [[47-SBRS-2.0-Upgrade]] — Original Gold v2.0 documentation
- [[56-Risk-Manager-Calibration]] — Risk manager fixes for multi-asset
- [[57-Monte-Carlo-Gold-v2]] — Gold v2 Monte Carlo results
- [[58-GBP-USD-Discovery]] — GBP/USD deep-dive
- [[54-Fine-Tuning-Process]] — How ablation drove the v2.0 upgrades
- [[52-Data-Infrastructure-Upgrade]] — OANDA/IBKR data pipeline

---

*Created: 2026-04-05 | Status: Active*
