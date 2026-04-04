---
tags: [phase-0, bug-fix, live-runner, broker-closed, session-filter, breakeven]
aliases: [Phase 0, Runner Bug Fixes]
---

# Phase 0 — Live Runner Bug Fixes

> Critical fixes applied before any new infrastructure. 12 trades, 0 wins, 11 `broker_closed` exits with $0 PnL.

---

## Bug 1: `broker_closed` P&L Recording (CRITICAL)

**Problem:** When `sync_positions()` detects a trade closed on OANDA between hourly runs, the runner recorded `pnl = 0.0` and `exit_price = entry_price` instead of querying OANDA for the actual exit.

**Root Cause:** `runner.py:107` — hardcoded `pnl = 0.0` with comment "Broker already applied the P&L to balance".

**Fix:**
1. Added `get_closed_trade_details()` to `oanda_executor.py` — queries OANDA's trade endpoint for closed trades to get `realizedPL`, `averageClosePrice`, and closing transaction type
2. `sync_positions()` now enriches each closed trade dict with `_broker_exit_price`, `_broker_pnl`, `_broker_close_reason`
3. Runner maps OANDA close reasons to our exit types: `take_profit` → `tp`, `stop_loss` → `sl`, etc.

**Files Modified:**
- `src/live/oanda_executor.py` — added `get_closed_trade_details()`, updated `sync_positions()`
- `src/live/runner.py` — Step 2 sync logic rewritten

---

## Bug 2: Session Filter Bare `except: pass`

**Problem:** `runner.py:297-301` wrapped `is_session_blocked()` in `try/except: pass`, silently swallowing all errors.

**Fix:** Changed to `except Exception as e:` with logging. On error, entry is blocked (safe default) rather than silently allowed.

**File Modified:** `src/live/runner.py`

---

## Bug 3: Breakeven Stop Too Close to Entry

**Problem:** BE buffer of `0.1R` on Gold is ~$0.56-0.74, which is dangerously close to Gold's typical spread ($0.30-0.50). Trades 84 and 92 show `stop_moved_to_be: true` then `broker_closed` within 2 hours.

**Fix:** BE logic now queries current bid/ask spread via `get_current_price()` and adds 60% of spread as additional buffer to the BE stop level. This prevents immediate SL hits from spread.

**File Modified:** `src/live/runner.py` — breakeven section

---

## Verification Plan

1. Run the runner for 1 week on paper
2. Confirm closed trades show actual PnL values (not $0)
3. Confirm session filter blocks 16-20 GMT entries with log messages
4. Confirm BE stops account for spread (check logs for SL moved messages)
5. Compare `state/sbrs_state.json` P&L with OANDA account history

---

## Related

- [[00-MOC-Zeros-Requiem]]
- [[30-Tool-Live-Status]] — check runner health
- [[38-Phase-1-SQLite-Trade-Database]] — database for trade tracking
