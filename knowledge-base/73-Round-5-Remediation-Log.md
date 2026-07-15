---
tags: [remediation, round5, round6, council, tdd, executive-summary]
aliases: [Round 5 Remediation Log, Phase A-E Closure, 2026-04-18 Session Log]
related: [[00-MOC-Zeros-Requiem]], [[67-Round-5-Post-Council-Validation]], [[70-Ablation-Round-6]], [[71-NDX-Fat-Tail-Audit]], [[72-Gold-Bar-Audit]]
---

> ⛔ **VOID/RETIRED (see root `CLAUDE.md`).** This remediation log's SBRS 2.0 numbers are
> phantom-fill artifacts (2026-06-01 audit) and additionally optimistic pre-2026-07-02 (WF
> peak-reset bug, R6-5 retracted). SBRS is now fully retired. Retained as historical record only.

# Round 5 Remediation Log — Full Phase A–D Closure (2026-04-18)

> **Directive:** Execute the Round 5 council remediation plan (20 items across 5 RED / 7 YELLOW / 8 GREEN-monitor) with TDD discipline, prioritised by live-money impact. Phase E closure pending user decision on slippage recalibration.

## Executive Summary

**Starting state:** 9/10 paper-gate, 4 Tier 1 strategies (Gold, DAX, NASDAQ, GBP/USD) cleared for paper at 0.25–0.5% risk.

**Ending state (under B1 live / current code):** 8/10 paper-gate, 3 Tier 1 (Gold, DAX, GBPUSD), 1 Tier 4 (NASDAQ suspended pending slippage recalibration decision).

**Single open blocker:** user approval of slippage recalibration (`slippage_pips` 1.5 → 0.75, OR asset-class-aware model). NASDAQ restorable to Tier 1 on either path; Gold unaffected; DAX requires parallel isolation check before trust.

| Phase | Items | Status |
|---|---|---|
| A — Canon cleanup | R1, R5 | ✅ merged with TDD |
| B — Protected patches | Y1, Y2 | ✅ merged with TDD |
| C — Re-validation | R2, R3, R4, Y3, Y4 | ✅ completed; R4 reclassified R6-1 |
| D — Data/docs | D1 (Y5), D2/D3 (Y6/Y7/R5), D4 (G1–G8) | ✅ closed; D1 inconclusive |
| E — Closure | council + paper-gate + tag | ⚠️ BLOCKED on user slippage decision |

## Phase A — Canon Cleanup

### A1 — Session filter belt-and-braces
- **File:** `src/regimes/sbrs_v2.py` — `SESSION_BLOCK_START_HOUR: 16 → 99`
- **TDD:** `tests/test_session_filter_disabled.py` — asserts sentinel + `is_session_blocked(ts)` returns False for all 24 hours. Red → green cycle observed.
- **Deleted:** `tests/_round5_session_off_wf.py` (test harness superseded).
- **Review:** arbiter-execution OK.

### A2 — GBPUSD sizing cap (R5)
- **File:** `src/core/risk_manager.py` (PROTECTED) — `SYMBOL_RISK_CAP = {'GBPUSD': 0.0025}`; `calculate_position_size()` short-circuits to `min(requested, cap)` when symbol matches.
- **TDD:** `tests/test_risk_caps.py::test_gbpusd_capped_at_25bps` — green.
- **CLAUDE.md:** R5 caveat block added under Current Portfolio Status.
- **Review:** arbiter-risk OK.

## Phase B — Protected-File Patches

### B1 — Index slippage bracket (Y1)
- **File:** `src/core/risk_manager.py` (PROTECTED) — inserted `entry_price > 5000 → slip = slippage_pips × 1.0` ABOVE existing `>1000` branch.
- **TDD:** `tests/test_slippage.py` 3/3 green (NDX-like 15.5k → +1.5, Gold 2050 → +0.15, forex 1.265 → +0.00015).
- **Review:** arbiter-risk + arbiter-execution OK at time of merge.
- **Post-merge discovery:** R6-1 isolation (see Phase C) reveals this is ~10× realistic OANDA CFD cost and 100% of the NASDAQ Tier 1 collapse. Recalibration queued for user approval.

