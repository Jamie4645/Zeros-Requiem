--
tags: [research, strategy, discovery]
aliases: [MA Convention, WMA SMMA Convention, MA Cross Direction]
related: [[47-SBRS-2.0-Upgrade]], [[48-Ablation-Study-Results]], [[CLAUDE]], [[46-SBRS-Parameters-Reference]], [[00-MOC-Zeros-Requiem]]
---

# MA Convention Discovery — The $3,300 Finding

**Date:** 2026-04-05
**Impact:** Single most impactful discovery in the project's history

---

## The Question

The methodology document (17 discretionary trades) states:
> *"SMMA crossing above WMA confirms a long bias. WMA crossing above SMMA confirms a short bias."*

The original SBRS 1.1 code used the OPPOSITE:
> WMA crossing above SMMA = bullish (for longs)

Which is correct for the algorithm?

---

## The Investigation

### Phase 1: We "Fixed" It (Bad Move)

Based on the methodology document, the MA convention was changed to match:
- SMMA > WMA = bullish (longs)
- WMA > SMMA = bearish (shorts)

**Result on 10Y Gold:** 57 trades, PF 1.14, $513 PnL

### Phase 2: Ablation Study Revealed the Truth

Test 11 of the ablation study reverted to the original convention:
- WMA > SMMA = bullish (longs)
- WMA < SMMA = bearish (shorts)

**Result on 10Y Gold:** 167 trades, PF 1.36, $3,814 PnL

**The "fix" had destroyed $3,300 of profit and eliminated 110 trades.**

### Phase 3: Applied the Revert

After applying all ablation-driven changes (including the revert):
**Final result:** 2,252 trades, PF 1.97, $146,256 PnL

---

## Why the Original Convention Works Better for the Algo

The key insight is about what each indicator represents:

| Indicator | Type | Behavior |
|-----------|------|----------|
| WMA(9) | Weighted, 9-period | Fast, responsive, leads price |
| SMMA(7) | Smoothed (recursive), 7-period | Slow despite shorter period, lags |

SMMA uses a recursive formula (MetaTrader-style) that makes it inherently smoother than its period suggests. Even with period 7, it moves slower than WMA(9).

**WMA crossing above SMMA = faster momentum indicator leading** = the market is accelerating upward. This is a MOMENTUM signal.

**SMMA crossing above WMA = the lagging indicator catching up** = price was already up, now the slow average confirms. This is a CONFIRMATION signal, not a leading signal.

For an algo that needs to enter AT the retest (time-sensitive), momentum is more valuable than lagging confirmation. The discretionary trader can afford to wait for lagging confirmation because they make subjective judgment calls. The algo cannot.

---

## The Lesson

> **What works in discretionary trading does not always translate 1:1 to systematic trading.**

The methodology document accurately describes how the trader reads the MAs. But the algo's time-critical entry at the retest bar benefits from the faster, momentum-oriented convention.

This is NOT a bug — it's a legitimate difference between discretionary and systematic edge capture.

---

## Current Convention (Final)

```python
# In check_ma_cross():
# Long (bullish): WMA crosses above SMMA (momentum leading)
if w_curr > s_curr and w_prev <= s_prev: return True

# Short (bearish): WMA crosses below SMMA (momentum fading)
if w_curr < s_curr and w_prev >= s_prev: return True
```

Validated in:
- `src/regimes/sbrs_v2.py` — `check_ma_cross()`, `compute_4h_context()`
- `src/core/engine.py` — `manage_sbrs_v2_trade()`, `_check_ma_cross_inline()`

---

## Related

- [[48-Ablation-Study-Results]] — The study that uncovered this
- [[47-SBRS-2.0-Upgrade]] — Where the finding was applied
- [[46-SBRS-Parameters-Reference]] — Parameter reference
- [[00-MOC-Zeros-Requiem]]
