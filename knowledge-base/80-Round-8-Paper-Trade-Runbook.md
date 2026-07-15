---
tags: [runbook, paper-trade, round-8]
aliases: [R8 Paper Runbook, Paper-Trade Gate]
related: [[75-Pre-Registered-Falsifier-R8]], [[76-Round-8-Evidence-Weighted-Sizing]], [[77-Round-8-Canon]]
---

# 80 — Round 8 Paper-Trade Runbook (60–90d gate)

**Start date:** 2026-04-20
**End-target window:** 60–90 calendar days from start
**Authority:** Round 8 dual-council canon (77-Round-8-Canon)

---

## 1. Configured sizing (engine-enforced)

`src/core/risk_manager.py::SYMBOL_RISK_CAP` clamps the effective risk per trade. Caller intents in `src/live/runner.py::SYMBOLS_CONFIG` and `src/live/engine_live.py::SYMBOLS_CONFIG` mirror these.

| Symbol | OANDA inst | Caller risk | Cap | Effective |
|---|---|---:|---:|---:|
| GC=F | XAU_USD | 0.50% | 0.50% | 0.50% |
| ^GDAXI | DE30_EUR | 0.25% | 0.25% | 0.25% |
| ^IXIC | NAS100_USD | 0.15% | 0.15% | 0.15% |
| GBPUSD=X | GBP_USD | 0.20% | 0.20% | 0.20% |
| USDJPY=X | USD_JPY | — | 0.00% | 0.00% (blocked) |

**Verification:** `tests/_r8_cap_binding_check.py` → `logs/round8/cap_binding_check.log` (13/13 PASS, 2026-04-20).

## 2. What is running

- **Hourly cron path:** `src.live.runner` — triggered from Task Scheduler at `xx:05` UTC. Each run processes all 4 symbols sequentially.
- **Continuous path:** `src.live.engine_live` — persistent process; polls OANDA stream, detects candle close, runs analysis. Uses same `analyze_sbrs_v2` as backtests.
- Both paths now use `fetch_live()` (retry + cache fallback) instead of bare `fetch()`.

## 3. Monitoring / falsifier tracking

- **Every fill** → `logs/paper/slip_reconciliation.jsonl` (expected_entry vs actual_fill).
- **Weekly** → `py scripts/weekly_falsifier_check.py` writes `knowledge-base/arbiters/logs/falsifier_YYYY-MM-DD.md`. Register once with:
  ```
  schtasks /Create /SC WEEKLY /D MON /TN "SBRS_WeeklyFalsifier" ^
          /TR "C:\…\Zeros Requiem\scripts\schedule_weekly_falsifier.bat" ^
          /ST 08:00 /F
  ```
- **Ad-hoc** → `py scripts/slip_reconcile.py --window-days 60` prints current realized/modeled ratio per symbol.

## 4. Exit/kill conditions (see 75-Pre-Registered-Falsifier-R8 for full text)

| Gate | Trigger | Action |
|---|---|---|
| F#1 | Realized mean slip > 1.25pt/side indices (100-fill window) | HALT that instrument; re-run BT/WF/MC |
| F#4 | USDJPY paper PF < 1.3 over any 50-fill window | Suspend USDJPY paper |
| F#5 | Gold Short PF < 1.0 cumulative | Rewrite Gold to long-only |

## 5. Live-ramp gate (end of paper window)

All 4 must hold before enabling live money:
1. 60–90d of paper fills logged, no F#1/F#4/F#5 trigger fired.
2. `py scripts/slip_reconcile.py --window-days 60` → all PASS.
3. `/arbiter-canon-audit` → CLAUDE.md still fresh vs logs.
4. User explicit approval citing this runbook.

## 6. Known data-fetch hardening (2026-04-20)

`src/data/oanda_fetcher.py` now retries 500/502/503/504/SSL/timeout with exponential backoff (1.5s → 12s, 4 attempts). On complete failure, `src/live/data_cache.py::fetch_live()` falls back to a local parquet cache of the last successful pull if ≤3h old. This removes the recurring Telegram "Failed to fetch data" alerts caused by OANDA 502/SSL EOF transients. See commit log for details.
