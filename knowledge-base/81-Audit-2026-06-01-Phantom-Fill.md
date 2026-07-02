---
tags: [audit, critical, validation, invalidation]
aliases: [Phantom Fill Audit, Reversal Fill Bug, Canon Invalidation]
related: [[00-MOC-Zeros-Requiem]], [[47-SBRS-2.0-Upgrade]], [[53-SBRS-2.1-Experiment]], [[48-Ablation-Study-Results]], [[74-Round-7-Post-Validation]]
---

# 81 — Phantom-Fill Audit (2026-06-01): SBRS 2.0 Canon Invalidated

> ⛔ **This note supersedes all prior performance canon.** A full-codebase audit found the
> backtest engine's edge was a fill artifact. With realistic fills, SBRS 2.0 has **no demonstrated
> edge** on any instrument. Nothing is live-ready.

## The bug
`src/core/engine.py` injected a "failed-breakout-reversal" trade whenever an SBRS 2.0 setup hit its
stop, scheduling an opposite-direction entry at the **broken level** on the next bar. The engine
filled that entry at the broken level **unconditionally** — it never checked whether price actually
traded to the level on the fill bar. The user's methodology (`Zeros_Trading_Methodology.docx`,
Trade 15 / Trade 6) specifies the reversal as a **limit order** ("limit orders exclusively, never at
market"), and a limit only fills if touched. The reverse trade profits precisely when price moves
*away* from the level, so the unconditional fill manufactured near-guaranteed winners.

## The evidence (10Y, 1H, raw 1% risk) — `logs/audit/reversal_stats_all.log`
Isolating reversal trades and checking whether price actually touched the level on the fill bar:

| Symbol | Total PnL | Phantom % of PnL | Phantom-cohort WR | Legit PnL (primary + real-fill) |
|---|---:|---:|---:|---:|
| Gold (GC=F) | $64,710 | 93.3% | 100% | +$4,330 |
| DAX (^GDAXI) | $7,945 | 149% | ~96% | −$3,894 |
| NDX (^IXIC) | $47,742 | 125% | ~96% | −$11,947 |
| GBPUSD | $35,323 | 121% | ~97% | −$7,459 |
| USDJPY | $18,406 | 98.9% | ~98% | +$201 |

A 95–100% win rate on the phantom cohort is the definitive look-ahead signature.

## The fix
Reversals now rest as real **limit orders** (`REVERSAL_LIMIT_MAX_WAIT = 10` bars): fill only when the
bar trades to the level (short → high ≥ level; long → low ≤ level), else expire. Post-fix the phantom
diagnostic reports **0 phantom fills**.

## Realistic-fill re-validation — `logs/audit/realistic_revalidation.log`
| Symbol | Trades | WR | PF | PnL | Sharpe | MaxDD | Gate |
|---|---:|---:|---:|---:|---:|---:|:--|
| Gold | 159 | 40.2% | 0.96 | −$446 | −0.04 | 20.2% | FAIL |
| DAX | 128 | 42.2% | 0.75 | −$1,918 | −0.34 | 20.2% | FAIL |
| NDX | 60 | 36.7% | 0.52 | −$1,900 | −0.56 | 20.6% | FAIL |
| GBPUSD | 58 | 27.6% | 0.55 | −$1,970 | −0.48 | 20.6% | FAIL |
| USDJPY | 132 | 40.1% | 1.07 | +$581 | 0.10 | 12.9% | FAIL |

## What is now VOID
All Round 5–8 canon: every PF 2.0–2.65, Sharpe 1.0–1.78, 88–100% walk-forward, MC Prob(20%DD), and
Tier-1 / live-ready status. These were computed on phantom-fill backtests. WF/MC re-runs are moot
(full-sample BT is already PF < 1.1).

## Other audit blockers fixed (same session)
- `SYMBOL_RISK_CAP` was cosmetic → now a real clamp at the `analyze_sbrs_v2` chokepoint (live + BT).
- `oanda_executor._last_fill_price` stale-fill bug (corrupted slip reconciliation) → reset on entry.
- `test_risk_caps.py` red (pinned stale R7 caps) → re-anchored to R8.
- No SACRED-param test pins → `tests/test_sacred_params.py` added.

## The full 2026-06 audit + rebuild series
This note is the entry point. The story continues across:
- [[82-Audit-2026-06-Blocker-Remediation]] — the six blockers and their fixes.
- [[83-Reversal-Fill-Fix]] — the phantom-fill bug and the limit-order fix (root cause).
- [[84-Realistic-Fill-No-Edge]] — realistic re-validation: no edge on any instrument.
- [[85-Primary-Edge-Teardown]] — entry/selectivity/trend ruled out; confluence is anti-predictive.
- [[86-SBRS-3.0-Spec-And-Build]] — clean-slate SBRS 3.0 with structural exits (still no edge).
- [[87-Supervised-Rebuild]] — the active phase: learning the edge from real 5m–15m trades.
- [[88-Audit-Harness-Index]] — every script, log, and file touched.

## Next
Capture the user's discretionary edge via the [[87-Supervised-Rebuild|supervised real-trade]]
approach. Re-derive any canon ONLY from realistic-fill backtests. Harnesses indexed in
[[88-Audit-Harness-Index]].
