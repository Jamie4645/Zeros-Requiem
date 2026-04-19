---
tags: [infra, archive]
aliases: [Phase 6, SCAF Removal]
---

# Phase 6 — SCAF Removal & SBRS Consolidation

> Removed all SCAF (Sovereign Cross-Asset Framework) code, consolidating the codebase to SBRS-only. Focus is now exclusively on the Sovereign Breakout Retest Strategy.

---

## What Was Removed

### Strategy Files (Deleted)
| File | What It Was |
|------|-------------|
| `src/regimes/gold.py` | SCAF Gold regime — Bollinger mean reversion + sweep/FVG momentum |
| `src/regimes/forex.py` | SCAF Forex regime — Killzone, Asian trap, MSS, JPY breakout |
| `src/regimes/crypto.py` | SCAF Crypto regime — Volatility compression + trend momentum |

### Execution Modules (Deleted)
| File | What It Was |
|------|-------------|
| `src/execution/displacement.py` | FVG (Fair Value Gap) detection, Displacement Factor |
| `src/execution/liquidity.py` | Liquidity sweep detection (PDH/PDL, session, Asian range) |

### Indicators (Deleted)
| File | What It Was |
|------|-------------|
| `src/indicators/candlestick.py` | Engulfing, pin bar, expansion candle patterns |

Functions removed from `src/indicators/technical.py`:
- `bollinger_bands()` — used only by SCAF Gold MR
- `volatility_ratio()` — used only by SCAF Crypto
- `displacement_factor()` / `candle_body()` — used only by SCAF execution
- `is_expansion_candle()` — used only by SCAF Crypto
- `detect_session()` / `get_session_range()` — used only by SCAF regimes

### Tests (Deleted)
| File | What It Was |
|------|-------------|
| `tests/quick_test.py` | SCAF all-regime test script (print-based) |
| `tests/test_scaf_quick.py` | Pytest wrapper for SCAF regimes |

### Knowledge Base (Deleted)
| File | What It Was |
|------|-------------|
| `knowledge-base/17-SCAF-2.0-Architecture.md` | SCAF architecture documentation |
| `knowledge-base/18-SCAF-Session-Results.md` | SCAF initial build results |

---

## What Was Refactored

### `TradeSetup` (Clean Break)
The `TradeSetup` dataclass in `src/execution/entries.py` was refactored:
- **Removed**: `sweep` (LiquiditySweep), `fvg` (FairValueGap), `displacement_df` fields
- **Added**: `broken_level`, `retest_bar`, `break_bar` — SBRS-native context fields
- **Result**: No more stub objects or SCAF type dependencies

### `sbrs_gold.py`
- Removed imports of `LiquiditySweep`, `FairValueGap` and their enums
- Removed `_make_stub_sweep()` and `_make_stub_fvg()` helper functions
- TradeSetup construction now uses clean SBRS fields

### `main.py`
- Removed `--strategy` flag (was `scaf`/`sbrs`, now SBRS is the only option)
- Removed `--multi` and `--all` flags (were for multi-regime SCAF runs)
- Removed imports of `analyze_gold`, `analyze_forex`, `analyze_crypto`
- Default interval changed to `1h` (SBRS primary timeframe)
- Default walk-forward windows changed to `8`

### `fetcher.py`
- Removed `forex` and `crypto` from SYMBOLS registry
- Removed forex/crypto symbol names
- Removed crypto/forex detection from `detect_asset_class()`

### `.cursorrules`
- Completely rewritten from SCAF-focused to SBRS-focused

### Core Module Docstrings
- `engine.py`, `walk_forward.py`, `risk_manager.py`, `monte_carlo.py` — all updated to remove SCAF references

---

## What Was Kept

All SBRS infrastructure remains untouched:
- `src/regimes/sbrs_gold.py` — core strategy
- `src/regimes/sbrs_original_parameters.py` — locked parameter reference
- `src/live/*` — live runner, executor, state, alerts
- `src/data/*` — OANDA, IBKR, Yahoo fetchers
- `src/visualization/*` — charts module
- `src/core/*` — engine, risk, walk-forward, Monte Carlo
- All SBRS test files
- All Phase 0-5 knowledge-base documents

---

## Related

- [[00-MOC-Zeros-Requiem]]
- [[37-Phase-0-Live-Runner-Bug-Fixes]] — previous phase
