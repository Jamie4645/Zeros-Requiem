---
tags: [audit, validation, no-edge, critical, monte-carlo, walk-forward]
aliases: [No Edge, Realistic Re-Validation, Canon Voided]
related: [[81-Audit-2026-06-01-Phantom-Fill]], [[83-Reversal-Fill-Fix]], [[85-Primary-Edge-Teardown]], [[76-Round-8-Evidence-Weighted-Sizing]], [[77-Round-8-Canon]], [[79-Round-8-Best-Version-PnL]]
---

# 84 — Realistic-Fill Re-Validation: The Portfolio Has No Edge

After the [[83-Reversal-Fill-Fix|fill fix]], every instrument was re-backtested on
realistic fills. This note records the result that **voids all prior canon**.

## Realistic-fill re-validation — Gold 1H 10Y, raw 1% risk
Source: `logs/audit/realistic_revalidation.log` (`tests/_audit_realistic_revalidation.py`).

| Symbol | Trades | WR | PF | PnL | Sharpe | MaxDD | Elite gate |
|---|---:|---:|---:|---:|---:|---:|:--|
| Gold (GC=F) | 159 | 40.2% | 0.96 | −$446 | −0.04 | 20.2% | FAIL |
| DAX (^GDAXI) | 128 | 42.2% | 0.75 | −$1,918 | −0.34 | 20.2% | FAIL |
| NDX (^IXIC) | 60 | 36.7% | 0.52 | −$1,900 | −0.56 | 20.6% | FAIL |
| GBPUSD | 58 | 27.6% | 0.55 | −$1,970 | −0.48 | 20.6% | FAIL |
| USDJPY | 132 | 40.1% | 1.07 | +$581 | 0.10 | 12.9% | FAIL |

Every instrument fails every elite gate (PF≥1.5, Sharpe≥1.5, DD≤15%, PnL>0).
NDX — canon PF 2.63 — is **PF 0.52** with fills that can actually happen.

## What is now VOID
All Round 5–8 canon: every PF 2.0–2.65, Sharpe 1.0–1.78, 88–100% walk-forward,
MC Prob(20%DD), and Tier-1 / live-ready status documented in
[[76-Round-8-Evidence-Weighted-Sizing]], [[77-Round-8-Canon]],
[[79-Round-8-Best-Version-PnL]]. They were computed on phantom-fill backtests.
WF/MC re-runs are moot — the full-sample BT is already PF < 1.1.

The root `../CLAUDE.md` carries a permanent invalidation banner; the portfolio
table there is retained only for historical diff.

## Cross-check
The realistic numbers reconcile with the "reversal OFF" ablation
([[85-Primary-Edge-Teardown]]): Gold ~154 tr / −$749 (ablation) ≈ 159 tr / −$446
(post-fix) — confirming the fix behaves correctly and the reversal contributed
nothing real.

## Implication
**Nothing is live-ready; total live risk should be treated as 0.00%.** The crucial
silver lining: the bug was caught in backtest, before any capital was deployed.
The rebuild path begins at [[85-Primary-Edge-Teardown]].
