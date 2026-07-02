--
tags: [validation, round-7, council, sbrs-v2, post-change, canonical]
aliases: [Round 7, Round 7 Canon, Round 7 Post-Validation, 2026-04-18 Canon]
related: [[67-Round-5-Post-Council-Validation]], [[70-Ablation-Round-6]], [[71-NDX-Fat-Tail-Audit]], [[73-Round-5-Remediation-Log]], [[00-MOC-Zeros-Requiem]]
---

# Round 7 — Post-Validation Canon

**Date:** 2026-04-18
**Trigger:** User approval of slippage recalibration blocker from Round 5 remediation (Phase E closure from [[73-Round-5-Remediation-Log]]).
**Scope:** R
e-run full BT + WF + MC on all Round 5/6 candidates under the recalibrated B1 bracket, promote/demote tiers accordingly, close open R6 items.
**Outcome:** 9/10 portfolio score restored. 4 Tier 1 + USDJPY Tier 2 candidate canonical.

---

## The Change That Unlocked Round 7

**Single source of drift:** the `entry_price > 5000 → slip = slippage_pips × 1.0` B1 bracket in `src/core/risk_manager.py::apply_slippage`.

| Parameter | Round 6 (B1 live, original) | Round 7 (recalibrated) |
|---|---:|---:|
| `slippage_pips` (B1 index bracket) | 1.5 pt/side | **0.75 pt/side** |
| Gold multiplier branch | 0.1 | 0.1 (unchanged) |
| Forex multiplier branch | 0.0001 | 0.0001 (unchanged) |

**Rationale:** Round 6 isolation ([[71-NDX-Fat-Tail-Audit]]) proved 100% of NDX's PF 3.49 → 0.86 collapse was the B1 bracket, not the data source flip. 1.5pt/side is ~10x realistic OANDA NAS100 CFD round-trip spread; 0.75pt/side matches realistic execution.

---

## Portfolio Status — Post Round 7 (CANONICAL)

**Score: 9/10.** 4 WF-validated Tier 1 strategies + USDJPY Tier 2 candidate (elite MC, sub-500 trade count). 10/10 gate requires 500+ trades on USDJPY or another 5th strategy clearing the elite bar.

| Tier | Strategy | Risk | WF | BT PF | BT Sharpe | MC Prob(20%DD) | Notes |
|---|---|---|---|---:|---:|---:|---|
| 1 | Gold (GC=F) | 0.5% | **100% (8/8)** | 2.65 | **1.78** | **1.10% PASS** | Anchor; edge improving |
| 1 | DAX (^GDAXI) | 0.25% | 88% (7/8) | 1.69 | 1.00 | **2.42% PASS** | Restored from Round 6 borderline |
| 1 | NDX (^IXIC) | 0.25% | 88% (7/8) | 2.63 | **1.53** | **0.80% PASS** | Full reversal from Round 6 Tier 4 suspension |
| 1 | GBPUSD=X | 0.25% | **100% (8/8)** | 2.01 | 1.20 | **0.00% PASS** | W7 healed; 275 trades < 500 caveat |
| 2 | USDJPY=X | 0.25% | 88% (7/8) | 3.18 ⚠ | 1.35 | **0.01% Elite PASS** | Round 7 validated. BT PF >3.0 red-flag (WF PF 2.58 benign); 161 trades < 500 blocks Tier 1 |

**Total portfolio risk:** 1.50% (5 strategies at documented per-symbol caps).
**Live-ramp gate:** 60-90d paper trade per short-term roadmap.

---

## Closed Items (Round 5/6 → Round 7)

### R6-1 — NASDAQ Tier 4 suspension → CLOSED (Tier 1 restored)
- **Before:** BT PF 0.86, 107 trades, MC Prob(20%DD) 51.85% FAIL under B1-live 1.5pt slip.
- **After:** BT PF 2.63, 533 trades, MC 0.80% PASS under 0.75pt slip.
- **Attribution:** 100% slippage recalibration. Data source (OANDA) unchanged.

### R6-3 — DAX Tier 1 borderline → CLOSED (elite restored)
- **Before:** BT PF 1.41, WF 75% (6/8), Avg Sharpe 0.55, MC 10.83% FAIL.
- **After:** BT PF 1.69, WF 88% (7/8), Sharpe 1.00, MC 2.42% PASS.
- **Attribution:** Slip recal only. No parameter changes. Y7 trade-count caveat (457 < 500) still holds; paper sizing capped at 0.25%.

