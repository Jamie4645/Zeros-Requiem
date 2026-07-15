"""
MPB — MA Pullback-Bounce (intraday Gold, 10m).

Pre-registered fresh-strategy candidate #1 (KB `knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md`,
frozen 2026-07-04, BEFORE any backtest). NO horizontal level, NO break, NO retest — the
geometry falsified in ZTT stays dead. In an established WMA(144) trend with efficient price
movement (ER gate), enter on a pullback that touches SMMA(5) and is rejected by the next
candle's close; structural stop; %-capped TP.

Design pillars:
  * Trend context = price on trend side of WMA(144) AND WMA(144) slope over SLOPE_WIN bars
    agreeing with trade direction — both evaluated AT the touch bar t.
  * Efficiency gate: ER(10) at t > ER_MIN (Kaufman noise/ER; same 0.30 already frozen as
    MIN_EFFICIENCY in ZTTParams — reused, not re-fit). ER math imported from ztt_regime.
  * Entry trigger: bar t touches/pierces SMMA(5) against the trend; bar t+1 CLOSES back on
    the trend side of SMMA(5) with a directional body. Setup entry_index = t+1;
    `ztt_sim.simulate` fills at the OPEN of t+2 (honest next-bar-open, phantom-fill assert).
  * Stop: pullback extreme (min/max of bars t and t+1) +/- SL_BUFFER_ATR x ATR(14) buffer,
    rejected outside the [SL_MIN_PCT, SL_MAX_PCT] band of entry (user's observed SL band +
    cost-realism floor).
  * TP: RR_TARGET x SL distance, capped at TP_CAP_PCT of entry; rr recomputed after the cap;
    setup rejected if capped rr < RR_FLOOR.
  * CAUSAL: every value used at bar t is computable from bars <= t; the t+1 rejection values
    only use bar t+1 (the entry bar itself). No .shift(-1), no future windows.

This module produces setup objects only — fills / PnL / costs live in
`analysis/real_trades/ztt_sim.py::simulate` (the ONE honest fill engine). Validation is the
pre-registered N1–N8 gauntlet in KB-93; nothing here runs a backtest.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from src.indicators.technical import wma, smma, atr
from src.regimes.ztt_regime import _efficiency_ratio


# ════════════════════════════════════════════════════════════════════════
# Parameters — SACRED (user's indicators) + FROZEN mechanization (KB-93, 2026-07-04)
# Pre-registered grid is the ONLY sanctioned variation: ER_MIN in {0.25, 0.30, 0.35}
# x RR_TARGET in {1.7, 1.8, 2.0}. Everything else frozen. Overrides go through this
# Params object ONLY — generate_setups takes no hidden kwargs.
# ════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class MPBParams:
    # ── SACRED — the user's own indicators, never optimized ──
    WMA_PERIOD: int = 144
    SMMA_PERIOD: int = 5
    ATR_PERIOD: int = 14
    # ── FROZEN mechanization (KB-93) ──
    SLOPE_WIN: int = 20          # bars — WMA slope window for the trend gate
    ER_WIN: int = 10             # Kaufman Efficiency Ratio window
    ER_MIN: float = 0.30         # ER gate (grid axis 1)
    SL_BUFFER_ATR: float = 0.10  # x ATR beyond the pullback extreme
    SL_MAX_PCT: float = 0.0045   # reject SL distance > 0.45% of entry (user's band)
    SL_MIN_PCT: float = 0.0015   # reject SL distance < 0.15% of entry (cost realism)
    RR_TARGET: float = 1.8       # TP = RR_TARGET x SL distance (grid axis 2)
    TP_CAP_PCT: float = 0.020    # TP hard ceiling as fraction of entry ("toooo wideeee" at 4-5%)
    RR_FLOOR: float = 1.7        # reject if the TP cap forces rr below this
    MAX_HOLD: int = 72           # bars (12h) — timeout; consumed by ztt_sim(max_hold=...)
    SWING_WIN: int = 5           # frozen; reserved for the pyramid-overlay A/B trailing stop
                                 # (per-unit stop trails the add bar's swing, KB-93) — NOT
                                 # used by the base SL, which anchors to bars t and t+1.


@dataclass
class MPBSetup:
    """Field set mirrors ZTTSetup — the `ztt_sim.simulate` consumption contract.

    level_price = SMMA(5) value at the touch bar (the dynamic 'level' bounced off);
    level_touches = 0 (no horizontal-level touch count exists for a dynamic MA);
    break_index = touch bar index t; mode = 'continuation' (MPB is trend-only).
    """
    entry_index: int                # iloc of the entry (rejection) bar = t + 1
    entry_time: pd.Timestamp
    direction: str                  # 'long' | 'short'
    mode: str                       # always 'continuation'
    entry_price: float              # Close[t+1] — reference only; sim fills at Open[t+2]
    stop_loss: float
    take_profit: float
    level_price: float              # SMMA(5) at the touch bar t
    level_touches: int              # always 0
    rr: float                       # recomputed AFTER the TP cap
    break_index: int                # touch bar index t

    @property
    def sl_distance(self) -> float:
        return abs(self.entry_price - self.stop_loss)


# ════════════════════════════════════════════════════════════════════════
# Indicators
# ════════════════════════════════════════════════════════════════════════
def compute_indicators(df: pd.DataFrame, p: MPBParams = MPBParams()) -> pd.DataFrame:
    """Attach WMA144, SMMA5, ATR14 (same implementations ztt.py uses). Returns a copy.

    All three are causal: wma/smma/atr in src.indicators.technical use only bars <= i.
    """
    out = df.copy()
    out['WMA'] = wma(out['Close'], p.WMA_PERIOD)
    out['SMMA'] = smma(out['Close'], p.SMMA_PERIOD)
    out['ATR'] = atr(out, p.ATR_PERIOD)
    return out


# ════════════════════════════════════════════════════════════════════════
# Setup generation (causal, bar-by-bar)
# ════════════════════════════════════════════════════════════════════════
def generate_setups(df: pd.DataFrame, p: MPBParams = MPBParams()) -> List[MPBSetup]:
    """Generate MPB setups over `df` (raw 10m OHLC; indicators computed here).

    Long (short = exact mirror), touch bar t / entry bar t+1:
      1. Trend:     Close[t] > WMA[t]  AND  WMA[t] > WMA[t - SLOPE_WIN]
      2. ER gate:   ER(ER_WIN) at t > ER_MIN
      3. Touch:     Low[t] <= SMMA[t]
      4. Rejection: Close[t+1] > SMMA[t+1]  AND  Close[t+1] > Open[t+1]
      5. entry_index = t+1, entry_price = Close[t+1]
      6. SL = min(Low[t], Low[t+1]) - SL_BUFFER_ATR x ATR[t+1];
         reject if SL distance / entry outside [SL_MIN_PCT, SL_MAX_PCT]
      7. TP = entry + RR_TARGET x SL_dist, capped at TP_CAP_PCT of entry;
         rr recomputed after the cap; reject if rr < RR_FLOOR
      8. Dedupe: after emitting a setup, the next touch bar must satisfy
         t >= previous entry_index + 2 (adjacent-touch suppression only —
         true position exclusivity is ztt_sim's one_position job).
    """
    d = compute_indicators(df, p)
    n = len(d)
    open_ = d['Open'].values.astype(float)
    high = d['High'].values.astype(float)
    low = d['Low'].values.astype(float)
    close = d['Close'].values.astype(float)
    wma_v = d['WMA'].values
    smma_v = d['SMMA'].values
    atr_v = d['ATR'].values
    idx = d.index

    setups: List[MPBSetup] = []
    last_entry = None                     # entry_index of the last emitted setup

    for t in range(p.SLOPE_WIN, n - 1):
        # ── dedupe adjacent touches ──
        if last_entry is not None and t < last_entry + 2:
            continue
        # ── warmup guards (all values causal at t / t+1) ──
        w_t, w_prev = wma_v[t], wma_v[t - p.SLOPE_WIN]
        s_t, s_e = smma_v[t], smma_v[t + 1]
        a_e = atr_v[t + 1]
        if (np.isnan(w_t) or np.isnan(w_prev) or np.isnan(s_t) or np.isnan(s_e)
                or np.isnan(a_e) or a_e <= 0):
            continue

        # ── 1+3. trend side + touch (mutually exclusive by the WMA side test) ──
        if close[t] > w_t and w_t > w_prev and low[t] <= s_t:
            direction = 'long'
        elif close[t] < w_t and w_t < w_prev and high[t] >= s_t:
            direction = 'short'
        else:
            continue

        # ── 2. efficiency gate at the touch bar ──
        er = _efficiency_ratio(close, t, p.ER_WIN)
        if np.isnan(er) or er <= p.ER_MIN:
            continue

        # ── 4. next-candle close-rejection (bar t+1 = entry bar) ──
        if direction == 'long':
            if not (close[t + 1] > s_e and close[t + 1] > open_[t + 1]):
                continue
        else:
            if not (close[t + 1] < s_e and close[t + 1] < open_[t + 1]):
                continue

        # ── 5-6. entry reference + structural stop with %-of-entry band ──
        entry = close[t + 1]
        if direction == 'long':
            sl = min(low[t], low[t + 1]) - p.SL_BUFFER_ATR * a_e
        else:
            sl = max(high[t], high[t + 1]) + p.SL_BUFFER_ATR * a_e
        sl_dist = abs(entry - sl)
        if sl_dist <= 0 or entry <= 0:
            continue
        if (direction == 'long' and sl >= entry) or (direction == 'short' and sl <= entry):
            continue                       # degenerate stop
        sl_pct = sl_dist / entry
        if sl_pct < p.SL_MIN_PCT or sl_pct > p.SL_MAX_PCT:
            continue

        # ── 7. %-capped TP, rr recomputed after the cap ──
        cap_dist = p.TP_CAP_PCT * entry
        tp_dist = min(p.RR_TARGET * sl_dist, cap_dist)
        rr = tp_dist / sl_dist
        if rr < p.RR_FLOOR:
            continue
        tp = entry + tp_dist if direction == 'long' else entry - tp_dist

        setups.append(MPBSetup(
            entry_index=t + 1, entry_time=idx[t + 1], direction=direction,
            mode='continuation',
            entry_price=round(entry, 3), stop_loss=round(sl, 3),
            take_profit=round(tp, 3),
            level_price=round(float(s_t), 3), level_touches=0,
            rr=round(rr, 3), break_index=t,
        ))
        last_entry = t + 1

    return setups
