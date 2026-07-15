---
tags: [audit, engine, bug, look-ahead, fill-realism, critical]
aliases: [Phantom Fill Bug, Reversal Limit Fix, Failed Breakout Reversal Bug]
related: [[81-Audit-2026-06-01-Phantom-Fill]], [[82-Audit-2026-06-Blocker-Remediation]], [[84-Realistic-Fill-No-Edge]], [[47-SBRS-2.0-Upgrade]], [[53-SBRS-2.1-Experiment]]
---

# 83 — The Reversal Phantom-Fill Bug & The Limit-Order Fix

The root cause behind the [[81-Audit-2026-06-01-Phantom-Fill|canon invalidation]].
This is an engine correctness bug, not a strategy choice.

## The feature (legitimate in the methodology)
SBRS 2.0 injected a "failed-breakout-reversal" trade: when a v2 setup hit its
stop, it entered the OPPOSITE direction at the broken level on the next bar. This
IS in the user's methodology (Trade 15 "failed breakout recovery", Trade 6
"recovery after initial stop-loss") — so the idea is sound. The **implementation**
was broken.

## The bug (engine.py, old behaviour)
The injected reversal filled at `entry_price = broken_level`
**unconditionally** — the engine never checked whether price actually traded to
that level on the fill bar. The user's methodology specifies a LIMIT order
("limit orders exclusively, never at market"), and a limit only fills if touched.

The reverse trade profits exactly when price moves *away* from the level, so
assuming an unconditional fill manufactured near-guaranteed winners.

## The proof (`logs/audit/reversal_stats_all.log`)
Isolating reversal trades and checking whether price touched the level on the
fill bar (short → high ≥ level; long → low ≤ level):

| Symbol | Total PnL | Phantom % of PnL | Phantom-cohort WR |
|---|---:|---:|---:|
| Gold | $64,710 | 93.3% | 100% |
| DAX | $7,945 | 149% | ~96% |
| NDX | $47,742 | 125% | ~96% |
| GBPUSD | $35,323 | 121% | ~97% |
| USDJPY | $18,406 | 98.9% | ~98% |

A 95–100% win rate on the phantom cohort is the definitive look-ahead signature
(no real trading bucket wins ~100%). The phantom wins also compound equity, which
let more *primary* trades pass risk-gating — so the artifact cascades.

## The fix (engine.py)
Reversals now rest as real **limit orders**:
- `REVERSAL_LIMIT_MAX_WAIT = 10` bars.
- Injection stores `(ready_bar, expiry_bar, setup)`.
- A shared resting-limit processor fills ONLY when the bar trades to the level
  (short → `high >= level`, long → `low <= level`), else the limit expires.
- Post-fix the phantom diagnostic reports **0 phantom fills**.

The same machinery later powers the SBRS 3.0 limit-at-retest entry test
([[86-SBRS-3.0-Spec-And-Build]]).

## Instrumentation added (default = no behaviour change)
- `engine.REVERSAL_ENTRY_ENABLED` / `STRUCTURE_EXIT_ENABLED` — ablation toggles
  (default True). Used to measure each feature's contribution.

## Consequence
Once fills are realistic, the edge evaporates portfolio-wide →
[[84-Realistic-Fill-No-Edge]]. Harness: `tests/_audit_reversal_stats.py`.
