---
tags: [sbrs-3.0, spec, structural-exits, rebuild, clean-slate]
aliases: [SBRS 3.0, Structural Exits, Clean Slate Spec]
related: [[85-Primary-Edge-Teardown]], [[87-Supervised-Rebuild]], [[46-SBRS-Parameters-Reference]], [[47-SBRS-2.0-Upgrade]], [[53-SBRS-2.1-Experiment]]
---

# 86 — SBRS 3.0: Clean-Slate Spec & Structural-Exit Build

User chose to "strip to a clean 3.0 spec first." Full spec:
`../docs/sbrs_3.0_spec.md`. Module: `src/regimes/sbrs_v3.py`. SBRS 2.0 left intact
for diff.

## Design principles
1. **Codify, don't invent** — every rule traces to the methodology or a measured win.
2. **Realistic fills only** (the fixed engine, [[83-Reversal-Fill-Fix]]).
3. **Earn-your-place ablation** — a feature ships only if removing it *hurts*
   realistic-fill PF. Default for everything is OFF.
4. **No self-deception gates** — BT clears elite gates before WF; WF before MC.
5. **Gold 1H first** (was; now superseded by the 5m–15m pivot — see
   [[87-Supervised-Rebuild]]).

## Kept vs cut (from [[85-Primary-Edge-Teardown]])
- **KEEP:** bare with-trend breakout-retest on clean levels (PF 1.07 floor).
- **CUT:** confluence scoring (anti-predictive), counter-trend, false-BO-level
  trades, the old reversal injection, limit-at-retest entry. All net-negative.

## Resolved design decisions (with user)
- **D1 Exits = STRUCTURAL, with room.** TP at a *significant* prior level in the
  trade direction (multi-touch / consolidation / origin of prior move), NOT a
  fixed 3R. For longs: the prior consolidation **low** / previous medium-big
  reversal (near edge), not the far high. SL beyond the broken/flip level with an
  ATR buffer (room). MIN_RR is a floor filter only.
- **D2 MA convention = SMMA > WMA bullish** (the methodology doc), reverting the
  2.0 WMA>SMMA (which was validated only on phantom data — see
  [[49-MA-Convention-Discovery]]).
- **D3/D4 Smart-money + reversal = OUT of baseline; ablate later** on the 3.0
  structural-exit foundation, each must earn its place.

## Implementation
`sbrs_v3.py` = bare-core v2 entries (confluence/counter-trend/false-BO OFF, doc
convention) + `apply_structural_exits` overlay:
- SL = `broken_level ∓ SL_BUFFER_ATR*ATR`.
- TP = nearest multi-touch level (`count_level_touches ≥ TP_MIN_TOUCHES`) in the
  trade direction (`tp_mode` near/far).
- Reuses the [[83-Reversal-Fill-Fix|realistic limit-fill]] machinery; no reversal.

## Result — still no edge (Gold 10Y realistic)
`tests/_audit_sbrs_v3.py`, `logs/audit/sbrs_v3.log`:

| Variant | Trades | PF | PnL |
|---|---:|---:|---:|
| v3 near (3R floor) | 11 | 0.00 | −$1,808 |
| **v3 far (3R floor)** | 53 | **0.98** | −$80 |
| v3 near (no floor) | 60 | 0.34 | −$2,089 |
| v3 far (no floor) | 71 | 0.66 | −$1,689 |
| *baseline (fixed 3R)* | *348* | *1.07* | *+$1,431* |

Best structural variant is breakeven (PF 0.98), still under the simple fixed-3R
baseline. **Conclusion: the user's discretionary breakout-retest, faithfully
codified across every tested dimension, does not produce a deployable 1H edge.**
The edge lives in discretionary judgment the narrative rules don't capture →
[[87-Supervised-Rebuild]].
