---
name: walk-forward
description: Run 8-window walk-forward validation on a strategy and report consistency vs 75% elite threshold. Use when the user says "walk-forward", "wf", "wf test", "validate consistency", "check edge stability", or "test windows".
user_invocable: true
argument-hint: [symbol] [interval] [windows] [strategy]
allowed-tools: Bash(py main.py --walk-forward:*), Bash(python main.py --walk-forward:*), Read
---

# /walk-forward — Walk-Forward Validation

Wraps `main.py --walk-forward`. Sequential non-overlapping windows, no optimisation per window.

## Protocol

### Step 1 — Parse args (or ask if missing)
| Arg | Default | Options |
|---|---|---|
| Symbol | `GC=F` | `GC=F`, `^GDAXI`, `^IXIC`, `GBPUSD=X`, `USDJPY=X`, `EURUSD=X`, `BTC-USD`, `ETH-USD` |
| Interval | `1h` | `1h`, `4h` |
| Windows | `8` | `4`–`10` |
| Strategy | `sbrs_v2` | `sbrs_v1`, `sbrs_v2` |

### Step 2 — Run (token-efficient — one shell call, stdout only)
```bash
py main.py --walk-forward <SYMBOL> --interval <INTERVAL> --windows <N> --strategy <STRAT>
```
Capture the per-window table from stdout. Do NOT re-run; do NOT pull source files unless the run fails.

### Step 3 — Report
Present the per-window table verbatim from stdout, then an aggregate summary:

```
═══════════════════════════════════════════════════════
  WALK-FORWARD: <Symbol> <Interval> | <Strategy>
═══════════════════════════════════════════════════════
  Consistency       X/N     ≥6/8       ✅/❌
  Avg Sharpe        X.XX    ≥1.50      ✅/❌
  Avg Profit Factor X.XX    ≥1.50      ✅/❌
  Edge Slope        +/-$X   positive   ✅/⚠️
  Worst Window PnL  $X      
  Best Window PnL   $X      
═══════════════════════════════════════════════════════
  VERDICT: TIER 1 (validated) / TIER 2 (promising) / TIER 3/4
```

### Step 4 — Red-flag checks (STOP if any trigger)
- Consistency = 100% → inspect for data leakage
- Avg Sharpe > 3.0 → too good, methodology suspect
- Window 1 best, Window N worst → edge decaying, serious
- <500 total trades across all windows → sample too small

### Step 5 — Recommendation
- **≥75% consistency**: eligible for paper trading via `/paper-gate`
- **62–74%**: identify failing window(s); recommend `bug-hunter` sub-agent or `/gsd forensics`
- **<62%**: no edge — reject the instrument (see CLAUDE.md Tier 4 rule)

## Remember
> "Judge success by the next 100 trades, not the next 1 trade." — Mark Douglas

NEVER re-tune parameters per window to hit 75%. That's overfitting and violates CLAUDE.md.
