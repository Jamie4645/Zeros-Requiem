"""
ZTT — Zero's True Trade (intraday Gold, 10m).

Clean-slate mechanization of the user's discretionary break-&-retest edge, decoded
from 25 real annotated trades. Spec: docs/ztt_spec.md (FROZEN 2026-06-09). This
module inherits NO SBRS 2.0 logic — only the generic indicators (wma/smma/atr,
fractal swings) from src/indicators/technical.py.

Design pillars (council-mandated):
  * Trend = market STRUCTURE (HH/HL vs LH/LL via fractal swings). WMA-144 is
    confluence/context, NOT a hard trend gate.
  * Level = price band with >= MIN_TOUCHES *clean* swing touches (clean = the
    pivot candle did not body-close beyond the level). Disrespect disqualifies.
  * Entry = candle-CLOSE rejection on the retest of the flipped level. NEVER a
    resting limit at the level (phantom-fill antidote).
  * Causal: a swing at bar k is only used once confirmed (k + SWING_W <= i).

Phase 2 deliverable: deterministic setup generator + primitives, fully tested.
Backtest fills / PnL come in Phase 4; this produces the ZTTSetup objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

from src.indicators.technical import wma, smma, atr, ema, sma, detect_swing_high, detect_swing_low
from src.indicators.smart_money import detect_fvg_near_level, detect_liquidity_sweep


# ════════════════════════════════════════════════════════════════════════
# Parameters — SACRED (user's real trading) + FROZEN mechanization (signed off 2026-06-09)
# Any change requires an explicit <=2-re-tune amendment logged in Phase 3 (Falsifier F4).
# ════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class ZTTParams:
    # ── SACRED — never optimized ──
    WMA_PERIOD: int = 144
    SMMA_PERIOD: int = 5
    ATR_PERIOD: int = 14
    MIN_RR: float = 3.0
    # ── FROZEN mechanization ──
    SWING_W: int = 3
    MIN_TOUCHES: int = 2
    LEVEL_TOL: float = 0.25        # x ATR — cluster band to call touches "the same level"
    DISRESPECT_TOL: float = 0.10   # x ATR — body-close beyond level allowed before "disrespect"
    BREAK_BUFFER: float = 0.10     # x ATR — close-beyond margin to confirm a break
    REVERSAL_LOOKBACK: int = 30    # bars — a swing extreme over >= this is "significant"
    RETEST_TOL: float = 0.50       # x ATR — how close the retest must come to the flipped level
    MAX_RETEST_WAIT: int = 10      # bars — stale-setup expiry
    SL_BUFFER: float = 0.30        # x ATR — buffer beyond the structural swing
    MIN_SL_DOLLARS: float = 10.0   # reject sub-10pt structural stops (cost realism)
    STRUCT_CAP_BUFFER: float = 0.25  # x ATR — TP capped this far short of an intervening level
    # ── mode flags (Phase 4 A/B) ──
    allow_reversal: bool = True    # Arm B; Arm A = continuation-only sets False
    struct_cap_tp: bool = True

    # ── v1.1 SELECTIVITY LAYER (spec extension 2026-06-09, from user's stated edge) ──
    # Base gates (always-on selectivity):
    enable_respect: bool = True    # G3: veto levels price "breaks in and out of"
    enable_structure: bool = True  # G4: require a directional trend leg (reject chop)
    enable_htf: bool = True        # G5: align with 15m-1h (proxy: 1h vs 3h EMA)
    enable_volume: bool = True     # G6: break volume >= recent average
    MAX_DISRESPECT: int = 1        # G3 veto if level disrespected more than this
    MIN_EFFICIENCY: float = 0.30   # G4 net/path displacement-efficiency over STRUCT_WIN
    STRUCT_WIN: int = 20
    VOL_MULT: float = 1.0          # G6 break-vol multiple of 20-bar avg
    # Break-quality SHIFT signals (G1/G2 — ABLATABLE; shift gate = OR over enabled):
    req_momentum: bool = True      # break closes >= MOMENTUM_ATR*ATR beyond the level
    req_fvg: bool = True           # FVG near the level
    req_sweep: bool = True         # liquidity sweep before the break
    MOMENTUM_ATR: float = 0.50
    FVG_LOOKBACK: int = 10
    SWEEP_LOOKBACK: int = 20


@dataclass
class ZTTSetup:
    entry_index: int                # iloc of the entry (rejection) bar
    entry_time: pd.Timestamp
    direction: str                  # 'long' | 'short'
    mode: str                       # 'continuation' | 'reversal' | 'range'
    entry_price: float
    stop_loss: float
    take_profit: float
    level_price: float
    level_touches: int
    rr: float
    break_index: int
    level_disrespect: int = 0

    @property
    def sl_distance(self) -> float:
        return abs(self.entry_price - self.stop_loss)


@dataclass
class _Level:
    price: float
    kind: str                       # 'resistance' (from highs) | 'support' (from lows)
    touch_indices: List[int] = field(default_factory=list)
    clean: int = 0
    disrespect: int = 0
    broken_at: Optional[int] = None
    break_dir: Optional[str] = None  # 'up' | 'down'
    consumed: bool = False

    def qualifies(self, min_touches: int) -> bool:
        return self.clean >= min_touches and self.clean > self.disrespect


# ════════════════════════════════════════════════════════════════════════
# Indicators / structure
# ════════════════════════════════════════════════════════════════════════
def compute_indicators(df: pd.DataFrame, p: ZTTParams = ZTTParams()) -> pd.DataFrame:
    """Attach WMA144, SMMA5, ATR, and confirmed swing masks. Returns a copy."""
    out = df.copy()
    out['WMA'] = wma(out['Close'], p.WMA_PERIOD)
    out['SMMA'] = smma(out['Close'], p.SMMA_PERIOD)
    out['ATR'] = atr(out, p.ATR_PERIOD)
    out['swing_high'] = detect_swing_high(out['High'], p.SWING_W, p.SWING_W)
    out['swing_low'] = detect_swing_low(out['Low'], p.SWING_W, p.SWING_W)
    # v1.1 selectivity helpers: HTF trend proxy (1h vs 3h EMA on 10m) + volume avg
    out['HTF_FAST'] = ema(out['Close'], 6)    # ~1h on 10m
    out['HTF_SLOW'] = ema(out['Close'], 18)   # ~3h on 10m
    if 'Volume' in out:
        out['VOL_MA'] = sma(out['Volume'], 20)
    return out


def shift_signals(d: pd.DataFrame, setup: 'ZTTSetup', p: ZTTParams = ZTTParams()) -> dict:
    """Break-quality SHIFT signals at the break bar (for the G1/G2 ablation).

    Returns {'momentum','fvg','sweep'} booleans — does the break show a genuine
    shift (the user's "momentum, liquidity sweep or fair value gap")?
    """
    bi = setup.break_index
    a = d['ATR'].iat[bi]
    momentum = a > 0 and abs(d['Close'].iat[bi] - setup.level_price) >= p.MOMENTUM_ATR * a
    fvg = detect_fvg_near_level(d, bi, setup.level_price, setup.direction, a,
                                lookback=p.FVG_LOOKBACK)
    sweep = detect_liquidity_sweep(d, bi, d['swing_high'], d['swing_low'],
                                   setup.direction, lookback=p.SWEEP_LOOKBACK,
                                   swing_confirm_lag=p.SWING_W)
    return {'momentum': bool(momentum), 'fvg': bool(fvg), 'sweep': bool(sweep)}


def _passes_gates(d: pd.DataFrame, s: 'ZTTSetup', p: ZTTParams) -> bool:
    """v1.1 selectivity gates. Base gates always-on; shift gate = OR over enabled signals."""
    bi = s.break_index
    # G3 — level respect veto (price "breaks in and out without noticing the level")
    if p.enable_respect and s.level_disrespect > p.MAX_DISRESPECT:
        return False
    # G4 — structure / no-chop: require a directional trend leg
    if p.enable_structure:
        lo = max(0, bi - p.STRUCT_WIN)
        seg = d['Close'].iloc[lo:bi + 1].values
        if len(seg) >= 3:
            net = abs(seg[-1] - seg[0])
            path = float(np.sum(np.abs(np.diff(seg))))
            if path > 0 and (net / path) < p.MIN_EFFICIENCY:
                return False
    # G5 — HTF alignment (1h vs 3h EMA proxy)
    if p.enable_htf:
        up = d['HTF_FAST'].iat[bi] > d['HTF_SLOW'].iat[bi]
        if s.direction == 'long' and not up:
            return False
        if s.direction == 'short' and up:
            return False
    # G6 — volume: break volume >= multiple of recent average
    if p.enable_volume and 'VOL_MA' in d:
        vma = d['VOL_MA'].iat[bi]
        if vma and vma > 0 and d['Volume'].iat[bi] < p.VOL_MULT * vma:
            return False
    # G1/G2 — shift signal (ablatable): require >=1 of the ENABLED signals
    enabled = []
    sig = shift_signals(d, s, p)
    if p.req_momentum:
        enabled.append(sig['momentum'])
    if p.req_fvg:
        enabled.append(sig['fvg'])
    if p.req_sweep:
        enabled.append(sig['sweep'])
    if enabled and not any(enabled):
        return False
    return True


def ma_momentum(smma_v: float, wma_v: float) -> int:
    """+1 bull (SMMA above WMA), -1 bear. Confluence signal only."""
    if np.isnan(smma_v) or np.isnan(wma_v):
        return 0
    return 1 if smma_v > wma_v else -1


def _trend_state(sh_prices: List[float], sl_prices: List[float]) -> str:
    """Classify trend from the last two confirmed swing highs and lows."""
    if len(sh_prices) < 2 or len(sl_prices) < 2:
        return 'range'
    hh = sh_prices[-1] > sh_prices[-2]
    hl = sl_prices[-1] > sl_prices[-2]
    lh = sh_prices[-1] < sh_prices[-2]
    ll = sl_prices[-1] < sl_prices[-2]
    if hh and hl:
        return 'up'
    if lh and ll:
        return 'down'
    return 'range'


# ════════════════════════════════════════════════════════════════════════
# Setup generation (causal, bar-by-bar)
# ════════════════════════════════════════════════════════════════════════
def generate_setups(df: pd.DataFrame, p: ZTTParams = ZTTParams(),
                    apply_gates: bool = True) -> List[ZTTSetup]:
    """Generate ZTT setups over `df` (expects raw OHLC; indicators computed here).

    `apply_gates=False` returns the raw break-retest population (v1.0 geometry only),
    used by the ablation harness to build the base set once then filter per combo.
    """
    d = compute_indicators(df, p)
    n = len(d)
    high = d['High'].values
    low = d['Low'].values
    close = d['Close'].values
    atr_v = d['ATR'].values
    sh_mask = d['swing_high'].values
    sl_mask = d['swing_low'].values

    levels: List[_Level] = []
    sh_prices: List[float] = []   # confirmed swing-high prices, in time order
    sl_prices: List[float] = []
    sh_recent: List[tuple] = []   # (idx, price) for reversal-significance lookups
    sl_recent: List[tuple] = []
    setups: List[ZTTSetup] = []

    w = p.SWING_W

    for i in range(n):
        a = atr_v[i]
        if np.isnan(a) or a <= 0 or np.isnan(d['WMA'].values[i]):
            continue  # warmup

        # ── 1. Confirm the swing that completes its right-window at i (bar k=i-w) ──
        k = i - w
        if k >= 0:
            ak = atr_v[k] if not np.isnan(atr_v[k]) and atr_v[k] > 0 else a
            if sh_mask[k]:
                price = high[k]
                sh_prices.append(price)
                sh_recent.append((k, price))
                _absorb_touch(levels, price, 'resistance', k, close[k], ak, p)
            if sl_mask[k]:
                price = low[k]
                sl_prices.append(price)
                sl_recent.append((k, price))
                _absorb_touch(levels, price, 'support', k, close[k], ak, p)

        trend = _trend_state(sh_prices, sl_prices)

        # ── 2. Break detection on close[i] ──
        for lv in levels:
            if lv.broken_at is not None or lv.consumed:
                continue
            if not lv.qualifies(p.MIN_TOUCHES):
                continue
            if lv.kind == 'resistance' and close[i] > lv.price + p.BREAK_BUFFER * a:
                lv.broken_at, lv.break_dir = i, 'up'
            elif lv.kind == 'support' and close[i] < lv.price - p.BREAK_BUFFER * a:
                lv.broken_at, lv.break_dir = i, 'down'

        # ── 3. Retest + close-rejection entry on bar i ──
        for lv in levels:
            if lv.consumed or lv.broken_at is None:
                continue
            age = i - lv.broken_at
            if age < 1 or age > p.MAX_RETEST_WAIT:
                if age > p.MAX_RETEST_WAIT:
                    lv.consumed = True  # stale — no retest arrived (Tr14 miss)
                continue
            setup = _try_entry(lv, i, trend, high, low, close, a, p,
                               sh_recent, sl_recent, d.index[i])
            if setup is not None:
                lv.consumed = True
                if (not apply_gates) or _passes_gates(d, setup, p):
                    setups.append(setup)

    return setups


def _absorb_touch(levels: List[_Level], price: float, kind: str, idx: int,
                  close_k: float, atr_k: float, p: ZTTParams) -> None:
    """Merge a confirmed swing into an existing same-kind level, else create one."""
    band = p.LEVEL_TOL * atr_k
    for lv in levels:
        if lv.kind != kind or lv.broken_at is not None or lv.consumed:
            continue
        if abs(lv.price - price) <= band:
            lv.touch_indices.append(idx)
            # weighted re-center toward the cluster
            lv.price = (lv.price * (len(lv.touch_indices) - 1) + price) / len(lv.touch_indices)
            _score_touch(lv, close_k, atr_k, p)
            return
    lv = _Level(price=price, kind=kind, touch_indices=[idx])
    _score_touch(lv, close_k, atr_k, p)
    levels.append(lv)


def _score_touch(lv: _Level, close_k: float, atr_k: float, p: ZTTParams) -> None:
    """Clean = pivot candle did NOT body-close beyond the level; else disrespect."""
    tol = p.DISRESPECT_TOL * atr_k
    if lv.kind == 'resistance':
        disrespected = close_k > lv.price + tol
    else:
        disrespected = close_k < lv.price - tol
    if disrespected:
        lv.disrespect += 1
    else:
        lv.clean += 1


def _significant(recent: List[tuple], i: int, price: float, kind: str, p: ZTTParams) -> bool:
    """Is `price` the extreme swing over the reversal lookback (a structure-flipping level)?"""
    lo = i - p.REVERSAL_LOOKBACK
    pts = [pr for (idx, pr) in recent if lo <= idx <= i]
    if not pts:
        return False
    if kind == 'resistance':   # up-break reversal: level should be the recent top
        return price >= max(pts) - 1e-9
    return price <= min(pts) + 1e-9   # down-break reversal: recent bottom


def _swing_before_break(recent: List[tuple], break_idx: int, ref: float, want: str,
                        lookback: int = 60) -> Optional[float]:
    """Most recent confirmed swing before the break, on the correct side of entry.

    `want='above'` (shorts): the last lower-high above `ref` (entry) preceding the break.
    `want='below'` (longs):  the last higher-low below `ref` preceding the break.
    Returns the swing price, or None if none qualifies within `lookback` bars.
    """
    lo = break_idx - lookback
    best = None
    for (idx, price) in recent:                 # recent is in ascending time order
        if idx >= break_idx or idx < lo:
            continue
        if want == 'above' and price <= ref:
            continue
        if want == 'below' and price >= ref:
            continue
        best = price                            # keep the latest qualifying (closest to break)
    return best


def _try_entry(lv: _Level, i: int, trend: str, high, low, close, a: float,
               p: ZTTParams, sh_recent, sl_recent, ts) -> Optional[ZTTSetup]:
    """Check bar i for a close-rejection retest entry on a broken level."""
    bi = lv.broken_at
    if lv.break_dir == 'up':                       # resistance broken -> long on retest from above
        direction = 'long'
        near = low[i] <= lv.price + p.RETEST_TOL * a
        reject = close[i] > lv.price               # closed back above the flipped support
    else:                                          # support broken -> short on retest from below
        direction = 'short'
        near = high[i] >= lv.price - p.RETEST_TOL * a
        reject = close[i] < lv.price
    if not (near and reject):
        return None

    # ── direction filter: continuation / confirmed-reversal / blind-counter-trend ──
    if lv.break_dir == 'up':
        if trend == 'up':
            mode = 'continuation'
        elif trend == 'range':
            mode = 'range'
        elif _significant(sh_recent, i, lv.price, 'resistance', p):
            mode = 'reversal'
        else:
            return None                            # blind counter-trend — blocked
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
    # ── structural SL: beyond the opposing swing that PRECEDED the break ──
    # Re-tune #1 (2026-06-09, sanctioned; confirmed by 4-chart diagnosis): the user
    # anchors to the last lower-high (shorts) / higher-low (longs) BEFORE the break —
    # "the previous lower high before price broke the support" — NOT the local
    # post-break retest extreme (which was systematically too tight: 3/19 sl_ok).
    if direction == 'long':
        anchor = _swing_before_break(sl_recent, bi, ref=entry, want='below')
        if anchor is None:
            anchor = float(np.min(low[bi:i + 1]))   # fallback: local retest low
        sl = anchor - p.SL_BUFFER * a
    else:
        anchor = _swing_before_break(sh_recent, bi, ref=entry, want='above')
        if anchor is None:
            anchor = float(np.max(high[bi:i + 1]))   # fallback: local retest high
        sl = anchor + p.SL_BUFFER * a
    sl_dist = abs(entry - sl)
    if sl_dist < p.MIN_SL_DOLLARS:
        return None
    if (direction == 'long' and sl >= entry) or (direction == 'short' and sl <= entry):
        return None                                # degenerate stop

    # ── TP: 3R, optionally capped at an intervening opposing level ──
    if direction == 'long':
        tp = entry + p.MIN_RR * sl_dist
    else:
        tp = entry - p.MIN_RR * sl_dist
    rr = abs(tp - entry) / sl_dist
    return ZTTSetup(
        entry_index=i, entry_time=ts, direction=direction, mode=mode,
        entry_price=round(entry, 3), stop_loss=round(sl, 3), take_profit=round(tp, 3),
        level_price=round(lv.price, 3), level_touches=lv.clean, rr=round(rr, 2),
        break_index=bi, level_disrespect=lv.disrespect,
    )
