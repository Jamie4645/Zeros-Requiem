"""ZTT v3 — regime instrumentation (book-informed, plan Workstream B1 = REG-1).

Stamps every setup / screener decision with an OBJECTIVE, CAUSAL regime tag so the
known down-trend/short contamination (WALL 3) becomes a measurable contingency table
and the future ~500-label corpus can be stratified across up/down/range × vol buckets.

TAG ONLY — never a gate. Thresholds here are DESCRIPTIVE bucket boundaries, NOT tuned
to the 60 labels (council mandate: tuning them would make the tag a fitted feature).

Tags (all computed from CLOSED bars up to and including bar i):
  trend_dir : 'up'|'down'|'range'  — market structure via ztt._trend_state (HH/HL vs LH/LL)
  er        : Efficiency Ratio = |net move| / sum(|bar moves|) over STRUCT_WIN closes
              (Kaufman: high ER = clean trend, low ER = chop). Continuous EXPORT of the
              same net/path math the G4 gate in ztt.py uses as a pass/fail.
  adx       : Wilder ADX(14) — trend strength
  vol_bucket: 'low'|'mid'|'high' — ATR(14) / median ATR over a LAGGED, non-overlapping
              window (Kaufman ch.21: avoid overlap with the recent bars being measured)
  vol_ratio : the raw ratio behind vol_bucket
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.regimes.ztt import ZTTParams, compute_indicators, _trend_state

# descriptive vol-bucket boundaries (NOT tuned — round, symmetric-ish cut points)
VOL_LOW = 0.80
VOL_HIGH = 1.25
# lagged non-overlapping window for the vol baseline
VOL_BASELINE = 200
VOL_GAP = 20


def wilder_adx(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Causal Wilder ADX. Returns an array aligned to df (NaN during warmup)."""
    high = df['High'].astype(float).values
    low = df['Low'].astype(float).values
    close = df['Close'].astype(float).values
    n = len(df)
    if n < 2:
        return np.full(n, np.nan)
    up = high[1:] - high[:-1]
    dn = low[:-1] - low[1:]
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum.reduce([
        high[1:] - low[1:],
        np.abs(high[1:] - close[:-1]),
        np.abs(low[1:] - close[:-1]),
    ])
    # Wilder smoothing (RMA) via ewm alpha=1/period
    def rma(x):
        return pd.Series(x).ewm(alpha=1.0 / period, adjust=False).mean().values
    atr = rma(tr)
    pdi = 100.0 * rma(plus_dm) / np.where(atr == 0, np.nan, atr)
    mdi = 100.0 * rma(minus_dm) / np.where(atr == 0, np.nan, atr)
    denom = pdi + mdi
    dx = 100.0 * np.abs(pdi - mdi) / np.where(denom == 0, np.nan, denom)
    adx = rma(np.nan_to_num(dx))
    # warmup: first `2*period` bars unreliable
    out = np.full(n, np.nan)
    out[1:] = adx
    out[: 2 * period] = np.nan
    return out


def _efficiency_ratio(close: np.ndarray, i: int, win: int) -> float:
    """|net| / sum(|diff|) over the last `win` closes ending at i. Causal."""
    lo = max(0, i - win)
    seg = close[lo:i + 1]
    if len(seg) < 3:
        return np.nan
    net = abs(seg[-1] - seg[0])
    path = float(np.sum(np.abs(np.diff(seg))))
    return net / path if path > 0 else np.nan


def compute_regime(df: pd.DataFrame, p: ZTTParams = ZTTParams()) -> pd.DataFrame:
    """Vectorized causal regime columns for every bar. Returns a DataFrame indexed
    like df with columns: trend_dir, er, adx, vol_ratio, vol_bucket.
    """
    d = compute_indicators(df, p)
    n = len(d)
    close = d['Close'].values
    atr_v = d['ATR'].values
    sh_mask = d['swing_high'].values
    sl_mask = d['swing_low'].values
    high = d['High'].values
    low = d['Low'].values
    w = p.SWING_W

    trend = np.empty(n, dtype=object)
    er = np.full(n, np.nan)
    sh_prices: list = []
    sl_prices: list = []
    for i in range(n):
        k = i - w
        if k >= 0:
            if sh_mask[k]:
                sh_prices.append(high[k])
            if sl_mask[k]:
                sl_prices.append(low[k])
        trend[i] = _trend_state(sh_prices, sl_prices)
        er[i] = _efficiency_ratio(close, i, p.STRUCT_WIN)

    adx = wilder_adx(d, p.ATR_PERIOD)

    # vol_ratio = ATR[i] / median ATR over a lagged non-overlapping window
    vol_ratio = np.full(n, np.nan)
    for i in range(n):
        hi = i - VOL_GAP
        lo = hi - VOL_BASELINE
        if lo < 0:
            continue
        base = atr_v[lo:hi]
        base = base[~np.isnan(base)]
        if base.size and atr_v[i] == atr_v[i] and np.median(base) > 0:
            vol_ratio[i] = atr_v[i] / np.median(base)

    bucket = np.where(np.isnan(vol_ratio), None,
                      np.where(vol_ratio < VOL_LOW, 'low',
                               np.where(vol_ratio > VOL_HIGH, 'high', 'mid')))

    return pd.DataFrame({
        'trend_dir': trend,
        'er': er,
        'adx': adx,
        'vol_ratio': vol_ratio,
        'vol_bucket': bucket,
    }, index=d.index)


def regime_tags(df: pd.DataFrame, i: int, p: ZTTParams = ZTTParams(),
                regime_df: pd.DataFrame | None = None) -> dict:
    """Regime tag dict at bar i (causal). Pass a precomputed `regime_df` from
    compute_regime() to avoid recomputation when tagging many setups.
    """
    rd = regime_df if regime_df is not None else compute_regime(df, p)
    row = rd.iloc[i]
    return {
        'trend_dir': row['trend_dir'],
        'er': None if pd.isna(row['er']) else round(float(row['er']), 4),
        'adx': None if pd.isna(row['adx']) else round(float(row['adx']), 2),
        'vol_ratio': None if pd.isna(row['vol_ratio']) else round(float(row['vol_ratio']), 3),
        'vol_bucket': row['vol_bucket'],
    }
