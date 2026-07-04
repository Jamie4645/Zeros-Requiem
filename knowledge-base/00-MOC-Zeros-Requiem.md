---
tags: [hub, strategy, reference]
aliases: [Home, Dashboard, Index]
---

# Zeros Requiem — Map of Content

> *"An edge is nothing more than an indication of a higher probability of one thing happening over another."* — Mark Douglas

> ⛔ **2026-06-01 — CANON INVALIDATED.** The SBRS 2.0 backtest edge was a phantom-fill artifact
> (reversal entries filled at levels price never reached, 95–100% WR). Fixed; realistic-fill BT
> shows **no edge on any instrument** (PF 0.52–1.07). All prior PF/Sharpe/WF/MC/tier claims in this
> KB are VOID pending rebuild. **Start here → [[81-Audit-2026-06-01-Phantom-Fill]].**

---

## Quick Access

| Action | Link |
|--------|------|
| Check live bot | [[30-Tool-Live-Status]] |
| Run a backtest | [[31-Tool-Backtest]] |
| Review risk rules | [[16-Risk-Management-Elite-System]] |
| Current portfolio | [[29-P5-P7-P8-OANDA-Portfolio]] |
| SBRS strategy spec | [[CLAUDE]] |
| ⛔ Why canon is void | [[81-Audit-2026-06-01-Phantom-Fill]] |
| ▶ Active phase | [[87-Supervised-Rebuild]] |

---

## ⛔ 2026-06 Phantom-Fill Audit & SBRS 3.0 Rebuild (READ FIRST)

The SBRS 2.0 track record below was found to be a **phantom-fill artifact** — the
backtest filled reversal entries at prices that were never touched (95–100% WR).
Fixed; realistic-fill backtests show **no edge on any instrument** (PF 0.52–1.07).
All SBRS 2.0 performance claims in this KB are **VOID**. Active work is a clean-slate
supervised rebuild from the user's real 5m–15m trades.

- [[81-Audit-2026-06-01-Phantom-Fill]] — entry point / executive summary
- [[82-Audit-2026-06-Blocker-Remediation]] — the six audit blockers + fixes
- [[83-Reversal-Fill-Fix]] — the phantom-fill bug & limit-order fix (root cause)
- [[84-Realistic-Fill-No-Edge]] — realistic re-validation: portfolio has no edge
- [[85-Primary-Edge-Teardown]] — confluence is anti-predictive; strip-back lead
- [[86-SBRS-3.0-Spec-And-Build]] — clean-slate SBRS 3.0 + structural exits
- [[87-Supervised-Rebuild]] — **ACTIVE:** learning the edge from real trades
- [[88-Audit-Harness-Index]] — every script, log, and file touched

## ✅ 2026-07-02 Full-Codebase Audit + Books Re-Read (LATEST)

Dual-workflow review (31-agent codebase audit + 17-agent blank-slate books/strategy
review). 10 confirmed CRITICAL/HIGH defects — **all fixed and committed same day**
(duplicate-order lock, deploy gate makes 0.00% live a code invariant, WF peak-reset
fixed → R6-5 retracted, look-ahead closed, block-bootstrap MC, asset-class slippage,
phantom-fill tripwire promoted to collected tests, screener pipeline repaired).
**NEW EVIDENCE:** 60-label permutation null — user selection +10.29R, p<0.0001
(p=0.0001 direction-stratified) → discretionary selection statistically supported
retrospectively; forward falsifier **F8** registered.

- [[91-Full-Codebase-Audit-2026-07]] — findings → fixes table (entry point)
- [[92-Books-Blank-Slate-Review]] — 13-book synthesis, kill list, permutation result
- [[90-Pre-Registered-Falsifier-ZTT]] — F8 added (discretionary-selection forward gate)
- [[93-Fresh-Gold-Strategy-MPB-VTC]] — 2026-07-04: fresh candidates MPB+VTC pre-registered
  (N1–N8, frozen grids) → **both KILLED at N3** (PF 0.44/0.41, 0/18 cells); 16-agent
  ultrareview upheld the kills, pre-registration integrity CLEAN; gap-collapse guard added
  to ztt_sim; socrates flag: 3rd dead mechanization → question the discovery method itself

---

## Strategy: SBRS 2.0 — Sovereign Breakout Retest Strategy

> ⛔ **VOID (2026-06):** all SBRS 2.0 performance numbers below are phantom-fill
> artifacts. See [[81-Audit-2026-06-01-Phantom-Fill]]. Retained for history.

