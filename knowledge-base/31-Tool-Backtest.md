--
tags: [tool, skill, backtesting, validation]
aliases: [backtest, run-backtest]
related: [[CLAUDE]], [[25-Walk-Forward-Full-Results]], [[28-P4-Monte-Carlo]], [[22-Priority-5-6-Metrics-WalkForward]]
---

# /backtest — Run & Report Against Elite Benchmarks

## What It Does

A custom Claude Code **skill** (slash command) that runs a backtest and presents results in a standardised format against the [[CLAUDE|elite benchmarks]]. Ensures every backtest is reported consistently and honestly — no cherry-picking, no sugarcoating.

## How It Works

When you type `/backtest`, Claude will:

1. **Ask what to test** (if not specified) — symbol, interval, period, framework (SBRS vs SCAF)
2. **Run the backtest** — executes the appropriate test harness
3. **Compare against 7 elite benchmarks** — Sharpe ≥1.5, PF ≥1.5, WR 35-65%, DD ≤15%, Expectancy >0, Trades ≥500, Annual Return ≥20%
4. **Check for red flags** — WR >70%, Sharpe >3.0, PF >3.0, 100% consistency (all indicate bugs/overfit)
5. **Give honest assessment** — compares to previous known results, notes improvements AND degradations

## The Report Format

```
═══════════════════════════════════════════════════════
  BACKTEST REPORT: Gold 1H 10Y
  Framework: SBRS | Date: 2026-03-20
═══════════════════════════════════════════════════════

  METRIC              RESULT      TARGET     STATUS
  ─────────────────────────────────────────────────
  Sharpe Ratio        0.90        ≥1.50      ❌
  Profit Factor       1.26        ≥1.50      ❌
  Win Rate            43.4%       35-65%     ✅
  Max Drawdown        11.9%       ≤15%       ✅
  ...
```

## Red Flag Triggers

These results cause the skill to **STOP and investigate** before continuing:

| Flag | Threshold | Likely Cause |
|------|-----------|-------------|
| Win Rate >70% | Bug or overfit | Check entry logic, data leakage |
| Sharpe >3.0 | Too good to be true | Inspect walk-forward windows |
| PF >3.0 | Data leakage | Verify out-of-sample separation |
| 100% WF consistency | Code error | All windows shouldn't be identical |

## Location

```
.claude/skills/backtest/SKILL.md
```

## Usage

```
/backtest                          # Interactive — asks what to test
/backtest Gold 1H 10Y SBRS        # Direct specification
```

## Why This Exists

From [[CLAUDE|the strategy spec]]:
> *"Don't cherry-pick best windows. Don't hide losing periods. Don't report 1-year results as 'annual return'."*

This skill enforces that discipline programmatically. Every backtest gets the same rigorous treatment.

## Related

- [[CLAUDE]] — Elite benchmark definitions and strategy spec
- [[25-Walk-Forward-Full-Results]] — Historical walk-forward results to compare against
- [[28-P4-Monte-Carlo]] — Monte Carlo validation methodology
- [[22-Priority-5-6-Metrics-WalkForward]] — How walk-forward was implemented
- [[16-Risk-Management-Elite-System]] — Risk rules that constrain results

---

*Installed: 2026-03-20*
