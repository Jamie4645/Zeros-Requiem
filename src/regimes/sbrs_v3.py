"""
SBRS 3.0 — Clean-slate breakout-retest with STRUCTURAL exits.

See docs/sbrs_3.0_spec.md. Design (resolved with user 2026-06-02):
  - Entry: bare with-trend breakout-retest (the only realistic-fill-positive core).
           Reuses v2's validated entry detection with all net-negative 2.0 features
           OFF (confluence scoring, counter-trend, false-BO levels) and the user's
           doc MA convention (SMMA>WMA = bullish).
  - Exit:  STRUCTURAL, with room (the 3.0 edge thesis) — replaces fixed/adaptive 3R.
             * TP = a significant prior reversal/consolidation level in the trade
               direction (tp_mode 'near' = nearest overhead/underfoot level — the
               user's preferred "consolidation low"; 'far' = the major level).
             * SL = beyond the most recent structural swing, plus an ATR buffer
               for room. Never tight.
           MIN_RR is a FLOOR filter only (skip setups whose structural target is
           sub-floor), never the target.
  - No confluence, no counter-trend, no false-BO, no reversal in the baseline.
    Those are added back only via earn-your-place ablation (see tests/_audit_sbrs_v3.py).

Contract: run analyze_sbrs_v3 AND its backtest inside a
USE_OLD_MA_CONVENTION=True + engine.REVERSAL_ENTRY_ENABLED=False context (the
harness sets these so the doc trend convention and the engine MA-exit stay
consistent and no reversal injection fires). analyze_sbrs_v3 manages the
confluence constants itself.
"""

from typing import List
import numpy as np
import pandas as pd

from ..indicators.technical import (
    atr, detect_swing_high, detect_swing_low,
)
from ..indicators.smart_money import count_level_touches
from ..execution.entries import TradeSetup, TradeDirection
from . import sbrs_v2 as v2
from .sbrs_v2 import analyze_sbrs_v2, ATR_PERIOD, SWING_WINDOW, MIN_RR


# Defaults for the structural exit overlay (tunable in ablation, not SACRED).
# User-pinned (2026-06-02):
#   SL  = just beyond the BROKEN/flip level itself (+ ATR buffer for room).
#   TP  = nearest SIGNIFICANT level in trade direction = a MULTI-TOUCH /
#         consolidation level (== origin of the prior big move, per user).
TP_LOOKBACK = 200          # bars to scan for a prior multi-touch level
TP_MIN_TOUCHES = 2         # a target level must have been respected >= this many times
SL_BUFFER_ATR = 0.5        # room beyond the broken level (user: "needs space")


def _dir_str(setup: TradeSetup) -> str:
    d = setup.direction
    return d.value if hasattr(d, 'value') else str(d)


def _structural_tp(df, direction, entry_price, idx, atr_val, highs, lows,
                   sh_mask, sl_mask, tp_lookback, tp_mode, min_touches):
    """Nearest ('near') or major ('far') SIGNIFICANT level in trade direction.

    A level is significant only if it is MULTI-TOUCH (respected >= min_touches
    times within tolerance) — a consolidation / S-R zone, which the user equates
    with the origin of the prior big move. Minor 3-bar wiggles are ignored.

    Long  -> a multi-touch swing HIGH above entry (overhead supply). 'near' = lowest
             qualifying level (first real resistance), 'far' = highest.
    Short -> a multi-touch swing LOW below entry. 'near' = highest, 'far' = lowest.
    Returns the target price, or None if no significant level exists.
    """
    start = max(0, idx - tp_lookback)
    end = max(0, idx - 2)  # swing confirmation lag; don't peek at the current bar
    cand = []
    if direction == 'long':
        for k in range(start, end):
            if sh_mask[k] and highs[k] > entry_price:
                if count_level_touches(df, highs[k], idx, atr_val) >= min_touches:
                    cand.append(highs[k])
        if not cand:
            return None
        return min(cand) if tp_mode == 'near' else max(cand)
    else:
        for k in range(start, end):
            if sl_mask[k] and lows[k] < entry_price:
                if count_level_touches(df, lows[k], idx, atr_val) >= min_touches:
                    cand.append(lows[k])
        if not cand:
            return None
        return max(cand) if tp_mode == 'near' else min(cand)


