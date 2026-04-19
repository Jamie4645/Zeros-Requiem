--
tags: [hub, strategy, reference]
aliases: [Strategy Spec, SBRS Spec, Sacred Parameters, Master Spec]
related: [[00-MOC-Zeros-Requiem]], [[16-Risk-Management-Elite-System]], [[25-Walk-Forward-Full-Results]], [[29-P5-P7-P8-OANDA-Portfolio]], [[47-SBRS-2.0-Upgrade]], [[48-Ablation-Study-Results]], [[49-MA-Convention-Discovery]]
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

### Current Portfolio Status (Round 7 — 2026-04-18 canonical)
- **Tier 1 (WF-Validated):** Gold 1H (100% WF, PF 2.65), DAX 1H (88% WF, PF 1.69), NASDAQ 1H (88% WF, PF 2.63), GBP/USD 1H (100% WF, PF 2.01)
- **Tier 2 (Elite-MC Candidate):** USD/JPY 1H (88% WF, PF 3.18 BT / 2.58 WF, 161 trades blocks Tier 1)
- **Tier 3 (Marginal / Unvalidated):** EUR/USD (PF 1.08), BTC/ETH (2Y only, G3 backlog)
- **Tier 4 (Rejected):** S&P 500, AUD/USD

See [[74-Round-7-Post-Validation]] for the full Round 7 canon and closed-items log; [[55-Multi-Asset-Expansion]] for the original 10-instrument baseline.

## Architecture Note

The project uses a **single unified framework** as of Phase 6 (2026-03), upgraded to SBRS 2.0 in April 2026:
- **SBRS 2.0** — Active strategy. Confluence scoring + smart money. 7/7 elite benchmarks met. See [[47-SBRS-2.0-Upgrade]].
- **SBRS 1.1** — Legacy. Preserved in `sbrs_gold.py` for comparison.
- **SCAF 2.0** — Removed. See [[43-Phase-6-SCAF-Removal]].
- **SBRS 2.1** — Experimental. Built and removed. See [[53-SBRS-2.1-Experiment]].

See [[29-P5-P7-P8-OANDA-Portfolio]] for portfolio allocation.

## Related

- [[00-MOC-Zeros-Requiem]] — Map of Content (start here)
- [[16-Risk-Management-Elite-System]] — 5-layer risk management
- [[25-Walk-Forward-Full-Results]] — Walk-forward validation
- [[28-P4-Monte-Carlo]] — Monte Carlo validation
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers
- [[36-Tool-CLAUDE-MD-Autoload]] — How auto-loading works
- [[67-Round-5-Post-Council-Validation]] — Round 5 synthesis (4 Tier-1 confirmed)
- [[73-Round-5-Remediation-Log]] — Round 5 remediation execution log
- [[74-Round-7-Post-Validation]] — Round 7 canon: slippage recal + USDJPY promotion + R6 closures
