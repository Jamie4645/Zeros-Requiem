--
tags: [audit, gold, data-quality, round6, inconclusive]
aliases: [Gold Bar Audit, OANDA vs Yahoo Gold, D1 Audit]
related: [[00-MOC-Zeros-Requiem]], [[45-Data-Pipeline]], [[73-Round-5-Remediation-Log]]
---

# Gold OANDA vs Yahoo Bar Audit — Round 6 D1 (2026-04-18, INCONCLUSIVE)

> **Scope:** Round 5 item Y5 asked: did Yahoo Finance GC=F contain phantom 24/5 weekend bars that OANDA correctly omits? Or does OANDA have a historical gap? The original Gold 10Y canon used Yahoo; Round 2+ moved to OANDA. Any bar-count divergence could explain a portion of the PF change between eras.

## Method

Script: `tests/_d1_gold_bar_audit.py`. Intended to call `src.data.fetcher.fetch("GC=F", "1h", "10y")` against both sources via parameterisation, then diff the timestamp sets.

## Result — INCONCLUSIVE

**Both runs returned identical bar counts (11,785 vs 11,785) and identical swing ratio (1.00x).**

## Root Cause

`src/data/fetcher.py::fetch` routes `GC=F` through OANDA regardless of caller intent. There is no `--source=yahoo` override in the current fetcher implementation. The "Yahoo" branch in the D1 script silently fell through to OANDA.

Confirmed by inspection of `src/data/fetcher.py`:
- Gold symbols (`GC=F`, `XAUUSD`) map directly to OANDA XAU_USD via `SYMBOL_ROUTING`.
- The yfinance path is reserved for indices (`^GSPC`, `^IXIC`, `^GDAXI`) that have no OANDA mapping.
- No user-level override exists to force yfinance on a Gold symbol.

**Consequence:** We compared OANDA to OANDA. The original question (is Yahoo's bar stream different from OANDA's?) remains unresolved.

## What This Doesn't Change

Nothing about current portfolio verdicts. The Round 6 Gold canon (733 trades, PF 2.05, MC 2.24% PASS) is computed on **OANDA data**, not Yahoo. Every live and paper deployment flows through OANDA. The Yahoo data used in the original 10Y Gold backtest (2,252 trades, PF 1.97) is historical — not live-path.

## Why It Still Matters (marginally)

The Gold 2,252-trade canon from late-2025 sat on Yahoo. The current OANDA canon is 733 trades (filter-OFF) / 643 trades (filter-ON, earlier). That's a ~3× trade-count gap that has been attributed to (a) the session filter being ON during one era, (b) Yahoo's looser bar construction admitting more phantom candles, (c) SBRS v2.0 filter tightening. Without the Yahoo comparison we can't partition the gap.

**Magnitude of uncertainty:** small. The dollar figure of Gold edge has been repeatedly validated (MC 2.24%, Sharpe 1.43, PF 2.05, Max DD 11.44%). The phantom-bar question is about *bar completeness*, not *edge sign*.

## Round 7 Fix

Logged as `next-hypotheses.md` 2026-04-18 arbiter-data entry. Plan:
1. Add `--force-source=yahoo` / `force_source='yahoo'` parameter to `fetch()`.
2. Re-run `tests/_d1_gold_bar_audit.py` with `force_source='yahoo'` on the Yahoo branch.
3. Diff bar-timestamp sets; classify any gap as "OANDA missing", "Yahoo phantom", or "equivalent".
4. Document findings; update [[45-Data-Pipeline]] if fetcher behaviour changes.

## Reference

- Script: `tests/_d1_gold_bar_audit.py`
- Log: `logs/round6/gold_bar_audit.log`
- Fetcher routing: `src/data/fetcher.py::SYMBOL_ROUTING`
- Related: [[45-Data-Pipeline]] (fetcher architecture), [[73-Round-5-Remediation-Log]] (Round 6 phase D context)
