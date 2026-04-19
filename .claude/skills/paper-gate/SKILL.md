---
name: paper-gate
description: 10-point deployment readiness checklist before paper or live trading a strategy. Use when the user says "ready for paper", "go live", "deployment check", "paper-trade checklist", or "deploy strategy".
user_invocable: true
argument-hint: [symbol] [interval]
allowed-tools: Read, Grep, Bash(py:*), Bash(python:*)
---

# /paper-gate — Paper/Live Deployment Readiness Gate

Enforces CLAUDE.md elite benchmarks before any deployment. NO instrument passes this without all 10 boxes ticked.

## Protocol

### Step 1 — Parse args
| Arg | Default |
|---|---|
| Symbol | ask if missing |
| Interval | `1h` |

### Step 2 — Evidence gathering (read, don't recompute)
Read in order — STOP if any file is missing and flag it:
1. `knowledge-base/25-Walk-Forward-Full-Results.md` — WF consistency
2. `knowledge-base/28-P4-Monte-Carlo.md` — MC prob(20% DD)
3. Most recent backtest output (ask user for filename or recompute via `/backtest`)
4. `src/core/risk_manager.py` — is slippage modelled?
5. `state/sbrs_state_<SYMBOL>.json` — if exists, runner is already deployed

### Step 3 — 10-point checklist
Score each; require **10/10** for live, **≥8/10** for paper (with the gaps documented):

```
═══════════════════════════════════════════════════════
  DEPLOYMENT GATE: <Symbol> <Interval>
═══════════════════════════════════════════════════════
  1.  500+ trades on full backtest               ✅/❌
  2.  5Y+ historical data available              ✅/❌
  3.  Walk-forward ≥75% consistency (≥6/8)       ✅/❌
  4.  Sharpe ≥1.50 (WF average)                  ✅/❌
  5.  Profit Factor ≥1.50 (WF average)           ✅/❌
  6.  Max DD ≤15% (backtest)                     ✅/❌
  7.  Monte Carlo: Prob(20% DD) <5%              ✅/❌
  8.  Slippage (1.5 pips) modelled               ✅/❌
  9.  Risk sized per MC recommendation           ✅/❌
  10. Data source approved (OANDA/IBKR/Binance)  ✅/❌

  SCORE: X/10
  VERDICT: 10/10 = GO LIVE | 8–9 = PAPER ONLY | <8 = NOT READY
═══════════════════════════════════════════════════════
```

### Step 4 — Risk sizing recommendation
Per CLAUDE.md + Monte Carlo precedent:
- **Account $10k–$50k, elite tier**: 0.3–0.5% per trade
- **MC shows 1% risk breaches 5% DD threshold** → halve to 0.5%
- **MC shows 0.5% still breaches** → halve to 0.25%
- **Paper-trade sizing**: one tier tighter than proposed live sizing

### Step 5 — Go/no-go recommendation
**If 10/10:**
```
✅ APPROVED for live deployment at <RISK>% per trade.

Next steps:
  1. Start runner: py -m src.live.runner --symbol <SYM> --risk <RISK>
  2. Paper trade first for 60–90 days
  3. Monitor with /live-status daily
  4. After 60 days, compare live win rate vs backtest WR (±10% tolerance)
```

**If 8–9/10:**
```
⚠️ PAPER ONLY at <RISK>% (halved from live-target).

Gaps to close before going live:
  [List the failing items]

Monitor paper for 90 days THEN re-run /paper-gate.
```

**If <8/10:**
```
❌ NOT READY for any deployment.

Required before retry:
  [List all failing items]
```

### Step 6 — Known precedent (don't repeat past mistakes)
- **Gold 1H SBRS 2.0**: passed 10/10, MC recommended 0.5% not 1% → live at 0.5%
- **DAX/NASDAQ 1H**: 88% WF, passed 9/10, MC pending → paper at 0.25%
- **GBP/USD 1H**: 62% WF, W7 collapse → NOT READY until W7 investigated
- **S&P 500, AUD/USD**: TIER 4, REJECTED

## Remember
> "Don't claim validation without walk-forward. Don't report 1Y results as annual return."

Deployment without full validation is how accounts die.
