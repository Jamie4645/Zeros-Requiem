"""ZTT Setup Screener + Labeling Loop.

The honest product after Phase 4: the ZTT geometry can't be auto-traded
(PF ~1.10), but it has near-perfect RECALL — it sees every break-retest setup.
So we use it as a human-in-the-loop SCREENER: it flags Gold 10m setups, logs each
with full features + blank take/skip columns, and the user applies the discretionary
judgment that IS the edge. Their labels accumulate the NEGATIVES needed to one day
learn the discrimination (the dataset 25 positives never gave us).

Usage:
    from src.screener.ztt_screener import run_screener
    run_screener()                      # fetch latest, log new setups, print alerts
    run_screener(config='raw')          # richer (all break-retests, ~6/day)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.regimes.ztt import generate_setups, compute_indicators, shift_signals, ZTTParams

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / 'analysis' / 'real_trades' / 'ztt_screener_log.csv'

# Columns: machine-filled features + blank user-labels (the learning target).
FEATURE_COLS = [
    'entry_time', 'direction', 'mode', 'entry_price', 'stop_loss', 'take_profit',
    'rr', 'level_price', 'level_touches', 'level_disrespect',
    'sig_momentum', 'sig_fvg', 'sig_sweep', 'htf_up', 'struct_eff', 'vol_ratio', 'atr',
]
LABEL_COLS = ['decision', 'reason', 'outcome']   # user fills: take/skip, why, win/loss/skip

_CONFIGS = {
    'base': ZTTParams(req_momentum=False, req_fvg=False, req_sweep=False),  # ~2-3/day, balanced
    'raw':  ZTTParams(),                                                    # ~6/day, richest labels
    'full': ZTTParams(),                                                   # all shift gates on
}


def _features(d: pd.DataFrame, s, p: ZTTParams) -> dict:
    bi = s.break_index
    a = d['ATR'].iat[bi]
    sig = shift_signals(d, s, p)
    lo = max(0, bi - p.STRUCT_WIN)
    seg = d['Close'].iloc[lo:bi + 1].values
    eff = (abs(seg[-1] - seg[0]) / max(np.sum(np.abs(np.diff(seg))), 1e-9)) if len(seg) >= 3 else np.nan
    vr = (d['Volume'].iat[bi] / d['VOL_MA'].iat[bi]) if ('VOL_MA' in d and d['VOL_MA'].iat[bi] > 0) else np.nan
    return {
        'entry_time': s.entry_time, 'direction': s.direction, 'mode': s.mode,
        'entry_price': s.entry_price, 'stop_loss': s.stop_loss, 'take_profit': s.take_profit,
        'rr': s.rr, 'level_price': s.level_price, 'level_touches': s.level_touches,
        'level_disrespect': s.level_disrespect,
        'sig_momentum': sig['momentum'], 'sig_fvg': sig['fvg'], 'sig_sweep': sig['sweep'],
        'htf_up': bool(d['HTF_FAST'].iat[bi] > d['HTF_SLOW'].iat[bi]),
        'struct_eff': round(float(eff), 3), 'vol_ratio': round(float(vr), 2) if vr == vr else np.nan,
        'atr': round(float(a), 2),
    }


def screen(df: pd.DataFrame, config: str = 'base') -> pd.DataFrame:
    """Run ZTT over `df`, return a DataFrame of setups with full features."""
    p = _CONFIGS[config]
    apply_gates = (config != 'raw')
    d = compute_indicators(df, p)
    setups = generate_setups(df, p, apply_gates=apply_gates)
    rows = [_features(d, s, p) for s in setups]
    out = pd.DataFrame(rows, columns=FEATURE_COLS)
    for c in LABEL_COLS:
        out[c] = ''
    return out


def update_log(setups: pd.DataFrame, log_path: Path = LOG_PATH) -> int:
    """Append NEW setups (dedup by entry_time) to the labeling log. Returns # added."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        existing = pd.read_csv(log_path)
        seen = set(existing['entry_time'].astype(str))
        fresh = setups[~setups['entry_time'].astype(str).isin(seen)]
        combined = pd.concat([existing, fresh], ignore_index=True)
    else:
        fresh = setups
        combined = setups.copy()
    combined.to_csv(log_path, index=False)
    return len(fresh)


def run_screener(df: Optional[pd.DataFrame] = None, config: str = 'base',
                 lookback_days: int = 14, alerts: int = 8) -> pd.DataFrame:
    """Fetch latest Gold 10m (or use `df`), screen, log new setups, print recent alerts."""
    if df is None:
        from src.data.oanda_fetcher import fetch_oanda
        df = fetch_oanda('GC=F', interval='10m', period='1mo')
    df = df.iloc[-int(lookback_days * 144 * 1.5):] if len(df) > lookback_days * 144 * 1.5 else df
    setups = screen(df, config=config)
    added = update_log(setups)
    print(f"ZTT screener [{config}] — {len(setups)} setups in window, {added} new logged -> {LOG_PATH.name}")
    if len(setups):
        recent = setups.tail(alerts)[['entry_time', 'direction', 'mode', 'entry_price',
                                      'stop_loss', 'take_profit', 'rr',
                                      'sig_momentum', 'sig_fvg', 'sig_sweep', 'htf_up']]
        print(recent.to_string(index=False))
    return setups


if __name__ == '__main__':
    cfg = sys.argv[1] if len(sys.argv) > 1 else 'base'
    run_screener(config=cfg)