### R6-4 — GBP/USD W7 collapse → CLOSED (healed in Round 5 remediation bundle)
- **Before (Round 5):** W7 21.5% WR / -$2,012 / WF 62% (5/8).
- **After (Round 7):** W7 31.4% WR / -$49.22 / WF 100% (8/8).
- **Attribution:** Round 5 remediation bundle (confluence tightening `CONFLUENCE_MIN_WITH_TREND_FOREX = 1.5` + session sentinel fix). Forex is immune to B1 slip recal (hits the 0.0001 multiplier branch).
- Trade count caveat (275 < 500) persists; `SYMBOL_RISK_CAP['GBPUSD'] = 0.0025` holds until count clears 500.

### R6-5 / R7-9 — NDX BT-vs-WF discrepancy → CLOSED (parity confirmed)
- **Before:** Same code, same state: BT 107 trades / PF 0.86 vs WF 532 trades / PF 1.34 — suggested `walk_forward.py` bypassed B1 bracket.
- **Root cause (found under recal):** R:R ≥3.0 gate rejection rate is non-linear in slippage. At 1.5pt slip, most setups fail the 3R projection and BT capital-state amplifies the starvation; WF's per-window capital resets mask it.
- **Verification under 0.75pt slip:** BT produces 533 trades, WF produces 532 trades — parity. Not a code-path bug.

### R7-10 — DAX sizing cap → CLOSED (unnecessary)
- Pre-recal proposal: hard-cap DAX at 0.15% as DD budget analogue of GBPUSD 0.25% cap.
- Post-recal: DAX restored to elite MC PASS; 0.25% paper sizing justified by numbers. No explicit cap needed beyond Y7 trade-count review.

### R7-11 — USDJPY promotion → CLOSED (Tier 3 → Tier 2 candidate)
- **Before:** Tier 3 marginal, PF 1.27 pre-recal.
- **After:** WF 88% (7/8), Avg PF 2.58, MC Elite PASS.
- **Blocker for Tier 1:** 161 trades < 500 minimum (avg 20/window).
- **Red-flag investigation:** BT PF 3.18 vs WF PF 2.58 — divergence is clustering artefact, not leakage. WF path is the deployment-relevant canon.
- **Sizing cap:** `SYMBOL_RISK_CAP['USDJPY'] = 0.0025` enforced until trade count clears 500 OR BT/WF divergence closes.

---

## What Round 7 Did NOT Change

- SBRS core parameters (WMA=9, SMMA=7, SWING_LOOKBACK=20, MIN_RR=3.0, RETEST_TOLERANCE_ATR=0.5) — **untouched**.
- SBRS 2.0 entry/exit logic — **untouched**.
- Forex slippage (0.0001 multiplier branch) — **untouched**.
- Gold slippage (0.1 multiplier branch) — **untouched**.
- Monte Carlo methodology (Gaussian P99) — unchanged. Student-t ν=4 upgrade queued as G2 backlog.

---

## Remaining Backlog (Carried from Round 5 / 6)

| Item | Description | Owner skill/agent |
|---|---|---|
| G1 | NDX live-promotion gate — lift from paper to live once fill-drift confirmed | `/paper-gate` + `arbiter-risk` |
| G2 | Fat-tail Monte Carlo (Student-t ν=4) — upgrade from Gaussian P99 | `/monte-carlo --tail` |
| G3 | Crypto per-asset FVG weight test — BTC/ETH FVG ∈ {0.75, 1.0} once 5Y+ Binance data fetched | `/data-refresh binance` → `/ablation` |
| G4 | USD/JPY 5Y+ depth — current 10Y OANDA gives 161 trades; assess whether IBKR depth raises count | `/data-refresh` |
| G6 | Paper-trade fill-drift tracking — `actual_fill_price` vs `backtest_expected_entry` validates 0.75pt index slip | `/live-status` recurring loop |
| G8 | Forex session filter review — widen 07:00-16:00 GMT if GBP/USD stays <500 trades | `arbiter-forex` |

G5, G7 locked (EUR/USD and S&P 500 do-not-pursue).

---

## Provenance

- Source of canon: `CLAUDE.md` lines 370–402 (Portfolio Status — Post Round 7, CANONICAL).
- Upstream evidence: [[71-NDX-Fat-Tail-Audit]] (R6-1 isolation), [[73-Round-5-Remediation-Log]] (Phase E blocker), [[67-Round-5-Post-Council-Validation]] (Round 5 baseline), [[70-Ablation-Round-6]] (feature ranking carried forward).
- Risk manager change: `src/core/risk_manager.py::apply_slippage` B1 bracket `slippage_pips` constant (1.5 → 0.75).