*Codification of 3-4 years of profitable discretionary Gold trading, enhanced with smart money concepts and ablation-validated tuning.*

### SBRS 2.0 (Current — April 2026)
- [[47-SBRS-2.0-Upgrade]] — Full upgrade documentation (7/7 elite benchmarks met)
- [[48-Ablation-Study-Results]] — 17-test ablation study: feature contribution analysis
- [[49-MA-Convention-Discovery]] — The $3,300 MA convention finding
- [[50-Smart-Money-Indicators]] — FVG, liquidity sweep, level quality, false breakout
- [[51-Confluence-Scoring-System]] — How multi-signal scoring replaced binary MA gate
- [[52-Data-Infrastructure-Upgrade]] — OANDA/IBKR data pipeline fix (10Y data unlocked)
- [[53-SBRS-2.1-Experiment]] — v2.1 experiment (built and removed)
- [[54-Fine-Tuning-Process]] — From $513 to $146,256: the ablation-driven process

### Multi-Asset Expansion (April 2026)
- [[55-Multi-Asset-Expansion]] — **10-instrument test:** Gold, 4 forex, 3 indices, 2 crypto
- [[56-Risk-Manager-Calibration]] — DD cap fix: unlocked NASDAQ/DAX edge (96% blocked → profitable)
- [[57-Monte-Carlo-Gold-v2]] — 10,000 simulations: 100% profitable, 0.5% risk recommended
- [[58-GBP-USD-Discovery]] — PF 2.69 single-test, needs WF tuning (62%, 5/8)
- [[59-Strategy-Comparison-v1-vs-v2]] — **Complete v1.1 vs v2.0 comparison + all 10 assets**
- [[60-Phase2-Algo-Improvements]] — ATR filter + adaptive R:R + exit optimization. GBP/USD FIXED (100% WF). ETH validated.
- [[61-Audit-Remediation-2026-04]] — Causal 4H, direction normalization, live/data fixes (April 2026)
- [[62-Ablation-Round-2-Results]] — **Round 2 ablation (2026-04-16):** FVG critical claim reversed; session filter confirmed primary
- [[63-FVG-Downshift-Change]] — FVG weight 1.0 → 0.5 after ablation found "No FVG" beat baseline +154%
- [[64-Risk-Manager-Gold-Cap-Fix]] — Gold inherits 20% DD cap (Layer 2 was blocking 97% of setups)
- [[65-Sovereign-Quant-Arbiters]] — **10-agent research council** with shared brain + council sessions
- [[66-Ablation-Round-3-Post-Change]] — **Round 3 ablation (2026-04-16):** session filter and MA convention findings reversed — high-priority hypotheses for council
- [[67-Round-5-Post-Council-Validation]] — Round 5 synthesis (2026-04-18): 4 Tier-1 strategies confirmed, 9/10 portfolio score
- [[70-Ablation-Round-6]] — **Round 6 ablation (2026-04-18):** 18-config re-baseline vs filter-OFF — Liquidity Sweep is THE load-bearing feature; 4 dead flags flagged for Round 7 cleanup
- [[71-NDX-Fat-Tail-Audit]] — **R6-1 resolution (2026-04-18):** NDX PF 3.49 → 0.86 collapse is 100% B1 slippage; data-source flip is a non-issue; user decision pending on recalibration
- [[72-Gold-Bar-Audit]] — **D1 inconclusive (2026-04-18):** fetcher routes GC=F through OANDA regardless of caller; Round 7 fix queued
- [[73-Round-5-Remediation-Log]] — **Round 5 remediation execution log (2026-04-18):** all 20 council items resolved/queued
- [[74-Round-7-Post-Validation]] — **Round 7 canon (2026-04-18):** slippage recal (1.5pt → 0.75pt) restored NDX/DAX; USDJPY promoted to Tier 2; 9/10 score; R6-1/R6-3/R6-4/R6-5/R7-10/R7-11 CLOSED
- [[75-Pre-Registered-Falsifier-R8]] — **Round 8 falsifiers (2026-04-19):** 5 numeric kill-switches, amendment-locked
- [[76-Round-8-Evidence-Weighted-Sizing]] — **Round 8 sizing (2026-04-19):** 1.50% → 1.10% evidence-weighted; measured MC
- [[77-Round-8-Canon]] — **Round 8 canon (2026-04-19):** dual-council deliberation; U1–U10 governance; supersedes R7 "9/10"
- [[78-Round-8-Council-Synthesis]] — **Round 8 dual-council merge (2026-04-19):** Philosophical (18) + Arbiter (10) synthesis
- [[79-Round-8-Best-Version-PnL]] — **Round 8 PnL tables (2026-04-19):** per-market best-version with dollar contributions

