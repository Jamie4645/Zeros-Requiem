# Round 8 Canon — Full Record

Date: 2026-04-19
Branch: `feature/council-of-high-intelligence`
Predecessor: Round 7 canon at CLAUDE.md line 380 (now retired)

---

## 1. What was done

1. Invoked `/council --full` (Philosophical, 18 members) on the R7 state.
2. Invoked `/arbiter-council` (Arbiter, 10 domain) on the same state.
3. Cross-referenced both councils' verdicts; identified the **convergent minority objection**: neither council endorsed R7's 1.50% allocation unconditionally.
4. Ran 4 measured convergent tests:
   - `tests/_r8_slip_sweep.py` → NDX SLOPE, DAX PLATEAU (32.2% vs 15.6% PF range)
   - `tests/_r8_gold_direction_regime.py` → Gold Long PF 2.84 / Short PF 2.40; all 3 regimes profitable
   - `tests/_r8_portfolio_studentt_mc.py` → exact t(4) copula MC at 1.50% (0.0% base, 0.0% stress)
   - `tests/_r8_portfolio_studentt_mc_110.py` → exact MC at evidence-weighted 1.10%
5. Derived the evidence-weighted allocation (see `76-Round-8-Evidence-Weighted-Sizing.md`).
6. Implemented governance upgrades U1–U10 (see `arbiters/governance-rules.md`).
7. Created 6 new Arbiter agents: canon-audit, falsifier, tail-risk, cost-skeptic, red-team, socrates.
8. Registered 5 pre-registered falsifiers with review time-boxes.
9. Rewrote CLAUDE.md to remove the "9/10" score label and substitute the evidence-weighted tier table.

## 2. Convergent findings across both councils

1. **Slip is the pivotal parameter.** A single change (1.5pt → 0.75pt) resurrected NDX and restored DAX between R6 and R7 — which means the 9/10 score was one parameter away from 7/10. Both councils flagged this as excessive parameter-sensitivity.
2. **Diversification is partially fake.** 3 of 5 strategies (NDX, DAX, GBPUSD) are mildly vol-compression / low-vol regime dependent. Only Gold is a structural R3 hedge.
3. **Canon lagged measurement by 1–2 rounds.** The Arbiter Council found several CLAUDE.md numbers that did not match the most recent log.
4. **USDJPY should not be in live.** Both councils' minority reports objected to the 0.25% live sizing given BT PF 3.18 > red-flag, 161 trades, and no direction/regime test.
5. **The council process itself lacked structural dissent.** The Arbiter Council had no mandatory devil's-advocate seat; the Philosophical Council had Socrates/Sun-Tzu but no canon-audit seat.

## 3. Divergences resolved

- **Philosophical Council** (Taleb + Aurelius barbell) wanted Gold-only at 0.50% plus cash buffer. **Arbiter Council** (risk + regime) wanted equal-weight 0.25% across all 5.
- Neither survived Round-3 crystallization. The third answer (evidence-weighted, 0.50 / 0.25 / 0.15 / 0.20 / 0.00) was derived by mapping each strategy's fragility profile to a sizing discount factor.

## 4. Governance upgrades implemented

| # | Upgrade | Where | Status |
|---|---|---|---|
| U1 | Problem-Restate Gate | `arbiter-socrates.md` + arbiter-council Step 0 | LIVE |
| U2 | Canon-Audit seat | `arbiter-canon-audit.md` | LIVE |
| U3 | Falsifier seat | `arbiter-falsifier.md` | LIVE |
| U4 | Minority Report + Scorecard | `arbiter-council.md` output template | LIVE |
| U5 | Tail-Risk seat | `arbiter-tail-risk.md` | LIVE |
| U6 | Cost-Skeptic seat | `arbiter-cost-skeptic.md` | LIVE |
| U7 | Red-Team seat + cross-check rule | `arbiter-red-team.md` + arbiter-council Step 0 | LIVE |
| U8 | Canon anti-drift ratchet | `governance-rules.md` U8 | LIVE |
| U9 | Time-boxed falsifier review | `governance-rules.md` U9 | LIVE |
| U10 | External anchor requirement | `governance-rules.md` U10 | LIVE |

## 5. Measured logs (evidence anchors)

- `logs/round7/gold_full_validation.log` — BT 731 trades / PF 2.65 / Sharpe 1.78 / $68,382
- `logs/round7/dax_full_validation.log` — BT 457 trades / PF 1.69 / Sharpe 1.00 / $16,914
- `logs/round7/ndx_full_validation.log` — BT 533 trades / PF 2.63 / Sharpe 1.53 / $49,823
- `logs/round7/gbpusd_full_validation.log` — BT 275 trades / PF 2.01 / Sharpe 1.20 / $3,991
- `logs/round7/usdjpy_full_validation.log` — BT 161 trades / PF 3.18⚠ / Sharpe 1.35 / $17,854
- `logs/round8/slip_sweep.log` — NDX SLOPE (32.2% PF range), DAX PLATEAU (15.6%)
- `logs/round8/gold_direction_regime_live.log` — Long PF 2.84, Short PF 2.40, all regimes positive
- `logs/round8/portfolio_studentt_mc_exact.log` — exact MC at 1.50% (base 0.0%)
- `logs/round8/portfolio_studentt_mc_110.log` — exact MC at 1.10% (base 0.0%, $6,468 expected)

## 6. Closed Round-7 caveats

- **R7 "9/10" scoreboard** — retired. Scoreboard is not a driver; falsifiers are.
- **R7-11 USDJPY Tier 2 promotion** — reversed. USDJPY paper-only until red-flag + trade-count gates clear.

## 7. Open at Round 9+

- 60–90d paper-trade reconciliation of realized slip vs 0.75pt assumption (Falsifier #1).
- USDJPY direction/regime mirror of the Gold R8 run.
- BT/WF re-run at R8 SYMBOL_RISK_CAP to confirm `SYMBOL_RISK_CAP[^IXIC / ^GDAXI / GC=F]` binds as expected (normalizer extension).
- BTC/ETH 5Y data sourcing (G3 backlog) — unchanged.

## 8. Amendment lock

This Round-8 canon is amendment-locked. Any change to per-strategy sizing, tier ranking, or governance rule (U1–U10) requires:
1. Council re-convene with fresh measurements.
2. `arbiter-canon-audit` freshness check passed.
3. User explicit approval cited in the amendment KB entry.
