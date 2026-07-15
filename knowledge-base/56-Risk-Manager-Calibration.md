---
tags: [risk, expansion, bug-fix]
aliases: [Risk Manager Fix, DD Cap Fix, Multi-Asset Risk]
related: [[55-Multi-Asset-Expansion]], [[16-Risk-Management-Elite-System]]
date: 2026-04-05
---

> ⛔ **VOID (see root `CLAUDE.md`).** This file predates the 2026-06-01 phantom-fill audit and
> 2026-07-02 full-codebase audit — the PF/trade-count "edge unlocked" claims below are void
> artifacts, not current state. Retained as historical record only. Current canon: root `CLAUDE.md`
> + [[00-MOC-Zeros-Requiem]].

# 56 — Risk Manager Calibration for Multi-Asset

## Problem

When SBRS 2.0 was first tested on indices (S&P, NASDAQ, DAX), **96-98% of trade setups were blocked** by the risk manager. Only 19-37 trades executed out of 800-1,000+ setups, making it impossible to evaluate whether the strategy had edge.

### Root Cause: 10% Drawdown Circuit Breaker

The risk manager's 5-layer system (see [[16-Risk-Management-Elite-System]]) was calibrated for Gold, which is consistently profitable. On indices, early losses quickly pushed equity below the 10% DD threshold, permanently blocking all new trades.

```
S&P 500:  816 setups → 37 traded → 783 blocked (96%)
NASDAQ:   852 setups → 37 traded → 817 blocked (96%)
DAX:     1031 setups → 19 traded → 1013 blocked (98%)
```

### Secondary Issue: R:R Too High for Indices

The 3.0R minimum target (designed for Gold's large directional moves) was too aggressive for indices. Breakout-retest on indices produces tighter moves — the 3R target was rarely hit, and exit management (MA cross, structure break, timeout) closed trades before TP.

**Before fix:** Avg win/loss ratio on S&P was 1.13:1 (vs Gold's 3.1:1)

### Tertiary Issue: Slippage Miscalculation

Forex pairs priced below $1.00 (AUD/USD ≈ 0.65, NZD/USD ≈ 0.59) fell through the slippage logic into the wrong bucket, receiving **100x intended slippage** ($0.015 instead of $0.00015).

---

## Fixes Applied

### 1. Asset-Class-Aware Risk Config

`risk_config_for_interval()` now accepts `asset_class` parameter:

| Parameter | Gold | Indices/Forex/Crypto |
|-----------|------|---------------------|
| Max DD Cap | 10% | **20%** |
| Daily Loss Limit | 3% | **5%** |
| Concurrent Risk | 8% | **10%** |
| Max Same Direction | 4 | **5** |

### 2. Asset-Specific R:R Minimums

| Asset Class | With-Trend R:R | Counter-Trend R:R |
|-------------|---------------|-------------------|
| Gold | 3.0 | 2.0 |
| Forex | **2.5** | 2.0 |
| Indices | **2.0** | 2.0 |
| Crypto | **2.5** | 2.0 |

### 3. Slippage Fix

```
> $1000:  slip = 1.5 × $0.10   (Gold, indices)
> $10:    slip = 1.5 × $0.01   (Stocks)
> $0.01:  slip = 1.5 × $0.0001 (ALL forex, including AUD/USD)
< $0.01:  slip = 1.5 × $0.000001 (sub-penny)
```

---

## Impact

| Index | Before (Trades / PF) | After (Trades / PF) | Change |
|-------|---------------------|---------------------|--------|
| S&P 500 | 37 / 0.69 | 64 / 0.63 | Still no edge |
| NASDAQ | 37 / 0.87 | **888 / 1.57** | Edge unlocked |
| DAX | 19 / 0.24 | **1,096 / 1.53** | Edge unlocked |

NASDAQ and DAX went from statistical noise to walk-forward validated strategies.

---

## Files Changed

- `src/core/risk_manager.py` — `risk_config_for_interval()` + `apply_slippage()`
- `src/regimes/sbrs_v2.py` — `MIN_RR_INDICES`, `MIN_RR_FOREX`, `MIN_RR_CRYPTO`
- `src/data/fetcher.py` — `detect_asset_class()`, `SYMBOLS`, `SYMBOL_NAMES`
- `main.py` — Asset routing, risk config pass-through
- `src/core/engine.py` — `sbrs_v2_crypto` regime management
- `src/core/walk_forward.py` — `interval`/`asset_class` params

---

## Related

- [[55-Multi-Asset-Expansion]] — Full results from the expansion
- [[16-Risk-Management-Elite-System]] — Original 5-layer risk system
- [[52-Data-Infrastructure-Upgrade]] — OANDA/IBKR data pipeline

---

*Created: 2026-04-05 | Status: Applied & Validated*