### Post-Round 8 Backlog — Open Items

Each queued for the next council cycle; skills / agents to fire on each in parentheses. See [[74-Round-7-Post-Validation]] for items closed at Round 7.

**Closed in Round 7:** R6-1 (NDX suspension), R6-3 (DAX borderline), R6-4 (GBPUSD W7), R6-5/R7-9 (BT-vs-WF discrepancy), R7-10 (DAX cap), R7-11 (USDJPY promotion).

**Still open:**
- **G1** NDX live-promotion gate — lift from paper to live once fill-drift confirmed (`/paper-gate` + `arbiter-risk`)
- **G2** Portfolio fat-tail Monte Carlo (Student-t ν=4 shocks) — current Gaussian P99 10.21% is likely conservative (`/monte-carlo --tail`)
- **G3** Crypto per-asset FVG weight test — BTC/ETH PF fell post-downweight; re-test CONFLUENCE_SCORE_FVG_CRYPTO ∈ {0.75, 1.0} once 5Y+ Binance data is fetched (`/data-refresh binance` → `/ablation` crypto subset)
- **G4** USD/JPY 5Y+ depth — 161 trades on OANDA 10Y; assess IBKR depth to push trade count → 500 → Tier 1 promotion (`/data-refresh`)
- **G5** EUR/USD Tier-3 lock — closed; do not pursue
- **G6** Paper-trade fill-drift tracking — compare `actual_fill_price` vs `backtest_expected_entry` to validate 0.75pt index slip (`/live-status` recurring loop)
- **G7** S&P 500 Tier-4 lock — structurally absent from live runner; no action
- **G8** Forex session filter review — currently 07:00-16:00 GMT; widen if GBP/USD trade count stays <500 (`arbiter-forex`)

### Core Documentation
- [[CLAUDE]] — Master strategy spec, parameters, entry/exit logic
- [[46-SBRS-Parameters-Reference]] — All parameters with test ranges
- [[16-Risk-Management-Elite-System]] — 5-layer risk management
- [[25-Walk-Forward-Full-Results]] — Walk-forward validation results (v1.1 era)
- [[28-P4-Monte-Carlo]] — Monte Carlo simulation & validation
- [[29-P5-P7-P8-OANDA-Portfolio]] — Portfolio tiers
- [[44-Live-Runner-Architecture]] — Runner, executor, state, alerts
- [[45-Data-Pipeline]] — OANDA → IBKR → Yahoo routing

### Validation & Optimisation (v1.1 Era)
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
- [[34-Tool-Sequential-Thinking-MCP]] — Sequential Thinking MCP server (structured reasoning)
- [[35-Tool-GSD2]] — GSD2 task management integration
- [[36-Tool-CLAUDE-MD-Autoload]] — How CLAUDE.md auto-loads into sessions
- [[68-Tool-Context7]] — Context7 live-documentation plugin (Upstash)
- [[69-Tool-Superpowers]] — Superpowers dev-methodology plugin (obra)

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

## Elite Benchmarks — Multi-Asset Portfolio

| Asset | PF | Sharpe | DD | WF | Trades | Tier |
|-------|-----|--------|------|------|--------|------|
| **Gold** | 1.97 | 1.77 | 9.2% | 75% (6/8) | 2,252 | **1 — Live Ready** |
| **DAX** | 1.53 | 1.18 | 11.4% | **88% (7/8)** | 1,096 | **1 — Paper Ready** |
| **NASDAQ** | 1.57 | 1.11 | 17.8% | **88% (7/8)** | 888 | **1 — Paper Ready** |
| **GBP/USD** | 2.69 | 2.00 | 7.8% | 62% (5/8) | 1,323 | 2 — Needs Tuning |
| **Bitcoin** | 1.59 | 2.76 | 9.6% | — (2Y only) | 747 | 2 — Needs Data |
| **Ethereum** | 1.63 | 2.63 | 9.7% | — (2Y only) | 748 | 2 — Needs Data |
| **USD/JPY** | 1.27 | 0.84 | 15.7% | — | 1,228 | 3 — Marginal |
| **S&P 500** | 0.63 | -0.39 | 20.4% | — | 64 | 4 — No Edge |

**3 strategies now walk-forward validated.** See [[55-Multi-Asset-Expansion]] for full details.

---

*Last updated: 2026-04-05*
