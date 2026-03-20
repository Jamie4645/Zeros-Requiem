---
tags: [core, SBRS, strategy-spec, sacred-parameters, MOC]
aliases: [Strategy Spec, SBRS Spec, Sacred Parameters, Master Spec]
related: [[00-MOC-Zeros-Requiem]], [[16-Risk-Management-Elite-System]], [[25-Walk-Forward-Full-Results]], [[29-P5-P7-P8-OANDA-Portfolio]]
---

# CLAUDE.md — Master Strategy Specification

> This is a **mirror reference** for Obsidian linking. The authoritative file lives at the project root: `../CLAUDE.md`

## What This File Contains

The root `CLAUDE.md` is the **single source of truth** for the Zeros Requiem project. It auto-loads into every Claude Code session and defines:

### Identity & Philosophy
- **Sovereign Quant-Tactician** persona
- Mark Douglas's 5 Fundamental Truths
- Probabilistic thinking framework

### SBRS 1.1 Strategy Specification
- **Sacred Parameters** (WMA=9, SMMA=7, Swing Lookback=20) — NEVER optimise
- **Tunable Parameters** (ATR, retest wait, SL buffer) — ±20% range only
- **5-Step Entry Logic:** Trend context → Structure break → Retest → MA cross → Filters
- **6 Exit Conditions:** TP hit, SL hit, BE move, MA reversal, Structure break, Max hold

### Elite Benchmarks
| Metric | Target |
|--------|--------|
| Sharpe Ratio | ≥1.50 |
| Profit Factor | ≥1.50 |
| Annual Return | ≥20% |
| Max Drawdown | ≤15% |
| Walk-Forward | ≥75% consistency |
| Monte Carlo | <5% prob of 20% DD |
| Trade Count | ≥500 per strategy |

### File Modification Rules
- **Can modify:** `src/regimes/sbrs_gold.py`, `src/indicators/technical.py`, `tests/`
- **Ask first:** `src/core/engine.py`, parameter changes outside ±20%
- **Never touch:** `src/core/risk_manager.py`, core SBRS parameters

### Current Portfolio Status
- **Tier 1 (Live):** Gold 1H SBRS — paper trading on OANDA
- **Tier 2 (Testing):** S&P 500, NASDAQ, DAX — need 5Y+ data
- **Tier 3 (Rejected):** Crypto — no edge found

## Dual Framework Note

The project contains **two** strategy frameworks:
1. **SBRS 1.1** — Live paper trading (breakout + retest + MA cross)
2. **SCAF 2.0** — Backtesting framework (sweep + displacement + FVG)

See [[17-SCAF-2.0-Architecture]] for SCAF details and [[29-P5-P7-P8-OANDA-Portfolio]] for portfolio allocation.

## Related

- [[00-MOC-Zeros-Requiem]] — Map of Content (start here)
- [[16-Risk-Management-Elite-System]] — 5-layer risk management
- [[25-Walk-Forward-Full-Results]] — Walk-forward validation
- [[28-P4-Monte-Carlo]] — Monte Carlo validation
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers
- [[36-Tool-CLAUDE-MD-Autoload]] — How auto-loading works
