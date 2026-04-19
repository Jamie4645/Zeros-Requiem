--
tags: [arbiters, agents, research, system]
aliases: [Arbiter Council, SQA, Sovereign Quant Arbiters, Council]
related: [[00-MOC-Zeros-Requiem]], [[CLAUDE]], [[62-Ablation-Round-2-Results]]
---

# Sovereign Quant Arbiters — Research Council

> *"A council of specialists — each hunting a different edge, each teaching the others."*

The **Sovereign Quant Arbiters (SQA)** are a council of 10 specialised Claude Code sub-agents that continuously investigate the SBRS 2.0 strategy, share findings, and propose improvements. Each Arbiter has a narrow focus domain; together they form a cross-discipline research team.

## Mission

1. **Investigate** — Each Arbiter runs domain-specific analyses using the existing tooling (`py main.py`, ablation, walk-forward, MC).
2. **Learn** — Every finding is written to a shared, append-only knowledge file that all Arbiters read before starting new work.
3. **Teach** — Findings include both conclusions AND hypotheses the author couldn't test; these seed other Arbiters' next runs.
4. **Propose** — Arbiters never modify sacred files (risk_manager.py, core SBRS params) without explicit user approval.
5. **Converge** — The Council Arbiter synthesizes findings into a daily/weekly brief.

## The 10 Arbiters

| # | Agent | Focus |
|---|---|---|
| 1 | `arbiter-gold` | Gold (XAU/USD) — breakout quality, session patterns, USD correlation |
| 2 | `arbiter-indices` | DAX, NASDAQ, S&P 500 — market hours, earnings/macro, index correlations |
| 3 | `arbiter-forex` | GBP/USD, EUR/USD, USD/JPY, AUD/USD — sessions, central banks, pair correlations |
| 4 | `arbiter-crypto` | BTC, ETH, SOL — 24/7 regime, weekend effects, cross-asset flow |
| 5 | `arbiter-regime` | Market regime classification — trending vs choppy, volatility clustering |
| 6 | `arbiter-risk` | Portfolio risk, position sizing, drawdown management, Kelly sizing |
| 7 | `arbiter-execution` | Slippage, fill quality, session timing, transaction cost analysis |
| 8 | `arbiter-data` | Data quality, gaps, source validation (OANDA/IBKR/Binance/Yahoo) |
| 9 | `arbiter-ablation` | Feature contribution — periodic ablation, parameter sensitivity |
| 10 | `arbiter-council` | Synthesizes all findings, produces executive briefs, prioritises next tests |

## Shared Brain

All Arbiters read and write to:

```
knowledge-base/arbiters/
├── shared-findings.md      # append-only canonical findings log
├── council-charter.md      # mission, hard rules, benchmarks
├── next-hypotheses.md      # open hypotheses waiting to be tested
└── logs/
    ├── arbiter-gold-log.md
    ├── arbiter-indices-log.md
    ├── ...
    └── arbiter-council-log.md
```

**Read order** before starting any Arbiter session:
1. `council-charter.md` — mission & hard rules
2. `shared-findings.md` — what others have learned
3. Own log — what this Arbiter has tried before
4. `next-hypotheses.md` — what others have flagged for this Arbiter's domain

**Write order** at end of Arbiter session:
1. Own log — chronological research journal
2. `shared-findings.md` — canonical finding (if novel)
3. `next-hypotheses.md` — hypotheses handed to other Arbiters

## Invocation

### Daily Council Session

Run `/arbiter-council` (skill) to fire all 10 Arbiters in parallel, then have the Council synthesize. Produces a one-page executive brief covering:

- What each Arbiter learned today
- Top 3 hypotheses worth testing this week
- Any red-flag findings that require immediate user decision
- Updated tier rankings across the portfolio

### Individual Arbiter

Invoke any specific Arbiter via the Agent tool (e.g., `subagent_type: "arbiter-gold"`). Useful when you want a domain-specific deep dive without firing the full council.

## Hard Rules

The **Council Charter** binds every Arbiter:

1. **Never modify sacred files** — `src/core/risk_manager.py`, WMA_PERIOD, SMMA_PERIOD, SWING_LOOKBACK, MIN_RR, RETEST_TOLERANCE_ATR changes require human approval. Arbiters propose only.
2. **Never deploy to live** — Arbiters propose; user deploys.
3. **Honesty over flattery** — If a strategy fails, say so. See CLAUDE.md: "Honest rejection > false hope".
4. **Walk-forward before claims** — No recommendation based on single-backtest.
5. **Reference the evidence** — Every claim in shared-findings.md must cite either a log path or a command the reader can re-run.
6. **No duplicate work** — Read shared-findings.md first. If someone else already tested it, cite them.
7. **Respect the token budget** — Arbiters use skills (`/walk-forward`, `/monte-carlo`, `/ablation`) and scoped CLI calls, not inline Python dumps.
8. **Mark Douglas thinking** — Think in probabilities, not predictions. Next 100 trades, not next 1.

## Purpose Beyond the Agents

This is not just an agent convenience. It is a **learning system**:
- Each invocation adds to shared-findings — future sessions start smarter than previous ones
- Failed hypotheses are recorded too, preventing re-tested dead ends
- Knowledge compounds across sessions even when individual agent runs are stateless

The "goal of becoming live Sovereign Quant Arbiters" is directional — as the shared brain accumulates sufficient validated findings, the Arbiters' recommendations become higher-signal, and the human layer can reduce its oversight from every decision to every release.

## Related

- [[00-MOC-Zeros-Requiem]] — Map of Content
- [[CLAUDE]] — Master strategy spec
- [[62-Ablation-Round-2-Results]] — The study that motivated formalising this system
- [[16-Risk-Management-Elite-System]] — Hard risk rules the Arbiters must respect
