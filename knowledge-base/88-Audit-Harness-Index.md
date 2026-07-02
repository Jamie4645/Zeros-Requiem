---
tags: [reference, harnesses, logs, tests, index]
aliases: [Audit Harness Index, Audit Logs, 2026-06 Scripts]
related: [[81-Audit-2026-06-01-Phantom-Fill]], [[82-Audit-2026-06-Blocker-Remediation]], [[83-Reversal-Fill-Fix]], [[84-Realistic-Fill-No-Edge]], [[85-Primary-Edge-Teardown]], [[86-SBRS-3.0-Spec-And-Build]], [[87-Supervised-Rebuild]]
---

# 88 — Audit Harness & Log Index (2026-06)

Reference for every investigation script and output from the 2026-06 audit + the
SBRS 3.0 rebuild. All are reproducible; run with the venv python.

## Investigation harnesses (`tests/`)
| Script | Purpose | Output log |
|---|---|---|
| `_audit_edge_ablation.py` | Reversal / structure-exit / sub-3R contribution | `logs/audit/edge_ablation.log` |
| `_audit_reversal_stats.py` | Phantom-fill isolation (`--all` for 5 instruments) | `logs/audit/reversal_stats_all.log` |
| `_audit_realistic_revalidation.py` | Realistic-fill BT, all instruments | `logs/audit/realistic_revalidation.log` |
| `_audit_selectivity_sweep.py` | Tightening levers + strip-back | `logs/audit/selectivity_sweep.log` |
| `_audit_entry_mode_ab.py` | Candle-close vs limit-at-retest | `logs/audit/entry_mode_ab.log` |
| `_audit_sbrs_v3.py` | SBRS 3.0 structural-exit backtest | `logs/audit/sbrs_v3.log` |

## Regression tests added (`tests/`)
- `test_risk_caps.py` — re-anchored to R8 + cap-clamp chokepoint coverage.
- `test_sacred_params.py` — pins SACRED + tunable params.
- `test_gold_backtest.py` — PF-band test de-flaked.

## Source touched
- `src/regimes/sbrs_v2.py` — `capped_risk_pct` clamp; `entry_mode` toggle; `is_limit`.
- `src/regimes/sbrs_v3.py` — NEW: bare-core entries + structural exits.
- `src/core/engine.py` — reversal limit-fill fix; `REVERSAL_ENTRY_ENABLED`,
  `STRUCTURE_EXIT_ENABLED`, `REVERSAL_LIMIT_MAX_WAIT`; `is_limit` routing.
- `src/core/risk_manager.py` — read-only (LOCKED); not modified.
- `src/live/oanda_executor.py` — fill-price reset fix.
- `src/execution/entries.py` — `TradeSetup.is_limit` field.

## Specs & intake
- `docs/sbrs_3.0_spec.md` — SBRS 3.0 specification (see [[86-SBRS-3.0-Spec-And-Build]]).
- `analysis/real_trades/README.md` + `trades_template.csv` — supervised intake
  (see [[87-Supervised-Rebuild]]).

## Reusable workflow
`.claude/workflows/full-codebase-audit.js` — the multi-agent audit that started
this whole chain (`/full-codebase-audit`). Both councils (Arbiter + Philosophical).
