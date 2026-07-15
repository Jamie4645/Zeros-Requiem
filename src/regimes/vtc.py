"""
VTC — Volatility-Thrust Continuation (intraday Gold, 10m).

Pre-registered candidate 2 of knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md
(FROZEN 2026-07-04, committed BEFORE any backtest ran). NO horizontal level, NO
break, NO retest — the ZTT-falsified geometry stays dead.

One line: a single decisive range-expansion bar closing in its outer 20%, aligned
with the 1H trend, continues; enter next bar; structural stop; %-capped TP.

Mechanism (10m XAUUSD entries, 1H trend filter — all values frozen in VTCParams):
  * Trend context (1H, resampled from the 10m frame INSIDE compute_indicators,
    closed='right'/label='right'): last completed 1H close > SMA(20) AND SMA(20)
    now > SMA(20) five completed 1H bars ago -> long-bias only (mirror for short).
    The 1H columns are forward-filled onto the 10m index so a 10m bar stamped
    10:30 sees the 1H state as of the 10:00 close — NEVER the in-progress
    10-11h bar (right-labeled bins are only assigned to 10m stamps >= the label,
    so every 1H value at 10m bar t is built exclusively from 10m bars <= t).
  * Thrust trigger at bar t: (High-Low) >= THRUST_ATR x ATR(14) AND
    CLV = (Close-Low)/(High-Low) >= CLV_BAND for longs (<= 1-CLV_BAND shorts)
    AND 1H bias agrees. Kaufman ch. 14 event-shock + CLV continuation.
  * Entry: setup at the thrust bar (entry_price = its close for reference);
    `ztt_sim.simulate` fills honestly at the NEXT bar's open (phantom-fill assert).
  * Stop: most recent SL_SWING_WIN-bar swing extreme against the position (the
    raw swing itself, no buffer). Eligibility bound, not a tightener: REJECT the
    setup if SL distance > SL_MAX_PCT of entry (hard cap 0.45%) or < SL_MIN_PCT
    (cost-realism floor 0.15%).
  * TP: RR_TARGET x SL distance, capped at TP_CAP_PCT of entry (user's hard
    ceiling). Recompute R:R after the cap; skip if < RR_FLOOR.
  * Cooldown: after EMITTING a setup, suppress new setups for COOLDOWN_BARS bars
    (prevents thrust-cluster stacking in the base variant). Max hold 72 bars
    (enforced by the simulator via VTCParams.MAX_HOLD).

CRITICAL: fully causal — every value at bar t derives from bars <= t only, and
1H context only from COMPLETED 1H bars. Grid overrides (THRUST_ATR, CLV_BAND —
the ONLY pre-registered grid axes) go through the VTCParams object only.

Contract: VTCSetup is consumable by analysis/real_trades/ztt_sim.py::simulate.
Per instruction, level-geometry fields are filled as: level_price = thrust bar
close, level_touches = 0, break_index = thrust bar index, mode = 'continuation'.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from src.indicators.technical import atr


# ════════════════════════════════════════════════════════════════════════
# Parameters — SACRED + FROZEN (pre-registered KB-93, 2026-07-04).
# Any change requires a documented amendment BEFORE the corresponding phase
# runs, per arbiter-falsifier protocol. NO other configs may be run.
# ════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class VTCParams:
    # ── SACRED — never optimized ──
    ATR_PERIOD: int = 14           # same ATR(14) convention as ztt.py / ztt_sim.py

    # ── FROZEN mechanization (KB-93; grid axes marked) ──
    THRUST_ATR: float = 1.5        # GRID {1.25, 1.5, 2.0} — range >= this x ATR14
    CLV_BAND: float = 0.80         # GRID {0.75, 0.80, 0.85} — CLV >= band (long) / <= 1-band (short)
    HTF_SMA: int = 20              # 1H SMA period for trend context
    HTF_SLOPE_WIN: int = 5         # 1H SMA slope lookback (completed 1H bars)
    SL_SWING_WIN: int = 3          # bars (t-2..t) for the structural swing stop
    SL_MAX_PCT: float = 0.0045     # REJECT if SL distance > 0.45% of entry (hard cap = eligibility)
    SL_MIN_PCT: float = 0.0015     # REJECT if SL distance < 0.15% of entry (cost realism)
    RR_TARGET: float = 1.8         # TP = 1.8 x SL distance (midpoint of user's 1.7-2.0)
    TP_CAP_PCT: float = 0.020      # TP capped at 2.0% of entry (user's hard ceiling)
    RR_FLOOR: float = 1.7          # skip if cap forces R:R below this
    COOLDOWN_BARS: int = 6         # suppress new setups this many bars after an emit
    MAX_HOLD: int = 72             # bars (12h) — timeout exit, consumed by the simulator


@dataclass
class VTCSetup:
    """ztt_sim-compatible setup. entry_index = thrust bar; sim fills at Open[t+1]."""
    entry_index: int                # iloc of the thrust bar
    entry_time: pd.Timestamp
    direction: str                  # 'long' | 'short'
    mode: str                       # always 'continuation' for VTC
    entry_price: float              # thrust bar close (reference; sim uses next open)
    stop_loss: float
    take_profit: float
    level_price: float              # = thrust bar close (contract filler; VTC has no level)
    level_touches: int              # = 0 (contract filler)
    rr: float
    break_index: int                # = thrust bar index (contract filler)

    @property
    def sl_distance(self) -> float:
        return abs(self.entry_price - self.stop_loss)


# ════════════════════════════════════════════════════════════════════════
# Indicators — ATR(14) on 10m + causal 1H trend context
# ════════════════════════════════════════════════════════════════════════
def compute_indicators(df: pd.DataFrame, p: VTCParams = VTCParams()) -> pd.DataFrame:
    """Attach ATR(14) and the causal 1H trend-bias columns. Returns a copy.

    1H resample uses closed='right'/label='right' so the bin labeled T contains
    only 10m bars stamped in (T-1h, T]. Forward-filling the right-labeled series
    onto the 10m index assigns bin T only to 10m stamps >= T, therefore every 1H
    value seen at 10m bar t is built exclusively from 10m bars with index <= t
    — a 10m bar at 10:30 sees the 1H state as of the 10:00 close, never the
    in-progress 10-11h bar. Partial trailing bins are labeled at the NEXT hour
    boundary, so they are never forward-filled onto any existing 10m bar
    (prefix-stability: generate_setups(df[:k]) matches the full run).
    """
    out = df.copy()
    out['ATR'] = atr(out, p.ATR_PERIOD)

    h_close = out['Close'].resample('1h', closed='right', label='right').last().dropna()
    h_sma = h_close.rolling(window=p.HTF_SMA).mean()
    h_sma_prev = h_sma.shift(p.HTF_SLOPE_WIN)
    long_b = (h_close > h_sma) & (h_sma > h_sma_prev)
    short_b = (h_close < h_sma) & (h_sma < h_sma_prev)

    out['HTF_CLOSE'] = h_close.reindex(out.index, method='ffill')
    out['HTF_SMA'] = h_sma.reindex(out.index, method='ffill')
    # float round-trip: bool reindex would upcast to object where leading NaN appear
    out['HTF_LONG'] = (long_b.astype('float64').reindex(out.index, method='ffill')
                       .fillna(0.0).astype(bool))
    out['HTF_SHORT'] = (short_b.astype('float64').reindex(out.index, method='ffill')
                        .fillna(0.0).astype(bool))
    return out


# ════════════════════════════════════════════════════════════════════════
# Setup generation (causal, bar-by-bar)
# ════════════════════════════════════════════════════════════════════════
def generate_setups(df: pd.DataFrame, p: VTCParams = VTCParams()) -> List[VTCSetup]:
    """Generate VTC setups over `df` (raw 10m OHLC; indicators computed here)."""
    d = compute_indicators(df, p)
    n = len(d)
    high = d['High'].values
    low = d['Low'].values
    close = d['Close'].values
    atr_v = d['ATR'].values
    long_bias = d['HTF_LONG'].values
    short_bias = d['HTF_SHORT'].values

    setups: List[VTCSetup] = []
    last_emit = -10 ** 9   # iloc of the last EMITTED setup (cooldown anchor)
    w = p.SL_SWING_WIN

    for t in range(n):
        a = atr_v[t]
        if np.isnan(a) or a <= 0 or t < w - 1:
            continue                                    # warmup / not enough swing bars
        if t - last_emit <= p.COOLDOWN_BARS:
            continue                                    # cooldown after an emitted setup

        rng = high[t] - low[t]
        if rng <= 0 or rng < p.THRUST_ATR * a:
            continue                                    # no range expansion
        clv = (close[t] - low[t]) / rng

        if clv >= p.CLV_BAND and long_bias[t]:
            direction = 'long'
        elif clv <= (1.0 - p.CLV_BAND) and short_bias[t]:
            direction = 'short'
        else:
            continue                                    # close-location or bias fails

        entry = close[t]
        # ── structural SL: SL_SWING_WIN-bar swing extreme against the position ──
        if direction == 'long':
            sl = float(np.min(low[t - w + 1:t + 1]))
        else:
            sl = float(np.max(high[t - w + 1:t + 1]))
        sl_dist = abs(entry - sl)
        if (direction == 'long' and sl >= entry) or (direction == 'short' and sl <= entry):
            continue                                    # degenerate stop
        # eligibility bounds — hard cap means REJECT, never tighten artificially
        if sl_dist > p.SL_MAX_PCT * entry:
            continue                                    # swing stop wider than 0.45%
        if sl_dist < p.SL_MIN_PCT * entry:
            continue                                    # tighter than the cost-realism floor

        # ── TP: RR_TARGET x SL distance, %-capped; recompute R:R; floor check ──
        cap = p.TP_CAP_PCT * entry
        tp_dist = min(p.RR_TARGET * sl_dist, cap)
        rr = tp_dist / sl_dist
        if rr < p.RR_FLOOR - 1e-9:
            continue                                    # cap forced R:R below the floor
        tp = entry + tp_dist if direction == 'long' else entry - tp_dist

        setups.append(VTCSetup(
            entry_index=t, entry_time=d.index[t], direction=direction,
            mode='continuation',
            entry_price=round(entry, 3), stop_loss=round(sl, 3),
            take_profit=round(tp, 3),
            level_price=round(entry, 3),                # contract filler: thrust bar close
            level_touches=0,                            # contract filler: no level in VTC
            rr=round(rr, 2),
            break_index=t,                              # contract filler: thrust bar index
        ))
        last_emit = t

    return setups
