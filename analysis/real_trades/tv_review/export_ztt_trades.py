"""Export ZTT setups for a date window into (a) a faithful trade CSV, (b) a blank
review log for the user's take/skip feedback, and (c) a TradingView Pine overlay.

This is the "audit overlay" half of the screener feedback loop (ZTT_PLAN open paths):
ZTT flags the setups -> the user reviews each on OANDA:XAUUSD 10m -> labels take/skip
+ why -> those labels become the discrimination filter the 25 positives never gave us.

FIDELITY GUARANTEES (so the overlay == what the engine actually produced):
  * Setups come straight from src.regimes.ztt.generate_setups (no re-derivation).
  * Each setup's outcome is walked forward with the SAME phantom-safe rule as
    phase4/backtest_ztt.py: an exit only fires when price ACTUALLY trades to SL/TP
    (low<=SL / high>=TP). No intrabar peeking; SL wins an intrabar tie (conservative).
  * Session-gated cost (src.regimes.ztt_costs) is applied adverse to entry & exit,
    so the realized-R column reflects realistic fills, not the raw 3R geometry.
  * Outcomes are computed INDEPENDENTLY per setup (no position-overlap blocking) —
    the user is reviewing each setup on its own merits, not a sequential P&L run.

Usage (from repo root):
    py analysis/real_trades/tv_review/export_ztt_trades.py [config] [days] [period_file]
      config      : base | raw | full          (default base — the screener default)
      days        : trailing window to display  (default 31)
      period_file : 1y | 10y                    (default 1y)

Outputs (analysis/real_trades/tv_review/):
    ztt_trades_<window>.csv        full trade list + features + outcome
    ztt_review_<window>.csv        same rows, blank decision/reason/notes for labeling
    ztt_overlay_<window>.pine      paste into TradingView Pine editor on OANDA:XAUUSD 10m
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.regimes.ztt import generate_setups, compute_indicators, shift_signals, ZTTParams  # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
MAX_HOLD = 144   # ~1 trading day on 10m, matches phase4 backtest

_CONFIGS = {
    'base': ZTTParams(req_momentum=False, req_fvg=False, req_sweep=False),  # ~2-3/day
    'raw':  ZTTParams(),   # geometry only (apply_gates=False below) — ~6/day, richest
    'full': ZTTParams(),   # all shift gates on
}


def _walk_outcome(df, s):
    """Phantom-safe forward walk for ONE setup. Returns (exit_iloc, exit_price, kind)."""
    high, low, close = df['High'].values, df['Low'].values, df['Close'].values
    ei = s.entry_index
    end = min(len(df), ei + 1 + MAX_HOLD)
    for j in range(ei + 1, end):
        if s.direction == 'long':
            if low[j] <= s.stop_loss:            # SL first (conservative tie)
                return j, s.stop_loss, 'loss'
            if high[j] >= s.take_profit:
                return j, s.take_profit, 'win'
        else:
            if high[j] >= s.stop_loss:
                return j, s.stop_loss, 'loss'
            if low[j] <= s.take_profit:
                return j, s.take_profit, 'win'
    return end - 1, float(close[end - 1]), 'timeout'   # ran out of hold time


def _realized_r(df, s, exit_iloc, exit_price):
    """Realized R-multiple after session-gated cost applied adverse to both fills."""
    hours = df.index.hour.values
    owc = COST.fill_cost_one_way(int(hours[s.entry_index]))
    oxc = COST.fill_cost_one_way(int(hours[exit_iloc]))
    if s.direction == 'long':
        entry = s.entry_price + owc
        exit_fill = exit_price - oxc
        pnl = exit_fill - entry
    else:
        entry = s.entry_price - owc
        exit_fill = exit_price + oxc
        pnl = entry - exit_fill
    risk = abs(s.entry_price - s.stop_loss)
    return round(pnl / risk, 2) if risk > 0 else 0.0


def build(config='base', days=31, period_file='1y'):
    p = _CONFIGS[config]
    apply_gates = (config != 'raw')
    src = ROOT / f'data/cache/oanda_gold_{period_file}_10m.csv'
    df = pd.read_csv(src, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')

    d = compute_indicators(df, p)                       # for feature extraction
    setups = generate_setups(df, p, apply_gates=apply_gates)

    window_start = df.index[-1] - pd.Timedelta(days=days)
    setups = [s for s in setups if s.entry_time >= window_start]
    if not setups:
        print(f"No ZTT setups in the last {days} days for config '{config}'.")
        return None

    rows = []
    for n, s in enumerate(setups, 1):
        xj, xprice, kind = _walk_outcome(df, s)
        rr = _realized_r(df, s, xj, xprice)
        sig = shift_signals(d, s, p)
        bi = s.break_index
        rows.append({
            'n': n,
            'entry_time': s.entry_time.strftime('%Y-%m-%d %H:%M'),
            'entry_ms': int(s.entry_time.timestamp() * 1000),
            'exit_ms': int(df.index[xj].timestamp() * 1000),
            'direction': s.direction, 'mode': s.mode,
            'entry_price': s.entry_price, 'stop_loss': s.stop_loss,
            'take_profit': s.take_profit, 'level_price': s.level_price,
            'level_touches': s.level_touches, 'level_disrespect': s.level_disrespect,
            'rr_target': s.rr, 'outcome': kind, 'realized_r': rr,
            'exit_price': round(xprice, 3),
            'exit_time': df.index[xj].strftime('%Y-%m-%d %H:%M'),
            'sig_momentum': sig['momentum'], 'sig_fvg': sig['fvg'], 'sig_sweep': sig['sweep'],
            'htf_up': bool(d['HTF_FAST'].iat[bi] > d['HTF_SLOW'].iat[bi]),
            'session': COST.session_label(int(df.index[s.entry_index].hour)),
            'atr': round(float(d['ATR'].iat[bi]), 2),
        })
    trades = pd.DataFrame(rows)

    w0 = setups[0].entry_time.strftime('%Y-%m-%d')
    w1 = setups[-1].entry_time.strftime('%Y-%m-%d')
    tag = f"{w0}_to_{w1}_{config}"
    csv_path = OUT_DIR / f'ztt_trades_{tag}.csv'
    review_path = OUT_DIR / f'ztt_review_{tag}.csv'
    pine_path = OUT_DIR / f'ztt_overlay_{tag}.pine'

    trades.to_csv(csv_path, index=False)
    review = trades[['n', 'entry_time', 'direction', 'mode', 'entry_price', 'stop_loss',
                     'take_profit', 'rr_target', 'outcome', 'realized_r', 'level_price',
                     'level_touches', 'session']].copy()
    review['decision'] = ''      # take | skip
    review['reason'] = ''        # WHY — the discretionary signal
    review['notes'] = ''
    review.to_csv(review_path, index=False)

    pine = _make_pine(trades, tag)
    pine_path.write_text(pine, encoding='utf-8')

    wins = (trades['outcome'] == 'win').sum()
    losses = (trades['outcome'] == 'loss').sum()
    tos = (trades['outcome'] == 'timeout').sum()
    print(f"=== ZTT audit overlay — {config} config, {w0} -> {w1} ===")
    print(f"  {len(trades)} setups : {wins} win / {losses} loss / {tos} timeout "
          f"(geometry hit-rate {100*wins/len(trades):.0f}%)")
    print(f"  net realized R (1R risk each, independent): {trades['realized_r'].sum():+.1f}R")
    print(f"  trades  -> {csv_path.name}")
    print(f"  review  -> {review_path.name}   (fill decision/reason/notes)")
    print(f"  overlay -> {pine_path.name}      (paste into TradingView Pine editor)")
    return trades


def _pine_arr(name, vals, kind='float'):
    if kind == 'str':
        body = ', '.join(f'"{v}"' for v in vals)
    elif kind == 'int':
        body = ', '.join(str(int(v)) for v in vals)
    else:
        body = ', '.join(f'{float(v)}' for v in vals)
    return f"var {name} = array.from({body})"


def _make_pine(t, tag):
    """Emit a self-contained Pine v5 overlay that draws every exported trade."""
    n = len(t)
    arrs = "\n".join([
        _pine_arr('e_ms', t['entry_ms'], 'int'),
        _pine_arr('x_ms', t['exit_ms'], 'int'),
        _pine_arr('entry', t['entry_price']),
        _pine_arr('sl', t['stop_loss']),
        _pine_arr('tp', t['take_profit']),
        _pine_arr('lvl', t['level_price']),
        _pine_arr('is_long', [1 if d == 'long' else 0 for d in t['direction']], 'int'),
        _pine_arr('won', [1 if o == 'win' else (0 if o == 'loss' else 2) for o in t['outcome']], 'int'),
        _pine_arr('rr', t['realized_r']),
        _pine_arr('lbl', [f"#{r.n} {r.mode[:4]} {r.direction[0].upper()} {r.realized_r:+.1f}R"
                          for r in t.itertuples()], 'str'),
    ])
    return f'''//@version=5
// ZTT AUDIT OVERLAY — autogenerated, window {tag}
// Source of truth: src/regimes/ztt.py via analysis/real_trades/tv_review/export_ztt_trades.py
// HOW TO USE: open OANDA:XAUUSD, set timeframe to 10m, Pine editor -> paste -> Add to chart.
//   Boxes = the EXACT setups ZTT produced. Green box = profit zone (entry->TP),
//   red box = risk zone (entry->SL), spanning entry bar to the bar the trade closed.
//   Gray dashed line = the respected/flipped level. Label at entry shows
//   #n mode dir realized-R (after session-gated cost). Green label = win, red = loss, gray = timeout.
//   WMA(144)/SMMA(5) are plotted natively so you see the same trend context the engine used.
indicator("ZTT Audit Overlay {tag}", overlay=true, max_boxes_count=500, max_labels_count=500, max_lines_count=500)

plot(ta.wma(close, 144), "WMA 144", color=color.new(color.orange, 0), linewidth=2)
plot(ta.rma(close, 5),  "SMMA 5",  color=color.new(color.aqua, 0), linewidth=1)

{arrs}

if barstate.islast
    for k = 0 to {n - 1}
        em = array.get(e_ms, k)
        xm = array.get(x_ms, k)
        en = array.get(entry, k)
        s  = array.get(sl, k)
        p  = array.get(tp, k)
        lv = array.get(lvl, k)
        lng = array.get(is_long, k) == 1
        w   = array.get(won, k)
        txt = array.get(lbl, k)
        col = w == 1 ? color.lime : (w == 0 ? color.red : color.gray)
        // profit zone (entry -> TP) green, risk zone (entry -> SL) red
        ptop = lng ? p : en
        pbot = lng ? en : p
        rtop = lng ? en : s
        rbot = lng ? s : en
        box.new(em, ptop, xm, pbot, xloc=xloc.bar_time, border_color=color.new(color.green, 60), bgcolor=color.new(color.green, 88))
        box.new(em, rtop, xm, rbot, xloc=xloc.bar_time, border_color=color.new(color.red, 60), bgcolor=color.new(color.red, 88))
        line.new(em, lv, xm, lv, xloc=xloc.bar_time, color=color.new(color.gray, 20), style=line.style_dashed, width=1)
        label.new(em, lng ? pbot : ptop, txt, xloc=xloc.bar_time, yloc=yloc.price, style=lng ? label.style_label_up : label.style_label_down, color=color.new(col, 25), textcolor=color.white, size=size.small)
'''


if __name__ == '__main__':
    cfg = sys.argv[1] if len(sys.argv) > 1 else 'base'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 31
    pf = sys.argv[3] if len(sys.argv) > 3 else '1y'
    build(config=cfg, days=days, period_file=pf)
