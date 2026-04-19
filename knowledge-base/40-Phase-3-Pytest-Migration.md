---
tags: [infra, tooling]
aliases: [Phase 3, Pytest Migration]
---

# Phase 3 — Pytest Migration

> 10 test files using `print()` statements migrated to proper pytest with assertions. Enables CI, hooks, and coverage tracking.

---

## Before vs After

| Before | After |
|--------|-------|
| `print("PASS")` / `print("FAIL")` | `assert` statements |
| `global passed, failed` counter | pytest auto-collection |
| `sys.exit(1)` on failure | pytest exit codes |
| No coverage tracking | `pytest-cov` integration |
| Manual run only | Hook-triggered on src/ edits |

---

## New Test Files

| File | Tests | Source |
|------|-------|--------|
| `tests/conftest.py` | Shared fixtures (data, backtest results) | New |
| `tests/test_sbrs_indicators.py` | WMA, SMMA, swing detection (rewritten) | Migrated |
| `tests/test_gold_backtest.py` | Gold 1H SBRS backtest assertions | New |
| `tests/test_scaf_quick.py` | SCAF multi-regime quick tests | From `quick_test.py` |
| `tests/test_engine_validation.py` | VectorBT cross-validation (Phase 4) | New |

## Kept As Manual

| File | Reason |
|------|--------|
| `tests/quick_test.py` | Legacy, still works as manual script |
| `tests/chart_trades.py` | Visual inspection required |
| `tests/chart_candles.py` | Visual inspection required |
| `tests/chart_full_candles.py` | Visual inspection required |
| `tests/sbrs_deep_analysis.py` | Too slow for auto-run (10Y analysis) |

---

## Running Tests

```bash
# All tests
py -m pytest tests/ -v --tb=short

# Just indicators (fast, no network)
py -m pytest tests/test_sbrs_indicators.py -v

# With coverage
py -m pytest tests/ --cov=src --cov-report=term-missing

# Skip slow tests
py -m pytest tests/ -v -k "not slow"
```

## Hook Integration

The PostToolUse hook in `.claude/settings.local.json` runs `python -m pytest tests/quick_test.py` after editing `src/*.py` files. After migration, this properly reports pass/fail.

---

## Related

- [[32-Tool-Auto-Test-Hook]] — auto-test hook configuration
- [[41-Phase-4-VectorBT-Validation]] — cross-validation tests
- [[00-MOC-Zeros-Requiem]]
