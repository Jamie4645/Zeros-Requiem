--
tags: [strategy, methodology, v2]
aliases: [Confluence Scoring, Confluence System, Entry Scoring]
related: [[47-SBRS-2.0-Upgrade]], [[50-Smart-Money-Indicators]], [[48-Ablation-Study-Results]], [[CLAUDE]], [[46-SBRS-Parameters-Reference]], [[00-MOC-Zeros-Requiem]]
---

> ⛔ **RETIRED (see root `CLAUDE.md`).** SBRS is fully retired — realistic-fill backtests found no
> edge on any instrument (PF 0.52–1.07), and the confluence-score ablation dollar figures below
> (FVG, Liquidity, MA Cross, Counter-Trend impacts) were measured on the pre-audit phantom-fill
> engine and are void. The ZTT rebuild does not inherit this scoring system. Retained as historical
> record only. Current strategy: ZTT (`knowledge-base/89-ZTT-Rebuild.md`).

# Confluence Scoring System — SBRS 2.0

**Date:** 2026-04-04
**Key innovation:** Replaces v1.1's binary MA-cross gate with a multi-signal scoring framework

---

## How It Works

After a valid structure break + retest, SBRS 2.0 scores the available confluence signals:

| Signal | Score | Ablation Impact |
|--------|-------|-----------------|
| Fair Value Gap (FVG) near level | +1.0 | CRITICAL (-$1,519 if removed) |
| Liquidity Sweep detected | +1.0 | VALUABLE (-$281 if removed) |
| MA Cross (WMA > SMMA for longs) | +0.5 | Reduced from 1.0 after ablation |
| Level Quality (3+ touches) | +0.5 | Minor positive |

The total score is compared against context-dependent thresholds:

| Trade Type | Min Score | Meaning |
|------------|-----------|---------|
| With-trend | >= 1.0 | At least 1 strong booster (FVG or Liquidity) |
| Counter-trend | >= 2.0 | Needs 2+ boosters (stringent) |
| Post-false-breakout | >= 2.0 | Extra conviction after prior failure |

---

## Why This Is Better Than v1.1's Binary Gate

**SBRS 1.1:** MA cross is required. No MA cross = no trade, regardless of other signals.

**SBRS 2.0:** MA cross is ONE of several signals. A trade can enter on FVG alone (1.0), Liquidity alone (1.0), or MA + Level Quality (0.5 + 0.5). This captures high-probability setups that v1.1 would miss because the MA hadn't crossed yet.

**The ablation study proved this is correct:** Test 4 (No MA Cross Score) actually IMPROVED results to $900 vs $513 baseline. FVG and Liquidity carry the real edge. MA cross is a supporting actor, not the lead.

---

## The MA Cross Score Reduction

Originally set to 1.0 (equal to FVG and Liquidity). The ablation study showed that reducing it to 0.5 forces trades to have a stronger signal (FVG or Liquidity) alongside the MA cross, rather than entering on MA cross alone. This improved the signal-to-noise ratio.

---

## Counter-Trend Scoring

Counter-trend trades (against 4H trend) require score >= 2.0:
- TP is placed at 70% of distance to previous swing extreme (conservative)
- Min R:R reduced to 2.0 (from 3.0 for with-trend)
- Ablation showed removing counter-trend costs $807 — they add genuine value

---

## Implementation

Located in `src/regimes/sbrs_v2.py`, lines ~708-745 of the `analyze_sbrs_v2()` function.

---

## Related

- [[50-Smart-Money-Indicators]] — The individual signals that feed into scoring
- [[48-Ablation-Study-Results]] — How each signal's weight was validated
- [[47-SBRS-2.0-Upgrade]] — The strategy this system belongs to
- [[00-MOC-Zeros-Requiem]]
