"""ZTT v2 — discretion-encoded intraday Gold (10m).

Built 2026-06-13 from the user's 60-setup take/skip review (analysis/real_trades/
tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv) — the FIRST dataset with
negatives. Decode/spec: analysis/real_trades/ZTT_V2_SPEC.md. Reuses the frozen
Phase-2 primitives in ztt.py (compute_indicators, level machinery, structural SL,
trend state) — NO change to that module, its 199 tests stay green.

Two layers the review demanded (verified: take-subset +10.29R vs skip-subset −24.75R):

  LAYER 1 — SELECTION (which setups are valid)
    S1  Significant-level gate: the broken level must coincide with a prior-day /
        prior-week extreme, a $50 round number, OR a dominant N-bar swing extreme —
        not merely a 2-touch swing. (level_touches did NOT separate the user's takes
        from skips; his "significant" is structural, per arbiter-gold.)
    S3  False-breakout filter: reject a break candle with a long rejection wick.
    S4  Session gate: skip rollover (21-23 UTC) and ny_close (20-21 UTC).
    S5  Stricter reversal: REVERSAL_LOOKBACK lifted 30 → 240 bars (~prior day).
    (S2 momentum/anti-chop reuses ztt._passes_gates; S6 no-stacking is enforced at
     the backtest layer — one position at a time.)

  LAYER 2 — EXIT (how to size TP/SL) — F3-validated (re-exit transfer PASS)
    E1  Structural + %-capped TP: closest-to-entry of {3R, nearest opposing
        significant level − buffer, entry·(1 ± MAX_MOVE_PCT)}. R:R is an OUTPUT.
    E2  R:R floor: reject if the capped R:R < RR_FLOOR (this is what culls the
        "predicting a break of a close strong level" setups the user skipped).
    E3  Structural SL: unchanged from ztt.py (the user accepted it).

Council verdict 2026-06-13: PROCEED-WITH-CHANGES. F3 passed (edge transfers to the
1.5% cap, WR 17%→40%, de-concentrates). Open deployment gates (NOT build gates):
direction/regime out-of-sample (F5), cost PF on 10y (F6). MAX_MOVE_PCT and RR_FLOOR
are GRID-reported, never hand-picked (arbiter-gold + red-team mandate).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from src.regimes.ztt import (
    ZTTParams, ZTTSetup, _Level,
    compute_indicators, _absorb_touch, _significant, _swing_before_break,
    _trend_state, _passes_gates,
)
from src.regimes.ztt_costs import DEFAULT_COST as COST


@dataclass(frozen=True)
class ZTTV2Params(ZTTParams):
    # ══ LAYER 2 (exits) — REBUILT 2026-06-14b from the user's clarified rules ══
    # User: SL "just below the support, not on it" (~0.4-0.46%); TP "1% to 2% price growth
    # while maintaining 2.5R-3R". KEY: 3R was never wrong — the WIDE swing-SL was. On a tight
    # level-anchored SL (~0.4%), 3R = ~1.2% move = exactly his 1-2% / 2.5-3R ask.
    sl_anchor: str = 'level'           # 'level' = retested level ± buffer (USER RULE) | 'swing' = old v1
    SL_BUFFER_PCT: float = 0.0045      # SL placed this far BEYOND the retested level (~0.45%; user gave -0.46%)
    MAX_MOVE_PCT: float = 0.015        # TP hard ceiling — F3-VALIDATED frozen value (2026-06-13:
                                       #   "best cap (1.5%) nets +8.72R"; council: "only the 1.5% cap
                                       #   is robust"). Satisfies user's "keep it below 2%". A 2.0%
                                       #   default crept in 2026-06-14b WITHOUT re-running F3 — reverted
                                       #   2026-07-02 (audit). Raising it requires an F3 re-run + doc.
    RR_FLOOR: float = 0.0              # high-recall: don't reject on R:R; surface + let user judge
    # ── opposing-level TP cap (don't target PAST a strong level) ──
    ROUND_STEP: float = 50.0           # $50 round-number magnetism (arbiter-gold)
    OPP_TOL_ATR: float = 0.50
    OPP_MIN_TOUCHES: int = 3           # cap TP only at STRONG opposing levels (3+ clean touches)
    enforce_opposing: bool = False     # OFF — pivots/rounds are too dense and crush TP to ~0.1%.
                                       #   "don't target past a strong level" is the USER's judgment call
                                       #   (high recall = he decides). TP = min(3R, 2%) on the tight SL.
    SIG_TOL_ATR: float = 0.50
    FALSE_BO_WICK_ATR: float = 0.75    # S3 rejection-wick on the break candle = fakeout
    # ── LAYER 1 selection — HIGH RECALL (user: surface ~60+/mo, I filter by eye) ──
    enforce_significance: bool = False # off — non-discriminating
    req_momentum: bool = False         # off — high recall
    enforce_false_bo: bool = True      # KEEP — user's explicit rule ("WE DO NOT TRADE FALSE BREAKOUTS")
    enforce_session: bool = False      # OFF — user's takes span all sessions; not in his words
    SESSION_BLOCK: Tuple[str, ...] = ('rollover',)  # only the cost-model rollover hard-gate still applies
    # ── momentum-continuation (#52-55 "riding the wave") — A/B test mode ──
    momentum_mode: str = 'off'         # 'off' | 'on' | 'on_tight' (smaller TP on post-initial entries)
    MOM_TP_PCT: float = 0.010          # tighter TP for momentum-continuation entries (reversal risk)
    # S5: lift the reversal lookback so "significant extreme" spans ~a prior day, not 5h.
    REVERSAL_LOOKBACK: int = 240
    # Shift signals OFF (matches the review's base config; momentum was non-discriminating).
    req_fvg: bool = False
    req_sweep: bool = False
    # ── PRUNED 2026-06-14 (ablation `phase4/ablate_ztt.py` + 10Y re-verify): base gates
    #    that were ON (inherited from ZTTParams) but TRULY INERT — exactly ΔnetR=0 on the
    #    1Y ablation AND reproduce the original 10Y baseline when removed — turned OFF in
    #    the shipped screener to simplify the surface. KEPT: G4 (enable_structure) pulls
    #    weight (removing it raises maxDD 32%→46%); G6 (enable_volume) looked inert on 1Y
    #    but the 10Y re-run showed it filters ~200 net-negative trades (IR −0.31→−0.43,
    #    maxDD 59%→66% if removed) — so it STAYS ON. enforce_session/momentum_mode/req_sweep/
    #    req_fvg were already off above. Reversible if a regime-balanced corpus says otherwise.
    enable_respect: bool = False    # G3 level-respect veto — Δ0 on 1Y AND 10Y (never bound)
    enable_htf: bool = False        # G5 1h/3h-EMA alignment — Δ0 on 1Y AND 10Y (never bound)
    # enable_volume KEPT (inherited True) — NOT inert on 10Y; see note above.


# ════════════════════════════════════════════════════════════════════════
# Significant-level register (arbiter-gold: prior-day/week pivots + round numbers)
# ════════════════════════════════════════════════════════════════════════
def session_levels(df: pd.DataFrame) -> dict:
    """Causal prior-day & prior-week high/low, aligned per-bar (no lookahead).

    A bar on calendar day D uses day D-1's completed extremes; week W uses W-1's.
    Returns arrays indexed like df.
    """
    idx = df.index
    day = idx.normalize()
    daily = df.groupby(day).agg(dh=('High', 'max'), dl=('Low', 'min'))
    daily_prev = daily.shift(1)
    pdh = pd.Series(day, index=idx).map(daily_prev['dh']).values
    pdl = pd.Series(day, index=idx).map(daily_prev['dl']).values

    wk = idx.tz_localize(None).to_period('W')   # tz dropped intentionally (week bucketing only)
    weekly = df.groupby(wk).agg(wh=('High', 'max'), wl=('Low', 'min'))
    weekly_prev = weekly.shift(1)
    wk_s = pd.Series(wk, index=idx)
    pwh = wk_s.map(weekly_prev['wh']).values
    pwl = wk_s.map(weekly_prev['wl']).values
    return dict(pdh=pdh, pdl=pdl, pwh=pwh, pwl=pwl)


def _nearest_round(price: float, step: float) -> float:
    return round(price / step) * step


def _level_significant(price: float, i: int, a: float, lv: '_Level',
                       sig: dict, sh_recent, sl_recent, kind: str,
                       p: ZTTV2Params) -> bool:
    """S1: is the broken level a *significant* structural reference?

    Significant if within SIG_TOL_ATR·ATR of a prior-day/week extreme or a $50 round
    number, OR if it is the dominant swing extreme over REVERSAL_LOOKBACK.
    """
    tol = p.SIG_TOL_ATR * a
    refs = [sig['pdh'][i], sig['pdl'][i], sig['pwh'][i], sig['pwl'][i],
            _nearest_round(price, p.ROUND_STEP)]
    for r in refs:
        if r == r and abs(price - r) <= tol:    # r==r filters NaN
            return True
    recent = sh_recent if kind == 'resistance' else sl_recent
    return _significant(recent, i, price, kind, p)


def _opposing_levels(direction: str, entry: float, i: int, sig: dict,
                     p: ZTTV2Params, levels=None) -> List[float]:
    """E1/S1b: levels on the FAR side of the trade that can cap the TP.

    Two sources:
      * prior-day/week pivots + next $50 round number (light, always — part of E1 exit).
      * STRONG engine swing levels (clean>=OPP_MIN_TOUCHES) on the far side — the
        intraday S/R the user actually reads (S1b, gated by enforce_opposing). This is
        the dominant skip reason: "a stronger opposing level sits in the way".
    """
    step = p.ROUND_STEP
    if direction == 'long':
        cands = [sig['pdh'][i], sig['pwh'][i], (np.floor(entry / step) + 1) * step]
        out = [c for c in cands if c == c and c > entry]
    else:
        cands = [sig['pdl'][i], sig['pwl'][i], (np.ceil(entry / step) - 1) * step]
        out = [c for c in cands if c == c and c < entry]
    if p.enforce_opposing and levels is not None:
        for lv in levels:
            if lv.clean < p.OPP_MIN_TOUCHES:
                continue
            if direction == 'long' and lv.price > entry:
                out.append(lv.price)
            elif direction == 'short' and lv.price < entry:
                out.append(lv.price)
    return out


# ════════════════════════════════════════════════════════════════════════
# Setup generation (v2) — same causal loop as ztt.generate_setups, v2 entry
# ════════════════════════════════════════════════════════════════════════
def generate_setups_v2(df: pd.DataFrame, p: ZTTV2Params = ZTTV2Params(),
                       apply_gates: bool = True) -> List[ZTTSetup]:
    d = compute_indicators(df, p)
    sig = session_levels(d)
    n = len(d)
    high, low, close = d['High'].values, d['Low'].values, d['Close'].values
    open_ = d['Open'].values if 'Open' in d else close
    atr_v = d['ATR'].values
    sh_mask, sl_mask = d['swing_high'].values, d['swing_low'].values

    levels: List[_Level] = []
    sh_prices: List[float] = []
    sl_prices: List[float] = []
    sh_recent: List[tuple] = []
    sl_recent: List[tuple] = []
    setups: List[ZTTSetup] = []
    w = p.SWING_W

    for i in range(n):
        a = atr_v[i]
        if np.isnan(a) or a <= 0 or np.isnan(d['WMA'].values[i]):
            continue
        k = i - w
        if k >= 0:
            ak = atr_v[k] if not np.isnan(atr_v[k]) and atr_v[k] > 0 else a
            if sh_mask[k]:
                sh_prices.append(high[k]); sh_recent.append((k, high[k]))
                _absorb_touch(levels, high[k], 'resistance', k, close[k], ak, p)
            if sl_mask[k]:
                sl_prices.append(low[k]); sl_recent.append((k, low[k]))
                _absorb_touch(levels, low[k], 'support', k, close[k], ak, p)

        trend = _trend_state(sh_prices, sl_prices)

        for lv in levels:
            if lv.broken_at is not None or lv.consumed:
                continue
            if not lv.qualifies(p.MIN_TOUCHES):
                continue
            if lv.kind == 'resistance' and close[i] > lv.price + p.BREAK_BUFFER * a:
                lv.broken_at, lv.break_dir = i, 'up'
            elif lv.kind == 'support' and close[i] < lv.price - p.BREAK_BUFFER * a:
                lv.broken_at, lv.break_dir = i, 'down'

        for lv in levels:
            if lv.consumed or lv.broken_at is None:
                continue
            age = i - lv.broken_at
            if age < 1 or age > p.MAX_RETEST_WAIT:
                if age > p.MAX_RETEST_WAIT:
                    lv.consumed = True
                continue
            setup = _try_entry_v2(lv, i, trend, high, low, close, open_, a, p,
                                  sh_recent, sl_recent, sig, d.index[i], levels)
            if setup is not None:
                lv.consumed = True
                if (not apply_gates) or _passes_gates(d, setup, p):
                    setups.append(setup)
    return setups


def _try_entry_v2(lv: _Level, i: int, trend: str, high, low, close, open_, a: float,
                  p: ZTTV2Params, sh_recent, sl_recent, sig: dict,
                  ts, levels=None) -> Optional[ZTTSetup]:
    bi = lv.broken_at
    if lv.break_dir == 'up':
        direction = 'long'
        near = low[i] <= lv.price + p.RETEST_TOL * a
        reject = close[i] > lv.price
        kind = 'resistance'
    else:
        direction = 'short'
        near = high[i] >= lv.price - p.RETEST_TOL * a
        reject = close[i] < lv.price
        kind = 'support'
    if not (near and reject):
        return None

    # ── S4 session gate ──
    if p.enforce_session and COST.session_label(int(ts.hour)) in p.SESSION_BLOCK:
        return None
    if COST.entry_blocked(int(ts.hour)):          # rollover hard gate (cost model)
        return None

    # ── S1 significant-level gate ──
    if p.enforce_significance and not _level_significant(
            lv.price, i, a, lv, sig, sh_recent, sl_recent, kind, p):
        return None

    # ── S3 false-breakout: rejection wick on the break candle ──
    if p.enforce_false_bo:
        if direction == 'long':
            wick = high[bi] - max(open_[bi], close[bi])     # upper rejection wick
        else:
            wick = min(open_[bi], close[bi]) - low[bi]      # lower rejection wick
        if wick > p.FALSE_BO_WICK_ATR * a:
            return None

    # ── mode (continuation / confirmed-reversal / blocked) ──
    if lv.break_dir == 'up':
        if trend == 'up':
            mode = 'continuation'
        elif trend == 'range':
            mode = 'range'
        elif _significant(sh_recent, i, lv.price, 'resistance', p):
            mode = 'reversal'
        else:
            return None
    else:
        if trend == 'down':
            mode = 'continuation'
        elif trend == 'range':
            mode = 'range'
        elif _significant(sl_recent, i, lv.price, 'support', p):
            mode = 'reversal'
        else:
            return None
    if mode == 'reversal' and not p.allow_reversal:
        return None

    entry = close[i]
    # ── E3 SL: anchor at the RETESTED LEVEL ± buffer (user rule: "just below the support,
    #    not on it" ~0.45%), NOT a distant swing-before-break. This is the fix for the
    #    R:R<1 slop — with a ~0.45% stop, a 3R target = ~1.3% move = the user's 1-2% ask. ──
    if p.sl_anchor == 'level':
        buf = p.SL_BUFFER_PCT * entry
        sl = lv.price - buf if direction == 'long' else lv.price + buf
    else:  # legacy swing-before-break (v1 behaviour, kept for ablation)
        if direction == 'long':
            anchor = _swing_before_break(sl_recent, bi, ref=entry, want='below')
            sl = (anchor if anchor is not None else float(np.min(low[bi:i + 1]))) - p.SL_BUFFER * a
        else:
            anchor = _swing_before_break(sh_recent, bi, ref=entry, want='above')
            sl = (anchor if anchor is not None else float(np.max(high[bi:i + 1]))) + p.SL_BUFFER * a
    sl_dist = abs(entry - sl)
    if sl_dist < p.MIN_SL_DOLLARS:
        return None
    if (direction == 'long' and sl >= entry) or (direction == 'short' and sl <= entry):
        return None

    # ── E1 structural + %-capped TP (closest-to-entry) + S1b opposing engine levels ──
    tp = compute_tp_v2(direction, entry, sl_dist, a, i, sig, p, levels)
    rr = abs(tp - entry) / sl_dist
    # ── E2 R:R floor (culls "break a close strong level" trades) ──
    if rr < p.RR_FLOOR:
        return None

    return ZTTSetup(
        entry_index=i, entry_time=ts, direction=direction, mode=mode,
        entry_price=round(entry, 3), stop_loss=round(sl, 3), take_profit=round(tp, 3),
        level_price=round(lv.price, 3), level_touches=lv.clean, rr=round(rr, 2),
        break_index=bi, level_disrespect=lv.disrespect,
    )


def compute_tp_v2(direction: str, entry: float, sl_dist: float, a: float, i: int,
                  sig: dict, p: ZTTV2Params, levels=None) -> float:
    """E1: TP = closest-to-entry of {3R, opposing significant level − buffer, %-cap}.

    The opposing-level candidate is capped STRUCT_CAP_BUFFER·ATR short of the level
    (we don't target right into a significant level). All candidates are on the
    trade's far side; we take the nearest (most conservative) one.
    """
    sign = 1.0 if direction == 'long' else -1.0
    tp_3r = entry + sign * p.MIN_RR * sl_dist
    tp_pct = entry * (1.0 + sign * p.MAX_MOVE_PCT)
    dists = [abs(tp_3r - entry), abs(tp_pct - entry)]
    if p.enforce_opposing:                               # optional: cap a buffer short of a strong level
        for opp in _opposing_levels(direction, entry, i, sig, p, levels):
            capped = opp - sign * p.STRUCT_CAP_BUFFER * a
            d = (capped - entry) * sign                  # signed distance on the far side
            if d > 0:
                dists.append(d)
    return entry + sign * min(dists)