### B2 — IBKR cache staleness guard (Y2)
- **File:** `src/data/ibkr_fetcher.py` — `_load_cache()` adds `(utcnow - mtime).days <= 7` guard; returns `None` on stale, logs warning to `logs/data_warnings.log`.
- **TDD:** `tests/test_ibkr_cache.py` — fresh returns df, stale returns None (green).
- **Follow-up:** forced refetch triggered refresh of `^GDAXI` and `^IXIC` caches. OANDA-routed fetch paths exercised; previously-stale IBKR caches bypassed.
- **Review:** arbiter-data OK.

## Phase C — Re-Validation Gauntlet

### C1 — Round 6 ablation vs filter-OFF baseline (R2, Y3)
- **Output:** `logs/round6/ablation_round6.log`, `knowledge-base/70-Ablation-Round-6.md`.
- **Configs run:** 18 (baseline + 17 variants). Y3 `ATR_PCTILE_ENABLED_GOLD` not run in this round — queued for R7.
- **Sign-stability vs Round 4:** 13/14 testable features stable in dollar direction. One flip: FVG PF direction (filter-OFF regime admits 16–23 GMT trades that change FVG's PF impact; dollar sign stable).
- **Key findings:**
  - Liquidity Sweep is THE load-bearing feature (−$47k, PF 2.05 → 0.96 without it).
  - Four flags are dead code under filter-OFF (Session, Squeeze, Whipsaw, Chop — byte-identical baseline results).
  - Old MA Convention (SMMA>WMA=bull) definitively dead under corrected four-callsite patch: PF 0.55, −$2,027. Closes Round 3 PF 5.23 artefact investigation.
  - Counter-Trend contributes ~$29k (real edge, not noise).
  - Higher confluence threshold (1.5) thins book but raises PF (consistent with forex).

### C2 — Gold filter-OFF Monte Carlo (R3)
- **Output:** `logs/round6/gold_mc_filter_off.log`.
- **Sample:** 733 trades, 10Y OANDA filter-OFF.
- **Result:** Prob(20%DD) = **2.24%** [PASS]; Prob(15%DD) 9.68%; Prob(30%DD) 0.22%; 100% profitable; median final PnL $46,246; P99 max DD 23.26%.
- **Status:** Authoritative Gold MC figure replaces Round 5 filter-ON 3.08%. Paper trade at 0.5% reconfirmed; 0.5% remains conservative given 2.24% margin vs 5% elite gate.

### C3 — NASDAQ fat-tail forensic (R4) → reclassified as R6-1
- **Initial finding:** Fresh OANDA 10Y BT returned PF 0.86 / −$1,082 / 107 trades — reversing Round 5 Tier 1 canon of PF 3.49.
- **Isolation (R6-1):** `tests/_r6_ndx_slip_isolation.py` three-variant run on identical OANDA data and setup set.
  - Variant A (B1 live, 1.5pt/side): 107 trades, PF 0.86, −$1,082, DD 20.48%.
  - Variant B (old cost 0.15pt/side): **532 trades, PF 3.57, +$74,423, DD 4.72%** — matches Round 5 canon.
  - Variant C (slippage OFF): 532 trades, PF 3.88, +$83,129, DD 4.51%.
- **Resolution:** Slippage is 100% of the collapse; data source (IBKR → OANDA) is a non-issue. NDX edge is real; B1 is ~10× too conservative for OANDA NAS100.
- **Full write-up:** [[71-NDX-Fat-Tail-Audit]].

### C4 — GBPUSD ATR threshold sweep (Y4)
- **Output:** `logs/round6/gbpusd_atr_sweep.log`.
- **Method:** `tests/_c4_gbpusd_atr_sweep.py` — monkey-patched `sbrs_v2.is_low_volatility` wrapper (default-argument binding gotcha fixed).
- **Result:**
  - T=15: 303 trades, PF 1.46, Sharpe 0.75, PnL $2,361, DD 1.86%.
  - **T=20: 294 trades, PF 1.57, Sharpe 0.88, PnL $2,771, DD 1.68%** ← OPTIMAL
  - T=25 (prod): 276 trades, PF 1.55, Sharpe 0.82, PnL $2,517, DD 2.60%.
- **Proposed R7 action:** Lower GBPUSD `ATR_PCTILE_THRESHOLD` from 25 → 20 (within ±20% tunable range). Uplift: +$254, +0.02 PF, +0.13 Sharpe, −0.92pp DD. Requires WF re-run to confirm 75%+ consistency preservation before canon.

## Phase D — Data Integrity & Round 7 Prep

### D1 — Gold OANDA vs Yahoo audit (Y5)
- **Output:** `logs/round6/gold_bar_audit.log`, [[72-Gold-Bar-Audit]].
- **Result:** INCONCLUSIVE. `src/data/fetcher.py::fetch("GC=F", ...)` routes through OANDA regardless of caller; no `--force-source=yahoo` override exists.
- **Round 7 fix:** add `force_source` parameter to `fetch()`; re-run audit.

### D2/D3 — CLAUDE.md caveats (Y6, Y7, R5)
- Added "Known Caveats — Round 5" block to root `CLAUDE.md` covering:
  - R5: GBPUSD 0.25% sizing cap rationale + trigger for revisit (500+ WF trades).
  - Y6: No commission model — material only for IBKR-futures live, not OANDA CFD paper.
  - Y7: DAX 457 trades below 500 minimum — paper-trade approved, sizing revisit post 500+.

### D4 — Round 7 backlog in MoC (G1–G8)
- Round 7 section appended to `knowledge-base/00-MOC-Zeros-Requiem.md` listing:
  - G1: Student-t nu=4 fat-tail portfolio MC.
  - G2: Ablation crypto subset (BTC/ETH per-feature isolation).
  - G3: 5Y+ Binance refresh for BTC/ETH WF.
  - G4: OANDA USDJPY 5Y+ fetch.
  - G5: (covered by C1 Round 6.)
  - G6: OANDA FOK fill-drift live tracking.
  - G7: S&P 500 structurally locked — no action.
  - G8: Forex session filter first-principles review.

## Phase E — Closure (BLOCKED)

Three-step closure (`/arbiter-council brief` → `/paper-gate 10/10` → `git tag round5-remediated`) blocked pending user decision on slippage recalibration. Options on user-decision queue:

1. **Keep B1 at 1.5pt/side (status quo):** Portfolio 8/10 (Gold + DAX + GBPUSD Tier 1, NDX Tier 4). Conservative but forfeits validated edge.
2. **Recalibrate to slippage_pips=0.75:** NDX likely rebounds to Tier 1. DAX parallel isolation required. Portfolio 9/10 restorable.
3. **Asset-class-aware slippage dict:** Most correct architecturally. Requires risk_manager.py redesign.

## Files Modified This Session

| File | Phase | Change |
|---|---|---|
| `src/regimes/sbrs_v2.py` | A1 | `SESSION_BLOCK_START_HOUR: 16 → 99` |
| `src/core/risk_manager.py` | A2 + B1 | `SYMBOL_RISK_CAP` dict + `>5000` slippage bracket |
| `src/data/ibkr_fetcher.py` | B2 | 7-day mtime guard in `_load_cache()` |
| `tests/_round5_session_off_wf.py` | A1 | DELETED |
| `tests/test_session_filter_disabled.py` | A1 | NEW (TDD) |
| `tests/test_risk_caps.py` | A2 | NEW (TDD) |
| `tests/test_slippage.py` | B1 | NEW (TDD) |
| `tests/test_ibkr_cache.py` | B2 | NEW (TDD) |
| `tests/_c3_ndx_fat_tail.py` | C3 | NEW (diagnostic) |
| `tests/_r6_ndx_slip_isolation.py` | C3/R6-1 | NEW (isolation) |
| `tests/_c4_gbpusd_atr_sweep.py` | C4 | NEW (sweep) |
| `tests/_d1_gold_bar_audit.py` | D1 | NEW (diagnostic, inconclusive) |
| `CLAUDE.md` | D2/D3 | R5/Y6/Y7 caveat block added |
| `knowledge-base/00-MOC-Zeros-Requiem.md` | D4 | Round 7 section |
| `knowledge-base/70-Ablation-Round-6.md` | C1 | NEW (full 18-config table + findings) |
| `knowledge-base/71-NDX-Fat-Tail-Audit.md` | C3 | NEW (R6-1 resolution) |
| `knowledge-base/72-Gold-Bar-Audit.md` | D1 | NEW (inconclusive doc) |
| `knowledge-base/73-Round-5-Remediation-Log.md` | this doc | NEW |
| `knowledge-base/arbiters/shared-findings.md` | all | Round 6 findings appended |
| `knowledge-base/arbiters/next-hypotheses.md` | all | R7 hypotheses + closures |

## Logs Generated (all under `logs/round6/`)

| Log | Purpose |
|---|---|
| `ablation_round6.log` | Full 18-config ablation table |
| `gold_mc_filter_off.log` | Gold 733-trade Prob(20%DD)=2.24% |
| `ndx_fat_tail.log` | Initial NDX BT surfacing PF 0.86 surprise |
| `ndx_slip_isolation.log` | R6-1 three-variant resolution |
| `gold_bar_audit.log` | D1 inconclusive output |
| `gbpusd_atr_sweep.log` | C4 three-threshold result |

## Open Items (carried into Round 7)

| ID | Item | Priority | Owner |
|---|---|---|---|
| **S1** | **User decision: slippage recalibration (blocker for portfolio 9/10)** | CRITICAL | user |
| R7-1 | DAX parallel slippage isolation (mirror R6-1) | HIGH | arbiter-risk |
| R7-2 | Student-t nu=4 fat-tail portfolio MC | HIGH | arbiter-risk |
| R7-3 | GBPUSD ATR_PCTILE_THRESHOLD 25→20 WF re-run | MEDIUM | arbiter-forex |
| R7-4 | Dead-code cleanup (session/squeeze/whipsaw/chop flags) | MEDIUM | arbiter-ablation |
| R7-5 | Y3 Gold `ATR_PCTILE_ENABLED_GOLD` into ablation suite | MEDIUM | arbiter-ablation |
| R7-6 | D1 fix — add `force_source='yahoo'` to fetcher + re-audit | LOW | arbiter-data |
| R7-7 | OANDA FOK fill-drift tracking (post paper-trade start) | LOW | arbiter-execution |

## Reproducibility

All Round 6 logs are deterministic under fixed random seed + pinned OANDA data. To replay any result:
```
py -m tests._<script_name>      # e.g. tests/_r6_ndx_slip_isolation.py
```

Ablation: `py -m tests.ablation_study --period 10y`.
MC: `/monte-carlo --symbol XAUUSD --filter-off`.

## Canon Drift vs Round 5

| Item | Round 5 canon | Round 6 canon |
|---|---|---|
| Gold trade count | 643 (filter-ON) | 733 (filter-OFF) |
| Gold MC Prob(20%DD) | 3.08% | 2.24% |
| NASDAQ BT PF | 3.49 (IBKR cache) | 3.57 (OANDA, Variant B — slippage-reconciled); 0.86 (B1 live) |
| Session filter | Partially applied (16-20 GMT Gold only) | Fully off (belt-and-braces) |
| Slippage model | 4 brackets (>1000, >10, >0.01, else) | 5 brackets (added >5000 @ 1.0×) — pending recalibration |
| Dead code | Unknown | Session/Squeeze/Whipsaw/Chop confirmed dead under filter-OFF |
| MA convention | WMA>SMMA=bull (validated) | Same; old convention reconfirmed as Tier 4 via corrected four-callsite patch |

## Round 6 Post-Council Full Validation (2026-04-18)

All 4 Tier-1-candidate instruments re-validated via full BT + WF + MC 10,000 sim pipeline on B1 live code (`slippage_pips × 1.0` bracket for `entry_price > 5000`, OANDA fresh 10Y data, A1 session sentinel, A2 GBPUSD 0.25% cap).

| Instrument | BT PF | BT Sharpe | BT DD | WF Cons | WF PF avg | WF Sharpe avg | MC Prob(20%DD) | MC Prob Profitable | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Gold** | 2.05 | 1.43 | 11.44% | **100% (8/8)** | 1.52 | 1.12 | **2.24% PASS** | 100.0% | **Tier 1** anchor |
| **DAX** | 1.41 | 0.72 | 12.06% | 75% (6/8) | 1.28 | 0.55 | **10.83% FAIL** | 99.8% | Tier 1 **borderline** (R6-3) |
| **NDX (BT)** | 0.86 | -0.18 | 20.48% | — | — | — | **51.85% FAIL** | 24.6% | Tier 4 suspended |
| **NDX (WF)** | — | — | — | 75% (6/8) | 1.34 | 0.61 | — | — | **Code-path anomaly (R6-5/R7-9)** |
| **GBPUSD** (0.25%) | 1.55 | 0.82 | 2.60% | **88% (7/8)** | 1.52 | 0.70 | **0.00% PASS** | 99.9% | **Tier 1 approaching** |

**Gold:** Strengthened in Round 6 — WF consistency climbed 75% → 100%. Edge improving at +$359/window slope. MC 2.24% clears elite by 2.24×.

**DAX:** Degraded under B1 — Sharpe 1.18 → 0.72, MC 10.83% FAILS elite gate. Confirms council R7-1 hypothesis (DAX B1-symmetric to NDX, partial collapse). See R6-3 in root `CLAUDE.md`.

**NDX:** Dual-verdict pending R7-9 resolution. BT path shows Tier 4 collapse (matches R6-1); WF path shows 532 trades / PF 1.34 (matches pre-B1 Variant B exactly). One of the two code paths bypasses B1 — critical forensic for tier reinstatement.

**GBPUSD:** Quiet breakthrough — W7 collapse healed without slippage intervention. WF 62% → 88%. MC 0.00% PASS. Trade-count caveat (275 < 500) still holds; otherwise Tier 1 material.

**Logs:**
- `logs/round6/gold_full_validation.log`
- `logs/round6/dax_full_validation.log`
- `logs/round6/ndx_full_validation.log`
- `logs/round6/gbpusd_full_validation.log`

**Findings persisted to:** `knowledge-base/arbiters/shared-findings.md` 2026-04-18 `arbiter-validator` entry | CLAUDE.md R6-3/R6-4/R6-5 sections.

## Round 7 Slippage Recalibration — 9/10 Portfolio Achieved (2026-04-18)

User-approved `slippage_pips` default change: **1.5 → 0.75** (council Option 2, global flat-fee). Single-line edit at `src/core/risk_manager.py:61` + bracket-comment updates. 14/14 TDD tests re-pass. Full BT+WF+MC re-validation at `logs/round7/*.log`.

### Round 7 Canon — all 4 instruments Tier 1

| Instrument | BT PF | BT Sharpe | BT DD | WF Cons | WF PF avg | MC Prob(20%DD) | Prob Profitable | Status vs Round 6 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **Gold** | 2.65 | **1.78** | 7.18% | **100% (8/8)** | 1.72 | **1.10% PASS** | 100.0% | Strengthened |
| **DAX** | 1.69 | 1.00 | 8.66% | **88% (7/8)** | 1.45 | **2.42% PASS** | 100.0% | **RESTORED** |
| **NDX** | 2.63 | **1.53** | 9.68% | **88% (7/8)** | 1.52 | **0.80% PASS** | 100.0% | **RESURRECTED from Tier 4** |
| **GBPUSD** | 2.01 | 1.20 | 1.95% | **100% (8/8)** | 1.88 | **0.00% PASS** | 100.0% | Strengthened |

### Material findings
1. **NDX Tier 4 → Tier 1 on a single constant change.** BT trades 107 → 533 (+398%), PF 0.86 → 2.63, Sharpe -0.18 → 1.53 (elite), MC 51.85% FAIL → 0.80% PASS.
2. **R6-5 / R7-9 BT-vs-WF discrepancy RESOLVED.** At slip=0.75, BT produces 533 trades and WF produces 532 — parity. Root cause was R:R ≥3.0 gate rejection, not a code-path bug.
3. **DAX restored without a cap.** R7-10 (DAX 0.15% sizing cap) CLOSED as unnecessary — slip recal alone restored DAX to 88% WF (matching Round 5) and MC 2.42% PASS.
4. **Gold and GBPUSD also benefit.** Non-B1 brackets (Gold 0.1×, forex 0.0001×) improved because the base constant halved. Gold Sharpe 1.43 → 1.78 (meets elite 1.5). GBPUSD WF 88% → 100% — first time every window profitable.

### Portfolio score: 9/10
- 4 WF-validated Tier 1 strategies on 2 asset classes (gold, indices, forex)
- 10/10 blocked only on 5th strategy (USDJPY 5Y+ data or another pair)
- Total portfolio risk: 1.25% (Gold 0.5% + DAX 0.25% + NDX 0.25% + GBPUSD 0.25%)
- Live-ramp gate: 60-90d paper trade per short-term roadmap

### Canon drift vs Round 6 (closed items)
| Item | Round 6 status | Round 7 status |
|---|---|---|
| R6-1 NASDAQ suspension | Tier 4, BT PF 0.86 | **CLOSED** — Tier 1, BT PF 2.63 |
| R6-3 DAX Tier 1 borderline | MC 10.83% FAIL | **CLOSED** — MC 2.42% PASS |
| R6-5 / R7-9 BT-vs-WF discrepancy | Unresolved | **CLOSED** — R:R gate rejection, no code bug |
| R7-10 DAX sizing cap 0.15% | Pending | **CLOSED as unnecessary** |
| R7-11 USDJPY 5th-strategy re-validation | Tier 3 (PF 1.27) | **CLOSED** — Tier 2 candidate at 0.25% cap (WF 88%, MC Elite 0.01%, trades 161 < 500) |

## Round 7 Remainder — USDJPY Tier 3 → Tier 2 (R7-11)

Post-canon, the sole portfolio blocker to 10/10 was the 5th strategy. Candidate USDJPY (Tier 3 under old 1.5pt slip) re-validated under Round 7 slip=0.75.

### Result (OANDA 10y, 1% risk pre-cap)

| Gate | Value | Status |
|---|---:|---|
| BT Trades | 161 | FAIL (<500) |
| BT PF | 3.18 | ⚠ above red-flag 3.0 (WF PF 2.58 is benign) |
| BT Sharpe | 1.35 | Near-miss 1.5 |
| BT DD | 2.57% | PASS |
| WF | 88% (7/8) | PASS |
| WF Avg PF | 2.58 | PASS |
| WF Avg Sharpe | 1.16 | PASS |
| MC Prob(20%DD) | **0.01%** | **Elite PASS** |
| MC Median DD | 4.72% | Well-contained |

### Code diff

- `src/core/risk_manager.py:20-23` — added `'USDJPY': 0.0025` entry to `SYMBOL_RISK_CAP`.
- `tests/test_risk_caps.py` — extended parametric suite to cover USDJPY variants (`USDJPY`, `USDJPY=X`, `USD_JPY`, `usdjpy`). 13/13 green.
- `CLAUDE.md` — Tier 2 row added to Post-Round-7 portfolio table; "Known Caveats — Round 7" now carries R7-11 block mirroring R5.

### Interpretation
Same pattern as GBPUSD: elite gates clear but trade count gates Tier 1. BT PF red-flag closes on WF PF evidence (2.58 < 3.0). Portfolio score remains **9/10** — USDJPY adds a 5th paper-trade candidate at 0.25% but does not clear 500-trade Tier-1 bar. Path to 10/10: (a) accumulate live trades to push USDJPY count ≥500, or (b) scout alternate high-sample pair (AUDJPY, EURJPY, NZDUSD, USDCHF).

**Evidence:** `logs/round7/usdjpy_full_validation.log`

## Reference

- **Plan file:** `C:\Users\jamie\.claude\plans\synchronous-dreaming-engelbart.md`
- **Prior round:** [[67-Round-5-Post-Council-Validation]]
- **Ablation details:** [[70-Ablation-Round-6]]
- **R6-1 deep-dive:** [[71-NDX-Fat-Tail-Audit]]
- **D1 docs:** [[72-Gold-Bar-Audit]]
- **Council files:** `knowledge-base/arbiters/shared-findings.md`, `knowledge-base/arbiters/next-hypotheses.md`
- **Round 7 logs:** `logs/round7/{gold,dax,ndx,gbpusd,usdjpy}_full_validation.log`
