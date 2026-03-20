---
description: Check SBRS live trading status, health, and recent trade outcomes. Use when the user says "live status", "check runner", "how's the bot", "trade status", or "SBRS status".
user_invocable: true
---

# /live-status — SBRS Live Runner Health Check

## Instructions

When invoked, perform these checks in order:

### Step 1: Read Current State
Read `state/sbrs_state.json` and extract:
- Current capital vs peak equity (drawdown %)
- Open trades (direction, entry, unrealized P&L)
- Pending setups (direction, level, bars waiting)
- Last run time (is the runner still active?)

### Step 2: Read Recent Logs
Read the latest log file in `logs/` (most recent month). Check for:
- ERROR entries (data fetch failures, broker errors)
- Runner frequency (should be ~1x per hour on the hour)
- Any anomalies (broker_closed exits, unexpected states)

### Step 3: Trade History Analysis
From trade_history in state file:
- Total trades, wins, losses
- Win rate
- Average P&L per trade
- Count of each exit_reason (broker_closed, ma_cross, stop_loss, take_profit, etc.)
- Any concerning patterns

### Step 4: Present Report

```
═══════════════════════════════════════════════════════
  SBRS LIVE STATUS — [date/time]
═══════════════════════════════════════════════════════

  ACCOUNT
  Capital:     $XX,XXX.XX
  Peak:        $XX,XXX.XX
  Drawdown:    X.X% from peak
  Daily P&L:   $XX.XX

  POSITIONS
  Open:        X trades
  Pending:     X setups waiting for retest

  RUNNER HEALTH
  Last Run:    [timestamp] ([X minutes ago])
  Status:      ✅ Active / ⚠️ Stale / ❌ Dead
  Errors:      X in last 24h

  TRADE HISTORY (lifetime)
  Total:       XX trades
  Wins:        XX (XX.X%)
  Losses:      XX
  Avg P&L:     $XX.XX/trade

  EXIT REASONS
  take_profit:     XX
  stop_loss:       XX
  ma_cross:        XX
  broker_closed:   XX  ← FLAG IF >0
  max_hold:        XX

  ALERTS
  [List any issues: broker_closed pattern, runner gaps,
   capital discrepancies, stale pending setups]
═══════════════════════════════════════════════════════
```

### Step 5: Recommendations
Based on findings, recommend:
- Whether to continue, pause, or investigate
- Any bugs that need fixing (especially broker_closed exits)
- Whether parameters need review
