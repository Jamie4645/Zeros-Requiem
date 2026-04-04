---
tags: [phase-4, vectorbt, validation, cross-check]
aliases: [Phase 4, VectorBT Validation]
---

# Phase 4 — VectorBT Engine Validation

> Validate the backtest engine against an independent framework before trusting it with real capital.

---

## Purpose

The backtest engine (`src/core/engine.py`) has a known history of bugs (direction bug, BE stop issues). Cross-validating against VectorBT ensures our Sharpe, P&L, and drawdown calculations are correct.

## Tests

### `tests/test_engine_validation.py`

| Test Class | What It Checks |
|------------|----------------|
| `TestSharpeCalculation` | Sharpe ratio matches VectorBT within 0.05 |
| `TestMaxDrawdown` | Max drawdown matches within 2% |
| `TestPnLAccuracy` | Long/short P&L calculations are correct |
| `TestProfitFactor` | PF = gross wins / gross losses |

### Skipped Without VectorBT

All tests use `pytest.mark.skipif(not HAS_VBT)` so they skip gracefully if vectorbt isn't installed. This keeps the test suite runnable on minimal setups.

## Dependencies

- `vectorbt>=0.25.0` (heavy: includes numba, requires compilation)
- `pytest>=7.0` (Phase 3)

## Installation

```bash
pip install vectorbt
```

Note: First install may take several minutes (numba compilation).

---

## Related

- [[40-Phase-3-Pytest-Migration]] — pytest infrastructure
- [[25-Walk-Forward-Full-Results]] — engine output to validate
- [[00-MOC-Zeros-Requiem]]
