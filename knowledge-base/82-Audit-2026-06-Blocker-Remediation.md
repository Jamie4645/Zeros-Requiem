---
tags: [audit, remediation, fixes, risk, tests]
aliases: [Blocker Remediation 2026-06, Audit Fixes, Six Blockers]
related: [[81-Audit-2026-06-01-Phantom-Fill]], [[83-Reversal-Fill-Fix]], [[84-Realistic-Fill-No-Edge]], [[16-Risk-Management-Elite-System]], [[64-Risk-Manager-Gold-Cap-Fix]], [[76-Round-8-Evidence-Weighted-Sizing]]
---

# 82 — Audit 2026-06: Blocker Remediation Log

Part of the [[81-Audit-2026-06-01-Phantom-Fill|2026-06 phantom-fill audit]]. The
full-codebase audit surfaced six blockers; five were fixable mechanical defects
(this note), the sixth (#2 reversal) became the whole-portfolio finding — see
[[83-Reversal-Fill-Fix]] and [[84-Realistic-Fill-No-Edge]].

**Test status throughout: 187 passed, 2 skipped (suite stayed green after every fix).**

## #1 — SYMBOL_RISK_CAP was cosmetic → real clamp (CRITICAL)
- `SYMBOL_RISK_CAP` (`src/core/risk_manager.py`) was consulted only by
  `walk_forward.py`. The dominant backtest path (`analyze_sbrs_v2`) and the live
  path (`engine_live.py`, `runner.py`) sized from raw uncapped `risk_pct`. Sizing
  was correct *only by coincidence* (config constants happened to equal the caps).
- **Fix:** added `capped_risk_pct(risk_pct, symbol)` in `src/regimes/sbrs_v2.py`
  and clamp at the top of `analyze_sbrs_v2` — the single chokepoint shared by
  backtest + walk-forward + live. `risk_manager.py` (a LOCKED file) was NOT
  modified; the clamp only *reads* its dict. USDJPY (cap 0.0) now collapses to 0.
- **Test:** `tests/test_risk_caps.py` re-anchored to R8 + covers the chokepoint.

## #3 — oanda_executor stale `_last_fill_price` (HIGH)
- Module global set only in the `orderFillTransaction` branch; on
  reject / exception / `relatedTransactionIDs` paths it retained a prior trade's
  (possibly prior instrument's) fill, corrupting `slip_logger` (Falsifier #1).
- **Fix (`src/live/oanda_executor.py`):** reset to `None` at `place_market_order`
  entry; capture the real fill on the `relatedTransactionIDs` branch; removed the
  now-dead `_get_latest_trade_id` helper.

## #4 — test_risk_caps.py was RED (HIGH)
- Pinned stale R7 caps (GBPUSD 0.0025, USDJPY 0.0025) vs R8 source
  (GBPUSD 0.0020, USDJPY 0.0000, GOLD 0.0050). The safety guard guarded nothing.
- **Fix:** re-anchored every assertion to R8 + added a "no extra symbols" pin.

## #5 — No SACRED-param test pins (HIGH)
- A silent `WMA 9 → 12` edit passed the full suite (the explicit CLAUDE.md
  "we have a problem" failure mode).
- **Fix:** new `tests/test_sacred_params.py` pins WMA=9 / SMMA=7 /
  SWING_LOOKBACK=20 / MIN_RR=3.0 / RETEST_TOLERANCE_ATR=0.7 + tunables. Documents
  the canon-vs-code divergences (RETEST 0.7 in code vs 0.5 in CLAUDE.md text;
  per-asset MIN_RR floors) as tracked items, not failures.

## #6 — Adaptive R:R admits sub-3.0 fills (HIGH) → KEEP, document
- `sbrs_v2.py` adaptive-R:R clamp (`ATR_RR_CLAMP_LOW=0.7`) admits Gold fills down
  to ~2.1R vs the SACRED MIN_RR=3.0. Ablation (`logs/audit/edge_ablation.log`)
  showed restoring the hard 3.0 floor cuts Gold PnL 58.5% and worsens DD — the
  sub-3.0 fills *contribute*. **Decision (user):** keep adaptive R:R, fix canon.
  (Moot in the end — see [[84-Realistic-Fill-No-Edge]].)

## #2 — Reversal "edge" → the phantom-fill bug
The big one. Reversal entries were 93–149% of every instrument's profit and won
95–100% of the time on impossible fills. Full story: [[83-Reversal-Fill-Fix]] →
[[84-Realistic-Fill-No-Edge]].

## Bonus fix
`tests/test_gold_backtest.py` flaky PF-band test (asserted a 0.5 PF floor on a
live 6-month slice that can legitimately lose) → relaxed to the meaningful upper
(leakage) bound.

## Code touched
`src/regimes/sbrs_v2.py`, `src/core/risk_manager.py` (read-only), `src/core/engine.py`,
`src/live/oanda_executor.py`, `src/live/engine_live.py`, `src/live/runner.py`,
`tests/test_risk_caps.py`, `tests/test_sacred_params.py`, `tests/test_gold_backtest.py`.
