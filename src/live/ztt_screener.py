"""ZTT v2 live screener / alerter — Gold 10m.

The VALIDATED deliverable from the 2026-06-14 v2 build: the autonomous selection
filter was falsified (the edge is the user's discretion), but the break-retest
geometry + false-bo/session filters + the F3-validated %-capped exits form a
high-recall SCREENER. This surfaces fresh setups for the user to take/skip; the
user IS the selection layer. Every alert is logged to a decisions CSV so take/skip
choices accumulate the multi-regime labels needed to one day learn discrimination.

Run a single scan (wire to a 10-min scheduler / the /loop skill):
    py -m src.live.ztt_screener                 # scan, alert fresh setups
    py -m src.live.ztt_screener --period 6mo --fresh 12 --backfill
Outputs:
    logs/ztt_screener/alerts.log        human-readable alert blocks
    logs/ztt_screener/decisions.csv     one row per alert + blank decision/reason (you fill)
    logs/ztt_screener/state.json        dedupe watermark (already-alerted setup keys)
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.data.oanda_fetcher import fetch_oanda
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params
from src.regimes.ztt_costs import DEFAULT_COST as COST
from src.regimes.ztt import compute_indicators
from src.regimes.ztt_regime import compute_regime, regime_tags

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'logs' / 'ztt_screener'
DECISIONS = OUT / 'decisions.csv'
ALERTS = OUT / 'alerts.log'
STATE = OUT / 'state.json'

DEC_COLS = ['alert_time_utc', 'entry_time', 'direction', 'mode', 'entry_price',
            'stop_loss', 'take_profit', 'rr', 'sl_pct', 'tp_pct', 'level_price',
            'level_touches', 'session',
            # ── B1 regime tags (REG-1): causal, descriptive, NEVER gated ──
            'trend_dir', 'er', 'adx', 'vol_ratio', 'vol_bucket',
            # ── C3 sizing features (SIZE-6): scale-invariant; for SIZING/regime
            #    validation only — NOT mined for selection (snoop guard). Last 4 are
            #    post-hoc fillable once the outcome is known. ──
            'atr_at_entry', 'sl_dist_atr', 'price_level',
            'realized_R', 'MFE_R', 'MAE_R', 'bars_held',
            'decision', 'reason']


def _key(s) -> str:
    """Stable id for a setup (entry bar + level) to dedupe across scans."""
    return f"{pd.Timestamp(s.entry_time).strftime('%Y-%m-%dT%H:%M')}|{round(s.level_price, 2)}|{s.direction}"


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {'alerted': []}


def _save_state(state: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2))


def _ensure_decisions_header() -> None:
    """Create decisions.csv — or MIGRATE it when its header predates DEC_COLS.

    2026-07-02 audit fix: this used to write a header only when the file was
    missing, so appending 27-field rows to an older 15-column file silently
    corrupted the label corpus. Any header mismatch now triggers a migration:
    old rows are re-mapped by column NAME (missing fields blank, decision/
    reason preserved) and the original file is kept as decisions.csv.bak*.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    if not DECISIONS.exists():
        with open(DECISIONS, 'w', newline='') as fh:
            csv.writer(fh).writerow(DEC_COLS)
        return
    with open(DECISIONS, newline='') as fh:
        rows = list(csv.reader(fh))
    if rows and rows[0] == DEC_COLS:
        return
    old_header = rows[0] if rows else []
    old_rows = rows[1:] if rows else []
    bak = DECISIONS.with_suffix('.csv.bak')
    n = 1
    while bak.exists():
        n += 1
        bak = DECISIONS.with_suffix(f'.csv.bak{n}')
    DECISIONS.replace(bak)
    with open(DECISIONS, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(DEC_COLS)
        for r in old_rows:
            d = dict(zip(old_header, r))
            w.writerow([d.get(c, '') for c in DEC_COLS])


def _alert_block(s, now: str) -> str:
    sl_pct = abs(s.entry_price - s.stop_loss) / s.entry_price * 100
    tp_pct = abs(s.take_profit - s.entry_price) / s.entry_price * 100
    sess = COST.session_label(int(pd.Timestamp(s.entry_time).hour))
    arrow = 'LONG' if s.direction == 'long' else 'SHORT'
    return (
        f"\n+-- ZTT SETUP  {arrow}  ({s.mode})  [{sess}]\n"
        f"|  setup bar : {pd.Timestamp(s.entry_time).strftime('%Y-%m-%d %H:%M')} UTC   (scanned {now})\n"
        f"|  entry     : {s.entry_price:.2f}\n"
        f"|  stop      : {s.stop_loss:.2f}   ({sl_pct:.2f}% / {abs(s.entry_price-s.stop_loss):.1f} pts)\n"
        f"|  target    : {s.take_profit:.2f}   ({tp_pct:.2f}% / {abs(s.take_profit-s.entry_price):.1f} pts)   R:R {s.rr:.2f}\n"
        f"|  level     : {s.level_price:.2f}   ({s.level_touches} clean touches)\n"
        f"+- your call: take / skip  ->  log it in {DECISIONS.name}\n"
    )


def _decision_row(s, now: str, reg: dict | None = None, atr_at_entry=None) -> list:
    sl_dist = abs(s.entry_price - s.stop_loss)
    sl_pct = round(sl_dist / s.entry_price * 100, 3)
    tp_pct = round(abs(s.take_profit - s.entry_price) / s.entry_price * 100, 3)
    sess = COST.session_label(int(pd.Timestamp(s.entry_time).hour))
    reg = reg or {}
    atr_e = round(float(atr_at_entry), 3) if atr_at_entry else ''
    sl_dist_atr = round(sl_dist / atr_at_entry, 3) if atr_at_entry else ''
    return [now, pd.Timestamp(s.entry_time).strftime('%Y-%m-%d %H:%M'), s.direction,
            s.mode, s.entry_price, s.stop_loss, s.take_profit, s.rr, sl_pct, tp_pct,
            s.level_price, s.level_touches, sess,
            reg.get('trend_dir', ''), reg.get('er', ''), reg.get('adx', ''),
            reg.get('vol_ratio', ''), reg.get('vol_bucket', ''),
            atr_e, sl_dist_atr, s.entry_price,   # C3 sizing features
            '', '', '', '',                       # realized_R, MFE_R, MAE_R, bars_held (post-hoc)
            '', '']


def scan(period: str = '3mo', fresh_bars: int = 6, backfill: bool = False,
         min_alert_rr: float = 0.5, params: ZTTV2Params | None = None) -> list:
    """One scan. Returns the list of NEW setups alerted this run.

    min_alert_rr suppresses absurdly-low-R:R alerts (where the %-cap/opposing pivot
    crushed the target) — noise reduction only, NOT a selection-edge filter.
    """
    params = params or ZTTV2Params()
    df = fetch_oanda('GC=F', '10m', period=period)
    setups = generate_setups_v2(df, params, apply_gates=True)
    if not setups:
        return []
    regime_df = compute_regime(df, params)   # B1: causal regime tags, one pass
    atr_v = compute_indicators(df, params)['ATR'].values   # C3: ATR at entry

    n = len(df)
    # "fresh" = entry bar within the last `fresh_bars` completed bars, unless backfilling
    cutoff_idx = 0 if backfill else max(0, n - 1 - fresh_bars)
    candidates = [s for s in setups if s.entry_index >= cutoff_idx and s.rr >= min_alert_rr]

    state = _load_state()
    seen = set(state.get('alerted', []))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    _ensure_decisions_header()

    new = []
    for s in candidates:
        k = _key(s)
        if k in seen:
            continue
        seen.add(k)
        new.append(s)
        block = _alert_block(s, now)
        print(block)
        with open(ALERTS, 'a', encoding='utf-8') as fh:
            fh.write(block)
        reg = regime_tags(df, s.entry_index, params, regime_df=regime_df)
        atr_e = atr_v[s.entry_index] if s.entry_index < len(atr_v) else None
        with open(DECISIONS, 'a', newline='') as fh:
            csv.writer(fh).writerow(_decision_row(s, now, reg, atr_e))

    state['alerted'] = sorted(seen)
    state['last_scan_utc'] = now
    state['last_bar_utc'] = pd.Timestamp(df.index[-1]).strftime('%Y-%m-%d %H:%M')
    _save_state(state)
    return new


def main():
    ap = argparse.ArgumentParser(description="ZTT v2 live screener — Gold 10m")
    ap.add_argument('--period', default='3mo', help="history to fetch for warmup (default 3mo)")
    ap.add_argument('--fresh', type=int, default=6,
                    help="alert setups whose entry bar is within the last N bars (default 6 = ~1h)")
    ap.add_argument('--backfill', action='store_true',
                    help="alert ALL un-seen setups in the window (initial population), not just fresh")
    ap.add_argument('--min-rr', type=float, default=0.5,
                    help="suppress alerts below this R:R (noise reduction, default 0.5)")
    args = ap.parse_args()

    new = scan(period=args.period, fresh_bars=args.fresh, backfill=args.backfill,
               min_alert_rr=args.min_rr)
    if not new:
        print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC] no new ZTT setups "
              f"(last bar checked written to {STATE}).")
    else:
        print(f"\n{len(new)} new setup(s) logged to {DECISIONS}. Fill in take/skip + reason.")


if __name__ == '__main__':
    main()
