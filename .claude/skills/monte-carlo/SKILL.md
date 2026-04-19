---
name: monte-carlo
description: Run 10,000-simulation Monte Carlo on a strategy's trade distribution, report drawdown/ruin probabilities, and recommend risk %. Use when the user says "monte carlo", "mc", "mc sim", "ruin probability", "tail risk", or "dd probability".
user_invocable: true
argument-hint: [symbol] [interval] [period]
allowed-tools: Bash(py main.py --monte-carlo:*), Bash(python main.py --monte-carlo:*), Read
---

# /monte-carlo — Tail-Risk Validation

Wraps `main.py --monte-carlo`. Resamples actual trade PnLs (with replacement) across 10k synthetic paths. Answers: *"Given my trade distribution, what's the probability of a catastrophic drawdown?"*

## Protocol

### Step 1 — Parse args (or ask)
| Arg | Default |
|---|---|
| Symbol | `GC=F` |
| Interval | `1h` |
| Period | `10y` (use longest available for the symbol — crypto max 2y) |
| Strategy | `sbrs_v2` |

### Step 2 — Run (single shell call)
```bash
py main.py --symbol <SYMBOL> --interval <INT> --period <PERIOD> --strategy sbrs_v2 --monte-carlo
```

### Step 3 — Report
```
═══════════════════════════════════════════════════════
  MONTE CARLO: <Symbol> | 10,000 sims
═══════════════════════════════════════════════════════
  DRAWDOWN DISTRIBUTION
  Median Max DD        X.X%
  P95 Max DD           X.X%
  P99 Max DD           X.X%
  Prob of 15% DD       X.X%    <5% target    ✅/❌
  Prob of 20% DD       X.X%    <5% ELITE     ✅/❌
  Prob of 30% DD       X.X%    <1% target    ✅/❌
  Prob of 50% DD       X.X%    ~0% target    ✅/❌

  PNL DISTRIBUTION
  Median Final PnL     $X,XXX
  P5 (worst case)      $X,XXX
  Prob Profitable      XX.X%   ≥90% target   ✅/❌

  STREAKS
  Median Max Losers    X in a row
  P95 Max Losers       X in a row            ← size SL buffer for this

  RISK RECOMMENDATION
  If Prob(20% DD) > 5% at 1.0% risk → recommend 0.5%
  If Prob(20% DD) > 5% at 0.5% risk → recommend 0.25%
═══════════════════════════════════════════════════════
```

### Step 4 — Verdict
- **Elite pass**: Prob(20% DD) <5% AND Prob(50% DD) <1% → ready for live
- **Conditional pass**: reduce risk % until Prob(20% DD) drops <5%
- **Fail**: Prob(30% DD) >10% at any risk → strategy is fragile, reject

### Known precedent
Gold v2.0 MC at 1% risk came back with Prob(20% DD) borderline → recommended **0.5% live risk**. Use this as a sanity anchor for other assets.

## Remember
MC tells you tail risk on the *trade distribution you already have*. It does NOT predict regime change. Combine with `/walk-forward` for full validation.
