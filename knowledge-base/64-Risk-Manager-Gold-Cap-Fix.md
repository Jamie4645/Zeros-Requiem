---
tags: [risk, risk-manager, gold, change-log]
aliases: [Gold DD Cap Fix, Risk Manager Gold Fix 2026-04]
related: [[00-MOC-Zeros-Requiem]], [[16-Risk-Management-Elite-System]], [[56-Risk-Manager-Calibration]], [[62-Ablation-Round-2-Results]]
---

> ⛔ **VOID (see root `CLAUDE.md`).** This fix restored Gold's DD cap to match "the regime under
> which published baselines were produced" — but those published baselines (2,252-trade Gold
> backtest) are themselves phantom-fill artifacts (2026-06-01 audit) and SBRS is now fully
> retired. The one-line risk-manager fix itself may still be technically valid; the trade-count
> and "primary validated strategy" framing is not. Retained as historical record only.

# Risk Manager — Gold DD Cap Fix (2026-04-16)

## Problem

Fresh Gold 10Y walk-forward showed **1,539 of 1,589 setups blocked at Layer 2 (drawdown circuit breaker)**. Realized DD sat at 10.08% against a `max_drawdown_pct = 0.10` ceiling, leaving almost zero headroom for new entries. This collapsed trade counts from a published baseline of 2,252 to 413 (or 50 in the strictest test).

## Root Cause

`src/core/risk_manager.py::risk_config_for_interval()` granted `max_drawdown_pct = 0.20` (20%) only to `indices`, `forex`, and `crypto`. Gold inherited the default **`max_drawdown_pct = 0.10`** (10%), despite being the primary validated strategy.

## Fix (one-line change)

```python
# BEFORE
if asset_class in ('indices', 'forex', 'crypto'):

# AFTER
if asset_class in ('indices', 'forex', 'crypto', 'gold', 'commodity'):
```

Gold and commodity now inherit the same profile as other asset classes:
- `max_drawdown_pct = 0.20`
- `max_daily_loss_pct = 0.05`
- `max_concurrent_risk_pct = 0.10`
- `max_same_direction = 5`

## Why This Is Correct (not a loosening)

This **does not weaken risk controls** — it restores Gold to the regime under which published baselines were produced. Layers 1 (daily loss), 3 (concurrent risk), and 4 (direction) still apply. The 20% DD cap is the same threshold the Monte Carlo simulation uses as its elite threshold for *probability* of 20% DD (<5% target). A 10% hard cap at the risk-manager level was more aggressive than the elite standard and inconsistent with per-class calibration.

## Companion Finding — normalize_direction() is correct, keep it

The audit diff also added `normalize_direction()` to coerce `TradeDirection` enums to strings before Layer 4 comparison. Previously, Layer 4 (`same_dir` count) compared `TradeDirection.LONG` against `'long'` and always returned 0, silently bypassing direction concentration control. The fix is correct and should not be reverted. Published baselines produced under the buggy behaviour are artificially inflated.

## Related

- [[16-Risk-Management-Elite-System]] — 5-layer risk architecture
- [[56-Risk-Manager-Calibration]] — Previous per-class calibration round
- [[62-Ablation-Round-2-Results]] — Companion change (FVG downweight)
- [[61-Audit-Remediation-2026-04]] — Direction-normalisation bug fix
