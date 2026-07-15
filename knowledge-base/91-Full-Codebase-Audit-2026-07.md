---
tags: [audit, codebase, remediation, governance, active]
aliases: [Full Codebase Audit July 2026, Audit 2026-07-02]
related: [[81-Audit-2026-06-01-Phantom-Fill]], [[88-Audit-Harness-Index]], [[90-Pre-Registered-Falsifier-ZTT]], [[92-Books-Blank-Slate-Review]]
---

# 91 — Full-Codebase Audit + Remediation (2026-07-02)

**Trigger:** user-requested from-scratch review of the entire codebase (dual workflow:
31-agent codebase audit — Review → adversarial Verify → Arbiter Council → Philosophical
Council → Synthesis; 48 findings raised, 10 confirmed serious). Companion review:
[[92-Books-Blank-Slate-Review]]. **All confirmed findings were remediated the same day**
(commits `a89e978`, `1c033d7`, `aabdacc` + canon commit).

## Council verdict (pre-remediation)
**HAS BLOCKING ISSUES — unanimous NOT READY from both councils.** The codebase was
"mechanically sound but economically dead"; safety rested on a prose banner, not code.
Red-Team dissent (accepted): "0.00% live" was a documentation claim, not a code
invariant. Kahneman dissent (accepted): the deepest defect is the institutional pattern
of manufacturing false validation — that pattern, not SBRS, is what ZTT inherits.

## Confirmed findings → fixes

| # | Sev | Finding | Fix (2026-07-02) |
|---|-----|---------|------------------|
| 1 | CRITICAL | `process_lock.py` locked a byte at EOF (`'a+'` open) — two processes lock disjoint bytes, both "acquire" the single-instance lock → duplicate OANDA orders | `seek(0)` before locking; verified with concurrent 2-process launch (2nd exits code 2) |
| 2 | HIGH | Live freeze enforced by discipline only; `engine_live.py` still ran 4 SBRS symbols @ R8 sizing, disagreeing with Gold-only `runner.py` | New `src/live/deploy_gate.py`: both order-placing entrypoints exit(3) unless `ZR_LIVE_TRADING_ENABLE` token set; engine_live reconciled to Gold-only |
| 3 | HIGH | `walk_forward.py` built a fresh RiskManager per window → peak_equity reset → drawdown breaker neutralized every window; WF (the promotion gate) systematically optimistic. **This is the real R6-5 mechanism — the canon "R:R gate" closure was false** | `run_backtest(initial_peak_equity=…)` + WF carries relative drawdown across windows; R6-5 closure retracted in CLAUDE.md |
| 4 | HIGH | `detect_liquidity_sweep` read swing masks needing 3 FUTURE bars — look-ahead in the +1.0 confluence booster | `swing_confirm_lag` cutoff, wired to SWING_WINDOW / SWING_W at both call sites; leak demonstrated + closed in test |
| 5 | HIGH | Adaptive-R:R gate `2.1 < 2.1` could never fire → with-trend Gold trades at 2.1R vs SACRED MIN_RR=3.0 | `ATR_RR_CLAMP_LOW` 0.7 → 1.0 (floor can never undercut MIN_RR); call-site gate now a real invariant |
| 6 | HIGH | `RETEST_TOLERANCE_ATR` 0.7 in code vs 0.5 in CLAUDE.md SACRED block; `test_sacred_params.py` pinned the drift as "NOT a test failure" | Canon was internally contradictory (its own v2.0 section documents 0.7 as ablation-validated, KB 46/59). SACRED block reconciled to 0.7/0.3; test now asserts code == canon, never blesses divergence |
| 7 | HIGH | Monte Carlo used IID trade resampling → destroys losing-streak autocorrelation → understates Prob(20%DD) | Circular moving-block bootstrap default (measured on clustered PnL: IID p95 streak 13 vs block 58; Prob(20%DD) 67% vs 91%); `method='iid'` kept for comparison |
| 8 | HIGH | Slippage classified by PRICE bracket: early NDX bars ≤5000 misfiled as Gold (~10× under-cost); Gold (now ~4,565) would misfile as an index >5000 (~10× over-cost) | Classification by `RiskConfig.asset_class`; price brackets retained only as legacy fallback |
| 9 | HIGH | `^IXIC` = NAS100 (Nasdaq-100) on OANDA but COMP (Composite) on IBKR — different indices under one symbol | Documented at both maps + loud runtime warning on the IBKR path; OANDA/NAS100 is canonical |
| 10 | HIGH | Test suite green ≠ safe: phantom-fill regression lived only in non-collected `_audit_*` harnesses; `test_engine_validation.py` never imported the engine and skipped entirely without vectorbt; WF/MC had zero tests | NEW collected tests: `test_phantom_fill_tripwire.py` (untouched limit must not fill; every fill inside its bar's range), `test_walk_forward_regression.py` (window coverage + drawdown carry), `TestEngineCrossValidation` (engine vs hand-computed PnL, runs without vbt) |

## Also fixed under the same audit (ZTT side, from [[92-Books-Blank-Slate-Review]])
- `ztt_screener.py` `_ensure_decisions_header` migrated on header mismatch (15-col
  decisions.csv would have been silently corrupted by 27-col appends); CSV migrated,
  original kept as `.bak`.
- `ztt_v2.py` `MAX_MOVE_PCT` reverted 0.020 → **0.015** (F3-validated frozen value;
  2.0% crept in 2026-06-14b without an F3 re-run).
- The entire ZTT era (ztt.py, ztt_v2.py, costs, regime, screener) + audit harnesses +
  KB 75–90 were **untracked in git** — all committed. "Frozen-by-rule" without version
  control was the same governance failure mode that produced the phantom-fill era.

## Canon corrections
- **R6-5 RETRACTED:** the "CLOSED — root cause was R:R gate rejection under 1.5pt slip"
  narrative is disproven; the per-window peak reset was the mechanism (see #3).
- **WF numbers pre-fix are optimistic:** any historical WF consistency score was computed
  with a per-window-reset drawdown breaker. All are already VOID via the phantom-fill
  banner; the fix matters for every FUTURE run (ZTT inherits the corrected gate).
- **"Zero skip wins" was wrong:** the 60-label file shows 3/30 skips positive — which
  actually *weakens* the hindsight-leakage red flag (0/30 was too clean).

## Standing rule (councils, accepted)
A green `pytest` is **not risk evidence** unless the phantom-fill tripwire, realistic
revalidation mechanics, and WF regression guards are in the collected suite — they now are.
Any future harness that guards economic validity must be a collected `test_*` file, not an
underscore script.
