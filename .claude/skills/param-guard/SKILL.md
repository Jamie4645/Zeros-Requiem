---
name: param-guard
description: Sacred-parameter change gate. Invoke BEFORE editing WMA_PERIOD, SMMA_PERIOD, SWING_LOOKBACK, MIN_RR, RETEST_TOLERANCE_ATR, or any SBRS constant. Use when the user says "change parameter", "tune", "optimise", "adjust WMA", or attempts param edits.
user_invocable: true
argument-hint: [param_name] [proposed_value]
allowed-tools: Read, Grep
---

# /param-guard — Sacred Parameter Change Gate

Enforces CLAUDE.md's "If I catch you optimizing WMA_PERIOD, SMMA_PERIOD, or SWING_LOOKBACK, we have a problem."

## When to Invoke
BEFORE any `Edit` or `Write` that touches:
- `src/regimes/sbrs_v2.py` — core strategy file
- `src/regimes/sbrs_gold.py` — legacy strategy file
- Any file defining `WMA_PERIOD`, `SMMA_PERIOD`, `SWING_LOOKBACK`, `MIN_RR`, `RETEST_TOLERANCE_ATR`, `ATR_PERIOD`, `SL_BUFFER_ATR`, `BE_TRIGGER_R`, `MAX_HOLD_BARS`, `SWING_WINDOW`, `MAX_RETEST_WAIT`, `MA_CROSS_LOOKBACK`, `CONFLUENCE_SCORE_*`

## Protocol

### Step 1 — Classify the parameter

| Tier | Parameters | Rule |
|---|---|---|
| **SACRED** | `WMA_PERIOD=9`, `SMMA_PERIOD=7`, `SWING_LOOKBACK=20`, `SWING_WINDOW=3`, `MIN_RR=3.0`, `RETEST_TOLERANCE_ATR=0.5` | **HARD STOP**. Require explicit, written user approval. Quote the CLAUDE.md warning verbatim. |
| **TUNABLE (±20%)** | `ATR_PERIOD=14` (12–16), `MAX_RETEST_WAIT=10` (8–12), `SL_BUFFER_ATR=0.3` (0.24–0.36), `BE_TRIGGER_R=1.5` (1.3–1.7), `MAX_HOLD_BARS=40` (30–50), `MA_CROSS_LOOKBACK=10` (8–12) | Verify proposed value is within ±20% of default. If outside, treat as SACRED. |
| **CONFLUENCE SCORES** | `CONFLUENCE_SCORE_FVG`, `CONFLUENCE_SCORE_LIQUIDITY`, `CONFLUENCE_SCORE_MA`, `CONFLUENCE_SCORE_LEVEL` | Ablation-validated. Require user confirmation + re-run `/ablation` after change. |

### Step 2 — Check current value
```bash
# Locate definition
```
Use Grep to confirm the current value matches the CLAUDE.md baseline. If it doesn't, flag drift before proceeding.

### Step 3 — Decision tree

**If SACRED and no explicit user approval:**
```
🛑 STOP — Sacred parameter change blocked.

<PARAM> is a SACRED parameter locked by CLAUDE.md:
  "These parameters come from real discretionary trading. They are SACRED."
  "If I catch you optimizing WMA_PERIOD, SMMA_PERIOD, or SWING_LOOKBACK,
   we have a problem."

To proceed, the user must:
  1. Explicitly say "change <PARAM> to <VALUE>" (not implied, not inferred)
  2. State the reason (what behaviour is this trying to fix?)
  3. Commit to re-running full validation: /walk-forward + /monte-carlo + /ablation

Do you want to proceed?
```

**If TUNABLE within ±20%:**
```
✅ ALLOWED — <PARAM> <OLD> → <NEW> is within ±20% range.

Post-change checklist:
  [ ] Re-run /backtest on Gold 1H 10Y
  [ ] If Sharpe or PF drops >10%, revert
  [ ] Update knowledge-base/46-SBRS-Parameters-Reference.md
```

**If TUNABLE but outside ±20%:**
Treat as SACRED — hard stop.

### Step 4 — Record decision
After approval, remind the user to update:
- `knowledge-base/46-SBRS-Parameters-Reference.md`
- Commit message prefix: `[SBRS]` or `[PARAMS]`

## The Philosophy
> "Your job is to CODIFY discretionary edge, NOT invent new strategies."

Parameter optimisation ≠ strategy improvement. It's the fastest path to overfitting.
