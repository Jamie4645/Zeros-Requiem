--
tags: [strategy, milestone, v2]
aliases: [SBRS 2.0, v2.0 Upgrade, SBRS 2.0 Upgrade]
related: [[CLAUDE]], [[00-MOC-Zeros-Requiem]], [[46-SBRS-Parameters-Reference]], [[48-Ablation-Study-Results]], [[49-MA-Convention-Discovery]], [[50-Smart-Money-Indicators]], [[51-Confluence-Scoring-System]], [[52-Data-Infrastructure-Upgrade]], [[25-Walk-Forward-Full-Results]]
---

> ⛔ **RETIRED (see root `CLAUDE.md`).** SBRS 2.0's "7/7 elite benchmarks met" was a phantom-fill
> artifact (2026-06-01 audit); realistic-fill re-validation found no edge on any instrument.
> SBRS is fully retired — the ZTT rebuild does not inherit this logic. Retained as historical
> record only. Current strategy: ZTT (`knowledge-base/89-ZTT-Rebuild.md`).

# SBRS 2.0 — Major Strategy Upgrade

**Date:** 2026-04-04 to 2026-04-05
**Status:** VALIDATED (7/7 elite benchmarks met)

---

## What Changed from SBRS 1.1

SBRS 2.0 is the most significant upgrade since the strategy was first codified. It transforms the binary pass/fail entry system into a multi-signal confluence scoring framework while preserving the sacred breakout-retest core.

| Feature | SBRS 1.1 | SBRS 2.0 |
|---------|----------|----------|
| MA Cross | Binary gate (required) | Confluence booster (+0.5 score) |
| Counter-trend | Blocked entirely | Allowed with score >= 2.0 |
| FVG Detection | Not used | Confluence booster (+1.0) |
| Liquidity Sweep | Not used | Confluence booster (+1.0) |
| Level Quality | Not checked | 2+ touches mandatory, 3+ bonus (+0.5) |
| Retest Tolerance (Longs) | 0.5 ATR | 0.7 ATR (ablation-validated) |
| MA Convention | WMA > SMMA = bullish | WMA > SMMA = bullish (ablation-validated) |
| Whipsaw Filter | Not present | Tested and REMOVED (hurt performance) |

---

## Performance Comparison (Gold 10Y, OANDA, 59,046 bars)

| Metric | SBRS 1.1 | SBRS 2.0 | Improvement |
|--------|----------|----------|-------------|
| Total Trades | 894 | 2,252 | +152% |
| Win Rate | 42.2% | 38.9% | -3.3pp |
| **Profit Factor** | 1.39 | **1.97** | +42% |
| **Total PnL** | $18,117 | **$146,256** | +707% |
| **Sharpe Ratio** | 1.06 | **1.77** | +67% |
| **Max Drawdown** | 10.10% | **9.17%** | -0.93pp |
| Expectancy/Trade | $20.27 | $64.95 | +220% |
| Avg Win | $170 | $339 | +99% |

---

## Walk-Forward (8 windows, 10Y)

| Window | Period | Trades | WR | PnL | PF | Sharpe |
|--------|--------|--------|------|------|------|--------|
| W1 | 2016-04 to 2017-07 | 271 | 41.0% | $7,715 | 1.48 | 1.84 |
| W2 | 2017-07 to 2018-10 | 96 | 33.3% | $940 | 1.17 | 0.47 |
| W3 | 2018-10 to 2020-01 | 134 | 35.8% | $1,939 | 1.25 | 0.82 |
| W4 | 2020-01 to 2021-04 | 276 | 44.6% | $7,604 | 1.51 | 1.96 |
| W5 | 2021-04 to 2022-07 | 75 | 34.7% | -$608 | 0.88 | -0.29 |
| W6 | 2022-07 to 2023-10 | 94 | 37.2% | -$76 | 0.99 | 0.02 |
| W7 | 2023-10 to 2025-01 | 80 | 33.8% | $328 | 1.06 | 0.22 |
| W8 | 2025-01 to 2026-04 | 89 | 38.2% | $1,229 | 1.22 | 0.60 |

**Consistency: 75% (6/8 profitable)**

---

## Elite Benchmark Scorecard

| Benchmark | Target | Result | Status |
|-----------|--------|--------|--------|
| Sharpe Ratio | >= 1.5 | 1.77 | PASS |
| Profit Factor | >= 1.5 | 1.97 | PASS |
| Max Drawdown | <= 15% | 9.17% | PASS |
| Expectancy | > $0 | $64.95 | PASS |
| Trade Count | 500+ | 2,252 | PASS |
| Walk-Forward | 75%+ | 75% (6/8) | PASS |
| Slippage | Modeled | 1.5 pips | PASS |

**First version to pass all 7 benchmarks simultaneously.**

---

## Key Files

- `src/regimes/sbrs_v2.py` — Strategy implementation
- `src/indicators/smart_money.py` — FVG, liquidity sweep, level touches, false breakout
- `src/core/engine.py` — v2.0 trade management
- `docs/sbrs_v2_spec.md` — Full specification

---

## Related

- [[48-Ablation-Study-Results]] — The ablation study that drove the fine-tuning
- [[49-MA-Convention-Discovery]] — The MA convention investigation
- [[50-Smart-Money-Indicators]] — FVG, Liquidity Sweep, Level Quality
- [[51-Confluence-Scoring-System]] — How confluence scoring works
- [[52-Data-Infrastructure-Upgrade]] — OANDA/IBKR data pipeline fix
- [[00-MOC-Zeros-Requiem]] — Map of Content
