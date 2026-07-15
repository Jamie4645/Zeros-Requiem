"""Phase 0 — pin the 25 real trades to OANDA M10 candles and resolve timezone.

The doc labels every timestamp "UTC+1". But UK clocks only sit at UTC+1 during
BST (29 Mar -> 25 Oct 2026); Jan/Feb/early-Mar trades would be GMT (UTC+0) if
the platform was London time. We resolve this EMPIRICALLY: for each trade, test
candidate UTC offsets {0h, 1h} and pick the one whose mapped M10 candle actually
contains the user's entry price. This both fixes the offset AND validates that
our OANDA data matches the user's broker fills.

A trade "pins" if the entry price lies within [low, high] of the candle that
covers (entry_local - offset). We report per-trade the best offset, containment
of entry/SL/TP-direction sanity, and any price mismatch (data drift).
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'data' / 'cache' / 'oanda_gold_1y_10m.csv'
TRADES = ROOT / 'analysis' / 'real_trades' / 'trades.csv'

df = pd.read_csv(DATA, index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
trades = pd.read_csv(TRADES)

OFFSETS = [pd.Timedelta(hours=1), pd.Timedelta(hours=0)]  # try BST first, then GMT


def bar_for(ts_utc):
    """Return the M10 bar whose [start, start+10m) contains ts_utc."""
    floored = ts_utc.floor('10min')
    if floored in df.index:
        return df.loc[floored]
    # nearest within 10 min (handles gap edges)
    pos = df.index.searchsorted(floored)
    for cand in (pos, pos - 1):
        if 0 <= cand < len(df):
            b = df.iloc[cand]
            if abs((df.index[cand] - floored).total_seconds()) <= 600:
                return b
    return None


rows = []
for _, t in trades.iterrows():
    local = pd.Timestamp(t['entry_local'], tz='UTC')  # treat label as wall-clock
    best = None
    for off in OFFSETS:
        ts_utc = local - off
        bar = bar_for(ts_utc)
        if bar is None:
            continue
        lo, hi = bar['Low'], bar['High']
        contained = lo <= t['entry_price'] <= hi
        # distance outside the bar (0 if contained)
        miss = 0.0 if contained else min(abs(t['entry_price'] - lo), abs(t['entry_price'] - hi))
        cand = dict(off=int(off.total_seconds() // 3600), contained=contained,
                    miss=miss, lo=lo, hi=hi, ts_utc=ts_utc)
        if best is None or (cand['contained'] and not best['contained']) or \
           (cand['contained'] == best['contained'] and cand['miss'] < best['miss']):
            best = cand
    rows.append({
        'id': int(t['id']), 'tf': t['timeframe'], 'dir': t['direction'],
        'entry': t['entry_price'], 'best_off_h': best['off'] if best else None,
        'contained': best['contained'] if best else False,
        'miss_$': round(best['miss'], 3) if best else None,
        'bar_lo': best['lo'] if best else None, 'bar_hi': best['hi'] if best else None,
        'utc': str(best['ts_utc']) if best else None,
        'outcome': t['outcome'],
    })

res = pd.DataFrame(rows)
pd.set_option('display.width', 200, 'display.max_columns', 20)
print(res.to_string(index=False))
print()
n = len(res)
print(f"Contained (entry inside mapped bar): {res['contained'].sum()}/{n}")
print(f"Offset chosen — 1h (BST): {(res['best_off_h']==1).sum()} | 0h (GMT): {(res['best_off_h']==0).sum()}")
print(f"Max miss among non-contained: ${res.loc[~res['contained'],'miss_$'].max() if (~res['contained']).any() else 0}")
# DST expectation: BST after 2026-03-29
trades['dt'] = pd.to_datetime(trades['entry_local'])
bst_expected = trades['dt'] >= pd.Timestamp('2026-03-29')
print(f"\nDST hypothesis (London): {bst_expected.sum()} trades BST / {(~bst_expected).sum()} GMT")
res.to_csv(ROOT / 'analysis' / 'real_trades' / 'phase0' / 'pin_report.csv', index=False)
print("Saved pin_report.csv")
