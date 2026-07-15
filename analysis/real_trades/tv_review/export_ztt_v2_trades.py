"""Export ZTT **v2** (latest screener config) setups for a DATE RANGE into a Pine
overlay + review CSV, for an out-of-sample take/skip review.

Differs from export_ztt_trades.py (v1, trailing-days, base config):
  * Uses src.regimes.ztt_v2.generate_setups_v2 with ZTTV2Params() defaults — the
    SHIPPED screener config (base geometry + false-bo + session + %-capped TP).
  * Selects an explicit [start, end] calendar window (default Jan-Feb 2026) instead
    of a trailing-days window — for reviewing a DIFFERENT regime than the May-Jun
    down-month already labelled (falsifier F5 regime hold-out + autonomy labels).
  * Applies the live screener's min-R:R alert floor (default 0.5) so the overlay ==
    what the screener would actually surface.

Same fidelity guarantees as v1: setups straight from the engine; phantom-safe
forward-walk for outcomes (SL wins intrabar tie); session-gated cost adverse on both
fills; outcomes independent per setup. Outcomes are CONTEXT — judge each on entry.

Usage (from repo root):
    py analysis/real_trades/tv_review/export_ztt_v2_trades.py [start] [end] [period_file] [min_rr]
      start/end   : YYYY-MM-DD   (default 2026-01-01 .. 2026-02-28)
      period_file : 1y | 10y     (default 1y; must span the window + warmup)
      min_rr      : alert floor   (default 0.5)

Outputs (analysis/real_trades/tv_review/):
    ztt_trades_<start>_to_<end>_v2.csv
    ztt_review_<start>_to_<end>_v2.csv     (blank decision/reason/notes — fill these)
    ztt_overlay_<start>_to_<end>_v2.pine   (paste into TradingView, OANDA:XAUUSD 10m)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.regimes.ztt import compute_indicators, shift_signals          # noqa: E402
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params         # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST                 # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
MAX_HOLD = 144


def _walk_outcome(df, s):
    high, low, close = df['High'].values, df['Low'].values, df['Close'].values
    ei = s.entry_index
    end = min(len(df), ei + 1 + MAX_HOLD)
    for j in range(ei + 1, end):
        if s.direction == 'long':
            if low[j] <= s.stop_loss:
                return j, s.stop_loss, 'loss'
            if high[j] >= s.take_profit:
                return j, s.take_profit, 'win'
        else:
            if high[j] >= s.stop_loss:
                return j, s.stop_loss, 'loss'
            if low[j] <= s.take_profit:
                return j, s.take_profit, 'win'
    return end - 1, float(close[end - 1]), 'timeout'


def _realized_r(df, s, exit_iloc, exit_price):
    hours = df.index.hour.values
    owc = COST.fill_cost_one_way(int(hours[s.entry_index]))
    oxc = COST.fill_cost_one_way(int(hours[exit_iloc]))
    if s.direction == 'long':
        pnl = (exit_price - oxc) - (s.entry_price + owc)
    else:
        pnl = (s.entry_price - owc) - (exit_price + oxc)
    risk = abs(s.entry_price - s.stop_loss)
    return round(pnl / risk, 2) if risk > 0 else 0.0


def build(start='2026-01-01', end='2026-02-28', period_file='1y', min_rr=0.5):
    p = ZTTV2Params()
    src = ROOT / f'data/cache/oanda_gold_{period_file}_10m.csv'
    df = pd.read_csv(src, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')

    lo = pd.Timestamp(start, tz='UTC')
    hi = pd.Timestamp(end, tz='UTC') + pd.Timedelta(days=1)   # inclusive of end day
    if df.index[0] > lo or df.index[-1] < hi - pd.Timedelta(days=1):
        print(f"WARNING: cache {df.index[0].date()}..{df.index[-1].date()} may not fully "
              f"span {start}..{end}. Use period_file=10y if the window is missing.")

    d = compute_indicators(df, p)
    setups = generate_setups_v2(df, p, apply_gates=True)
    setups = [s for s in setups if lo <= s.entry_time < hi and s.rr >= min_rr]
    setups.sort(key=lambda s: s.entry_index)
    if not setups:
        print(f"No ZTT v2 setups in {start}..{end} (min_rr={min_rr}).")
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

    tag = f"{start}_to_{end}_v2"
    trades.to_csv(OUT_DIR / f'ztt_trades_{tag}.csv', index=False)
    review = trades[['n', 'entry_time', 'direction', 'mode', 'entry_price', 'stop_loss',
                     'take_profit', 'rr_target', 'outcome', 'realized_r', 'level_price',
                     'level_touches', 'session']].copy()
    review['decision'] = ''
    review['reason'] = ''
    review['notes'] = ''
    review.to_csv(OUT_DIR / f'ztt_review_{tag}.csv', index=False)
    (OUT_DIR / f'ztt_overlay_{tag}.pine').write_text(_make_pine(trades, tag), encoding='utf-8')

    wins = (trades['outcome'] == 'win').sum()
    losses = (trades['outcome'] == 'loss').sum()
    tos = (trades['outcome'] == 'timeout').sum()
    longs = (trades['direction'] == 'long').sum()
    print(f"=== ZTT v2 audit overlay — screener config, {start} -> {end} ===")
    print(f"  {len(trades)} setups ({longs} long / {len(trades)-longs} short) : "
          f"{wins} win / {losses} loss / {tos} timeout (geometry hit-rate {100*wins/len(trades):.0f}%)")
    print(f"  net realized R (1R each, independent, after cost): {trades['realized_r'].sum():+.1f}R")
    print(f"  pine objects: {2*len(trades)} boxes + {len(trades)} lines + {len(trades)} labels "
          f"({'OK' if 2*len(trades) <= 500 else 'EXCEEDS 500 — split the window!'})")
    print(f"  -> ztt_overlay_{tag}.pine   |   ztt_review_{tag}.csv (fill decision/reason/notes)")
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
// ZTT v2 AUDIT OVERLAY — autogenerated, window {tag}
// Source of truth: src/regimes/ztt_v2.py via export_ztt_v2_trades.py (SCREENER config + %-capped TP)
// HOW TO USE: open OANDA:XAUUSD, set timeframe to 10m, Pine editor -> paste -> Add to chart.
//   Boxes = the EXACT setups ZTT v2 produced. Green box = profit zone (entry->TP, %-capped),
//   red box = risk zone (entry->SL), spanning entry bar to the bar the trade closed.
//   Gray dashed line = the respected/flipped level. Label at entry shows
//   #n mode dir realized-R (after session-gated cost). Green label = win, red = loss, gray = timeout.
//   WMA(144)/SMMA(5) plotted natively = the trend context the engine used.
//   NOTE: judge each setup on what you'd see AT ENTRY — the win/loss colour is hindsight.
indicator("ZTT v2 Overlay {tag}", overlay=true, max_boxes_count=500, max_labels_count=500, max_lines_count=500)

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
    start = sys.argv[1] if len(sys.argv) > 1 else '2026-01-01'
    end = sys.argv[2] if len(sys.argv) > 2 else '2026-02-28'
    pf = sys.argv[3] if len(sys.argv) > 3 else '1y'
    mrr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    build(start=start, end=end, period_file=pf, min_rr=mrr)
