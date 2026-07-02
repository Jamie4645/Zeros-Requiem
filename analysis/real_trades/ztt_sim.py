"""ZTT v3 — the ONE honest fill/exit engine (plan V7 "one-codebase" principle).

Every backtest, auto-label study, permutation null, and robustness sweep imports
`simulate` from HERE, so the phantom-fill discipline lives in exactly one place:

  * ENTRY  : next bar's OPEN (never the signal candle's close).
  * EXITS   : gap-aware — if a bar gaps THROUGH a level, fill at its open (the level
              was never traded that bar). SL checked before TP (conservative tie).
  * F7 ASSERT: every fill price must lie in its bar's [low, high] or the run HALTS.
  * OUTLIER/"UNABLE": a fill bar whose range >= OUTLIER_ATR*ATR (news spike) is an
              UNABLE (skipped + counted), not a phantom fill.
  * COST    : realistic session-gated spread+slip (ztt_costs), applied adverse.

`one_position=True`  -> portfolio backtest (no overlapping trades).
`one_position=False` -> label EVERY setup independently (auto-label / outcome study).
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
import pandas as pd

from src.regimes.ztt import ZTTParams, compute_indicators
from src.regimes.ztt_costs import DEFAULT_COST as COST

START_EQ = 10000.0
MAX_HOLD = 144          # ~1 trading day cap on a 10m trade
OUTLIER_ATR = 3.5       # fill-bar range >= this * ATR => "unable" (news spike)
TARGET_RR = ZTTParams().MIN_RR   # 3.0 — TP exactly at 3R is a clean target; tighter = a cap


def atr_array(df: pd.DataFrame, p: ZTTParams) -> np.ndarray:
    return compute_indicators(df, p)['ATR'].values


def simulate(setups, df: pd.DataFrame, atr_v: np.ndarray,
             regime_df: Optional[pd.DataFrame] = None, risk: float = 0.01,
             start_eq: float = START_EQ, max_hold: int = MAX_HOLD,
             outlier_atr: float = OUTLIER_ATR, block_rollover: bool = False,
             one_position: bool = True, target_rr: float = TARGET_RR):
    """Return (trades, unables). Each trade dict carries pnl, r, exit_reason
    ('sl'|'tp'|'cap'|'timeout'), entry/exit time+index, mfe_r, regime, direction.

    When one_position=True the trade R uses a compounding equity (portfolio sense);
    when False every setup is filled on the same fixed `start_eq` (independent labels)
    so R-multiples are comparable and unaffected by ordering.
    """
    OPEN = df['Open'].values if 'Open' in df else df['Close'].values
    HIGH, LOW, CLOSE = df['High'].values, df['Low'].values, df['Close'].values
    IDX = df.index
    HOURS = df.index.hour.values
    n = len(df)

    def _assert_fill(price, j):
        if not (LOW[j] - 1e-6 <= price <= HIGH[j] + 1e-6):
            raise AssertionError(
                f"PHANTOM FILL at bar {j} ({IDX[j]}): {price} outside [{LOW[j]}, {HIGH[j]}]")

    setups = sorted(setups, key=lambda s: s.entry_index)
    eq = start_eq
    next_free = -1
    unables = 0
    trades: List[dict] = []
    for s in setups:
        ei = s.entry_index
        fi = ei + 1
        if fi >= n:
            continue
        if one_position and ei <= next_free:
            continue
        if block_rollover and COST.entry_blocked(int(HOURS[ei])):
            continue
        a_fill = atr_v[fi]
        if a_fill and a_fill > 0 and (HIGH[fi] - LOW[fi]) >= outlier_atr * a_fill:
            unables += 1
            continue
        owc = COST.fill_cost_one_way(int(HOURS[fi]))
        raw_entry = OPEN[fi]
        _assert_fill(raw_entry, fi)
        entry = raw_entry + owc if s.direction == 'long' else raw_entry - owc
        risk_dist = abs(entry - s.stop_loss)
        if risk_dist <= 0:
            continue
        if (s.direction == 'long' and s.stop_loss >= entry) or \
           (s.direction == 'short' and s.stop_loss <= entry):
            continue
        size = ((eq if one_position else start_eq) * risk) / risk_dist

        sl, tp = s.stop_loss, s.take_profit
        exit_price = reason = None
        end = min(n, fi + max_hold)
        mfe = 0.0
        for j in range(fi, end):
            if s.direction == 'long':
                mfe = max(mfe, HIGH[j] - entry)
                if LOW[j] <= sl:
                    exit_price, xj, reason = (sl if OPEN[j] >= sl else OPEN[j]), j, 'sl'; break
                if HIGH[j] >= tp:
                    exit_price, xj, reason = (tp if OPEN[j] <= tp else OPEN[j]), j, 'tp'; break
            else:
                mfe = max(mfe, entry - LOW[j])
                if HIGH[j] >= sl:
                    exit_price, xj, reason = (sl if OPEN[j] <= sl else OPEN[j]), j, 'sl'; break
                if LOW[j] <= tp:
                    exit_price, xj, reason = (tp if OPEN[j] >= tp else OPEN[j]), j, 'tp'; break
        if exit_price is None:
            xj = end - 1
            exit_price = CLOSE[xj]
            reason = 'timeout'
        _assert_fill(exit_price, xj)
        oxc = COST.fill_cost_one_way(int(HOURS[xj]))
        if s.direction == 'long':
            pnl = size * ((exit_price - oxc) - entry)
        else:
            pnl = size * (entry - (exit_price + oxc))
        if one_position:
            eq += pnl
        if reason == 'tp' and abs(s.rr - target_rr) > 0.05:
            reason = 'cap'
        reg = None
        if regime_df is not None:
            reg = regime_df.iloc[ei]['trend_dir']
        trades.append(dict(
            pnl=pnl, r=pnl / (size * risk_dist) if size * risk_dist else 0.0,
            exit_reason=reason, entry_time=IDX[ei], exit_time=IDX[xj],
            entry_index=ei, exit_index=xj,
            mfe_r=mfe / risk_dist if risk_dist else 0.0,
            regime=reg, direction=s.direction,
        ))
        if one_position:
            next_free = xj
    return trades, unables
