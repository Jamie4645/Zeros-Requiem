---
tags: [research, archive, experiment]
aliases: [SBRS 2.1, v2.1 Experiment]
related: [[47-SBRS-2.0-Upgrade]], [[48-Ablation-Study-Results]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **RETIRED (see root `CLAUDE.md`).** SBRS is fully retired — realistic-fill backtests found no
> edge on any instrument (PF 0.52–1.07). The v2.0-vs-v2.1 PF/PnL comparison below was measured on
> the pre-audit phantom-fill engine and is void; neither version has a demonstrated edge. Retained
> as historical record only. Current strategy: ZTT (`knowledge-base/89-ZTT-Rebuild.md`).

# SBRS 2.1 Experiment — Built and Removed

**Date:** 2026-04-05
**Status:** REMOVED (did not outperform v2.0)

---

## What It Was

SBRS 2.1 was an experimental strategy file (`src/regimes/sbrs_v2_1.py`) that attempted 5 additional improvements over v2.0:

1. **Limit-order entry at broken level** — Enter at the S/R level instead of candle close
2. **Structural stop-loss** — Use nearest swing level for SL instead of fixed ATR buffer
3. **Stale MA cross rejection** — Reject MA crosses that had subsequently reversed
4. **Counter-trend position size halved** — 50% size reduction for against-trend trades
5. **Squeeze SL at range boundary** — Place SL at consolidation range edges

---

## Why It Failed

On Gold 2Y data:
- v2.0: 108 trades, PF 1.27, +$1,751 walk-forward
- v2.1: 54 trades, PF 0.50, -$2,159 walk-forward

**Root causes:**
1. Limit-order fill check was too strict — required price to touch the exact level, rejecting many valid "close enough" retests
2. Trade count halved — compounded with stale MA rejection, too few opportunities remained
3. Structural SL sometimes too tight — small swing levels near entry created tiny SL distances and tiny profit targets

---

## Lesson Learned

The methodology document describes discretionary practices (limit orders, structural SL) that work with human judgment but don't translate cleanly to algorithmic execution on 1H bars. The algo benefits from "close enough" entries (candle close) and consistent ATR-based SL rather than structural levels that vary in distance.

> **Codifying discretionary edge requires adaptation, not literal translation.**

---

## Files Removed

- `src/regimes/sbrs_v2_1.py` — Deleted
- `tests/test_sbrs_v2_1.py` — Deleted
- All engine/CLI/walk-forward references — Cleaned

---

## Related

- [[47-SBRS-2.0-Upgrade]] — The strategy that won
- [[48-Ablation-Study-Results]] — The data-driven approach that succeeded
- [[00-MOC-Zeros-Requiem]]