def apply_structural_exits(
    df: pd.DataFrame,
    setups: List[TradeSetup],
    equity: float,
    risk_pct: float,
    tp_mode: str = 'near',
    min_rr_floor: float = MIN_RR,
    sl_buffer_atr: float = SL_BUFFER_ATR,
    tp_lookback: int = TP_LOOKBACK,
    tp_min_touches: int = TP_MIN_TOUCHES,
) -> List[TradeSetup]:
    """Overlay structural SL/TP on bare-core entry setups. Returns kept setups."""
    if not setups:
        return setups
    atr_vals = atr(df, ATR_PERIOD)
    sh_mask = detect_swing_high(df['High'], left=SWING_WINDOW, right=SWING_WINDOW)
    sl_mask = detect_swing_low(df['Low'], left=SWING_WINDOW, right=SWING_WINDOW)
    highs, lows = df['High'].values, df['Low'].values
    sh_vals, sl_vals = sh_mask.values, sl_mask.values

    out: List[TradeSetup] = []
    for s in setups:
        i = s.index
        if i <= 5 or i >= len(df):
            continue
        a = atr_vals.iloc[i]
        if np.isnan(a) or a <= 0:
            continue
        direction = _dir_str(s)
        entry = s.entry_price
        level = s.broken_level  # the broken/retested flip level
        if level <= 0:
            continue

        # ── Structural SL: just beyond the broken/flip level, with room ──
        if direction == 'long':
            sl = level - sl_buffer_atr * a
            if sl >= entry:
                continue
        else:
            sl = level + sl_buffer_atr * a
            if sl <= entry:
                continue

        # ── Structural TP: nearest significant multi-touch level ──
        tp = _structural_tp(df, direction, entry, i, a, highs, lows,
                            sh_vals, sl_vals, tp_lookback, tp_mode, tp_min_touches)
        if tp is None:
            continue

        sl_dist = abs(entry - sl)
        if sl_dist <= 0:
            continue
        rr = abs(tp - entry) / sl_dist
        if min_rr_floor and rr < min_rr_floor:
            continue  # structural target too close — skip (floor filter)

        s.stop_loss = sl
        s.take_profit = tp
        s.position_size = (equity * risk_pct) / sl_dist
        s.risk_reward = round(rr, 2)
        out.append(s)
    return out


# Bare-core v2 constants (the only realistic-fill-positive config) + doc convention.
_BARE_CORE = {
    'CONFLUENCE_MIN_WITH_TREND': 0.0,
    'CONFLUENCE_MIN_WITH_TREND_FOREX': 0.0,
    'CONFLUENCE_MIN_COUNTER_TREND': 99.0,   # no counter-trend
    'CONFLUENCE_MIN_AFTER_FALSE_BO': 99.0,  # no false-breakout-level trades
}


def analyze_sbrs_v3(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01,
    asset_class: str = 'gold',
    symbol: str = '',
    tp_mode: str = 'near',
    min_rr_floor: float = MIN_RR,
    sl_buffer_atr: float = SL_BUFFER_ATR,
    tp_lookback: int = TP_LOOKBACK,
) -> List[TradeSetup]:
    """SBRS 3.0 setups: bare-core entries + structural exits.

    NOTE: caller must set v2.USE_OLD_MA_CONVENTION=True and
    engine.REVERSAL_ENTRY_ENABLED=False around analyze + backtest (see harness).
    """
    saved = {k: getattr(v2, k) for k in _BARE_CORE if hasattr(v2, k)}
    for k, val in _BARE_CORE.items():
        if hasattr(v2, k):
            setattr(v2, k, val)
    try:
        base = analyze_sbrs_v2(df, equity, risk_pct, asset_class=asset_class,
                               symbol=symbol, entry_mode='close')
    finally:
        for k, val in saved.items():
            setattr(v2, k, val)

    return apply_structural_exits(
        df, base, equity, risk_pct, tp_mode=tp_mode,
        min_rr_floor=min_rr_floor, sl_buffer_atr=sl_buffer_atr,
        tp_lookback=tp_lookback,
    )
