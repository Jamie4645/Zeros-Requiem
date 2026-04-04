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

## Strategy: SBRS 1.1 — Sovereign Breakout Retest Strategy

*Codification of 3-4 years of profitable discretionary Gold trading.*

### Core Documentation
- [[CLAUDE]] — Master strategy spec, parameters, entry/exit logic
- [[46-SBRS-Parameters-Reference]] — All parameters with test ranges
- [[16-Risk-Management-Elite-System]] — 5-layer risk management
- [[25-Walk-Forward-Full-Results]] — Walk-forward validation results
- [[28-P4-Monte-Carlo]] — Monte Carlo simulation & validation
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers
- [[44-Live-Runner-Architecture]] — Runner, executor, state, alerts
- [[45-Data-Pipeline]] — OANDA → IBKR → Yahoo routing

### Validation & Optimisation
- [[22-Priority-5-6-Metrics-WalkForward]] — Walk-forward + elite metrics
- [[23-Optimisation-Weak-Areas]] — Optimisation pass: weak areas
- [[24-Optimisation-Round-2]] — Optimisation round 2
- [[25-Walk-Forward-Full-Results]] — Full walk-forward results
- [[26-P1-Gold-BE-Stop-Fix]] — Breakeven stop fix (Sharpe 0.69 → 1.49)

---

## Infrastructure & Tooling (2026-03)

### Phase Roadmap
- [[37-Phase-0-Live-Runner-Bug-Fixes]] — broker_closed bug, session filter, BE stop
- [[38-Phase-1-SQLite-Trade-Database]] — SQLite MCP + trade database + /trades skill
- [[39-Phase-2-IBKR-Index-Data]] — IBKR data fetcher for 10Y index walk-forward
- [[40-Phase-3-Pytest-Migration]] — print-based tests → proper pytest
- [[41-Phase-4-VectorBT-Validation]] — engine cross-validation vs VectorBT
- [[42-Phase-5-Visualization-Refactor]] — consolidated charting + /chart skill
- [[43-Phase-6-SCAF-Removal]] — Removed SCAF, consolidated to SBRS-only codebase

### Skills (Slash Commands)
- [[31-Tool-Backtest]] — `/backtest` — Run & report against elite benchmarks
- [[30-Tool-Live-Status]] — `/live-status` — SBRS runner health check
- [[38-Phase-1-SQLite-Trade-Database]] — `/trades` — Query trade history from SQLite
- [[42-Phase-5-Visualization-Refactor]] — `/chart` — Generate analysis charts

### Automation
- [[32-Tool-Auto-Test-Hook]] — PostToolUse hook: auto-runs tests after code changes
- [[33-Tool-Protected-Files-Hook]] — PreToolUse hook: blocks edits to sacred files
- [[34-Tool-Sequential-Thinking-MCP]] — Sequential Thinking MCP server setup
- [[35-Tool-GSD2]] — GSD2 task management integration
- [[36-Tool-CLAUDE-MD-Autoload]] — How CLAUDE.md auto-loads into sessions

---

## Strategy Extraction Pipeline

*Multi-agent system: Claude Code reads trading book PDFs, extracts strategies, cross-compares across books, outputs backtestable Python.*

- [[Pipeline Documentation]] — How the pipeline works, how to run it
- [[Strategy Comparison Overview]] — Hub note for all extracted strategies
- [[Master Report]] — Auto-generated report after processing books
- [[Pipeline Instructions v2]] — Full original instructions

---

## Reference Guides

- [[05-Deployment-Options-Platform-Comparison]] — Broker/platform comparison (VPS, cloud, local)
- [[07-Guide-Python-Broker-APIs]] — Python API guide: OANDA, IBKR, Alpaca
- [[08-Guide-QuantConnect]] — QuantConnect platform overview

---

## Archive — SCAF Era (Historical, Pre-Phase 6)

*These notes document work done on the old SCAF 2.0 framework, which was removed in [[43-Phase-6-SCAF-Removal]]. Kept for context.*

- [[19-Priority-1-Signal-Generation]] — Signal generation improvements (SCAF era)
- [[20-Priority-2-Gold-Daily-Fix]] — Gold daily FVG fix (SCAF era)
- [[21-Priority-3-4-New-Pairs]] — Adding GBP/USD, USD/JPY, ETH (SCAF era)
- [[27-P3-P6-Forex-Fixes]] — Forex regime fixes (SCAF era)

---

## Architecture

```
Zeros Requiem/
├── CLAUDE.md              ← Strategy spec (auto-loaded)
├── main.py                ← CLI entry point
├── src/
│   ├── core/              ← Engine, risk, walk-forward, Monte Carlo
│   ├── regimes/           ← SBRS strategy implementation
│   ├── indicators/        ← WMA, SMMA, ATR, swing detection
│   ├── execution/         ← TradeSetup dataclass
│   ├── data/              ← OANDA + IBKR + Yahoo fetchers
│   ├── live/              ← Runner, executor, state, alerts
│   └── visualization/     ← Charts module
├── strategy_pipeline/     ← Book → Strategy extraction pipeline
├── knowledge-base/        ← This Obsidian vault
├── state/                 ← Live trading state (JSON)
├── data/                  ← SQLite DB + IBKR cache
├── logs/                  ← Runner logs
└── tests/                 ← Pytest suite
```

---

## Elite Benchmarks (Current vs Target)

| Metric | Gold 1H (SBRS Live) | Target |
|--------|---------------------|--------|
| Sharpe | 0.90 | ≥1.50 |
| Profit Factor | 1.26 | ≥1.50 |
| Max Drawdown | 11.9% | ≤15% |
| Walk-Forward | 75% (10Y) | ≥75% |
| Trades | 1,152 (10Y) | ≥500 |

---

*Last updated: 2026-03-20*
