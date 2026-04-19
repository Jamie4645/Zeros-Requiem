# Audit remediation (April 2026)

## Scope

Batch remediation for correctness, live safety, and data integrity: direction normalization, causal 4H context (no future 1H in backtests), broker sync, fetchers, process lock, atomic state/cache writes.

## Changes (summary)

| Area | Change |
|------|--------|
| **Risk** | `normalize_direction()` in `src/core/risk_manager.py`; `apply_slippage`, `can_trade`, and direction-concentration use normalized `'long'` / `'short'` (supports `TradeDirection` enum). |
| **4H context** | `causal_4h_trend_series()` in `src/regimes/sbrs_v2.py`: O(n) causal trend; `drop_incomplete_last_4h_bar()` strips partial 4H buckets. `analyze_sbrs_v2` / `analyze_gold_sbrs` use causal trend; SBRS 1.1 4H MA cross uses resample on `df.iloc[:i+1]` + drop incomplete. |
| **Live** | `sync_positions`: only close locally when OANDA returns closed-trade details; retries in `get_closed_trade_details`. `process_lock.py`: single instance for `runner` + `engine_live`. |
| **State** | `save_state`: atomic `mkstemp` + `os.replace`. |
| **OANDA fetch** | On `RequestException` after partial candles: raise (no silent truncated history). |
| **Binance** | UTC-consistent timestamps; partial-fetch raises; CSV cache via temp + `os.replace`; cache freshness uses `pd.Timestamp.now(tz='UTC')`. |
| **Tests** | `tests/test_remediation.py`: direction, incomplete 4H drop, causal parity (fast vs slice reference). |

## Validation run

- **Full suite (2026-04-09):** `py -m pytest tests/ -q` — **85 passed**, **13 skipped**, ~71s. Skips: vectorbt (11), portfolio + indices integration scripts (2). Warnings: `oanda_fetcher` `utcnow` deprecation (cosmetic).
- **Subset (earlier remediation pass):** same core modules without `test_portfolio`/`test_indices` import fix — **81 passed**, 11 skipped (~14s). Not directly comparable: fewer collection skips, fewer test files.
- **Pre-remediation git baseline:** last commit `e3c6623` only had 11 files under `tests/` (no `test_remediation`, `test_sbrs_v2`, `test_smart_money`, `test_bollinger`, etc.); a true before/after count needs a dedicated branch or stash of the old tree.
- Spot backtest: `py main.py --symbol GC=F --interval 1h --period 3mo --strategy sbrs_v2` — completed successfully.

### Test harness fixes (for full `pytest tests/`)

- `tests/test_portfolio.py`: module-level `pytest.skip(..., allow_module_level=True)` unless `__main__` so OANDA is not hit on import; run manually: `py tests/test_portfolio.py`.
- `tests/test_indices.py`: body moved to `main()`; `test_indices_integration_manual_only` skips; run `py tests/test_indices.py`.
- `tests/test_gold_backtest.py`: PF assertion allows `profit_factor == 0` when the 6mo sample has no winning trades (valid after causal 4H).

## Follow-up

- Re-run full **walk-forward** / **Monte Carlo** on Gold (and key indices) when you want refreshed benchmark tables after causal 4H (metrics may shift vs pre-fix lookahead).
- `tests/test_portfolio.py` / `tests/test_indices.py` perform module-level OANDA fetch; run only when online and acceptable.

## Links

- [[00-MOC-Zeros-Requiem]]
- SBRS spec: `docs/sbrs_strategy_spec.md`
