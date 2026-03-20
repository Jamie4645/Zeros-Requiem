---
tags: [MOC, index, zeros-requiem]
aliases: [Home, Dashboard, Index]
---

# Zeros Requiem — Map of Content

> *"An edge is nothing more than an indication of a higher probability of one thing happening over another."* — Mark Douglas

---

## Quick Access

| Action | Link |
|--------|------|
| Check live bot | [[30-Tool-Live-Status]] |
| Run a backtest | [[31-Tool-Backtest]] |
| Review risk rules | [[16-Risk-Management-Elite-System]] |
| Current portfolio | [[29-P5-P7-P8-OANDA-Portfolio]] |
| SBRS strategy spec | [[CLAUDE]] |

---

## Strategy Frameworks

### SBRS 1.1 — Sovereign Breakout Retest Strategy (Live)
*Codification of 3-4 years of profitable discretionary Gold trading.*

- [[CLAUDE]] — Master strategy spec, parameters, entry/exit logic
- [[16-Risk-Management-Elite-System]] — 5-layer risk management
- [[25-Walk-Forward-Full-Results]] — Walk-forward validation results
- [[28-P4-Monte-Carlo]] — Monte Carlo simulation & validation

### SCAF 2.0 — Sovereign Cross-Asset Framework (Backtesting)
*Regime-aware multi-asset framework: Sweep + Displacement + FVG.*

- [[17-SCAF-2.0-Architecture]] — Architecture & execution protocol
- [[18-SCAF-Session-Results]] — Initial build session results
- [[19-Priority-1-Signal-Generation]] — Signal generation improvements
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers (Core/Satellite/Dropped)

---

## Development Timeline

### Foundation
- [[05-Deployment-Options-Platform-Comparison]] — Where to run the algo
- [[07-Guide-Python-Broker-APIs]] — Python + broker API integration
- [[08-Guide-QuantConnect]] — QuantConnect platform evaluation

### SCAF 2.0 Build
- [[17-SCAF-2.0-Architecture]] — Framework design
- [[18-SCAF-Session-Results]] — Build results
- [[19-Priority-1-Signal-Generation]] — P1: More signals (18 → 800+ trades/year)
- [[20-Priority-2-Gold-Daily-Fix]] — P2: Fix Gold Daily (0 trades bug)
- [[21-Priority-3-4-New-Pairs]] — P3-P4: Add GBP/USD, USD/JPY, ETH

### Optimisation & Validation
- [[22-Priority-5-6-Metrics-WalkForward]] — P5-P6: Walk-forward + elite metrics
- [[23-Optimisation-Weak-Areas]] — Optimisation pass: weak areas
- [[24-Optimisation-Round-2]] — Optimisation round 2: N1-N4
- [[25-Walk-Forward-Full-Results]] — Full walk-forward results (all symbols)

### Production Hardening
- [[26-P1-Gold-BE-Stop-Fix]] — Breakeven stop fix (Sharpe 0.69 → 1.49)
- [[27-P3-P6-Forex-Fixes]] — USD/JPY fix + AUD/USD rejection
- [[28-P4-Monte-Carlo]] — Monte Carlo validation (10K sims)
- [[29-P5-P7-P8-OANDA-Portfolio]] — OANDA integration + portfolio tiers

---

## Claude Code Tooling

### Skills (Slash Commands)
- [[31-Tool-Backtest]] — `/backtest` — Run & report against elite benchmarks
- [[30-Tool-Live-Status]] — `/live-status` — SBRS runner health check

### Automation
- [[32-Tool-Auto-Test-Hook]] — PostToolUse hook: auto-runs tests after code changes
- [[33-Tool-Protected-Files-Hook]] — PreToolUse hook: blocks edits to sacred files
- [[34-Tool-Sequential-Thinking-MCP]] — MCP server for complex debugging

### Workflow
- [[35-Tool-GSD2]] — GSD-2: structured autonomous development
- [[36-Tool-CLAUDE-MD-Autoload]] — CLAUDE.md auto-loading configuration

---

## Architecture Quick Reference

```
Zeros Requiem/
├── CLAUDE.md              ← Strategy spec (auto-loaded)
├── main.py                ← CLI entry point
├── src/
│   ├── core/              ← Engine, risk, walk-forward, Monte Carlo
│   ├── regimes/           ← SBRS Gold, SCAF Gold/Forex/Crypto
│   ├── indicators/        ← WMA, SMMA, ATR, swing detection
│   ├── execution/         ← Sweep, displacement, FVG, entries
│   ├── data/              ← OANDA + Yahoo fetchers
│   └── live/              ← Runner, executor, state, alerts
├── knowledge-base/        ← This Obsidian vault
├── state/                 ← Live trading state (JSON)
├── logs/                  ← Runner logs
└── tests/                 ← Backtest & validation scripts
```

---

## Elite Benchmarks (Current vs Target)

| Metric | Gold 4H (SCAF) | Gold 1H (SBRS Live) | Target |
|--------|----------------|---------------------|--------|
| Sharpe | 1.49 | Live testing | ≥1.50 |
| Profit Factor | 1.71 | Live testing | ≥1.50 |
| Max Drawdown | 3.14% | ~5.7% from peak | ≤15% |
| Walk-Forward | 50% (10Y) | N/A (live) | ≥75% |
| Monte Carlo | 0.28% prob 20%DD | N/A | <5% |
| Trades | 624 (10Y) | 12 (1 month) | ≥500 |

---

*Last updated: 2026-03-20*
