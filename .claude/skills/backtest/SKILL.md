---
description: Run a backtest and report results against elite benchmarks. Use when the user says "backtest", "run test", "validate strategy", or "check performance".
user_invocable: true
---

# /backtest — Run & Report Against Elite Benchmarks

## Instructions

When invoked, follow this exact protocol:

### Step 1: Determine What to Test
Ask the user (if not specified) which configuration:
- **Symbol:** GC=F (Gold), GBPUSD, USDJPY, BTC-USD, ETH-USD, SPY, NAS100, DAX
- **Interval:** 1h, 4h, 1d
- **Period:** 1y, 2y, 5y, 10y (prefer longest available)
- **Framework:** SBRS or SCAF (default SBRS for Gold 1H, SCAF for everything else)

### Step 2: Run the Backtest
```bash
cd "C:/Users/jamie/OneDrive/Documents/Jamie VS Code/Git/Zeros Requiem"
python -m tests.quick_test  # or specific test file
```

### Step 3: Report Against Elite Benchmarks

Present results in this EXACT format:

```
═══════════════════════════════════════════════════════
  BACKTEST REPORT: [Symbol] [Interval] [Period]
  Framework: [SBRS/SCAF] | Date: [today]
═══════════════════════════════════════════════════════

  METRIC              RESULT      TARGET     STATUS
  ─────────────────────────────────────────────────
  Sharpe Ratio        X.XX        ≥1.50      ✅/❌
  Profit Factor       X.XX        ≥1.50      ✅/❌
  Win Rate            XX.X%       35-65%     ✅/⚠️
  Max Drawdown        X.X%        ≤15%       ✅/❌
  Expectancy/Trade    $XX.XX      >$0        ✅/❌
  Total Trades        XXX         ≥500       ✅/❌
  Annual Return       XX.X%       ≥20%       ✅/❌

  WALK-FORWARD (if available):
  Consistency         X/8         ≥6/8       ✅/❌
  Edge Slope          +/-$XX/win  positive   ✅/❌

  OVERALL SCORE: X/7 benchmarks met
═══════════════════════════════════════════════════════
```

### Step 4: Red Flag Check
Flag and STOP if any of these appear:
- Win Rate >70% → likely bug or overfit
- Sharpe >3.0 on walk-forward → too good to be true
- 100% consistency across all windows → inspect code
- Profit Factor >3.0 average → check for data leakage

### Step 5: Honest Assessment
- Compare to previous known results (check knowledge-base/)
- Note what improved and what degraded
- If results are worse, say so clearly
- Recommend next action based on results

### Remember
> "Judge success by the next 100 trades, not the next 1 trade." — Mark Douglas
