"""Phase 1 prep — measure the geometry of the 25 trades to set PRINCIPLED defaults.

Descriptive only (informs sane defaults; not curve-fitting). For each trade we
price-anchor the entry bar (timestamps drift — see Phase 0), then report:
  - ATR(14) at entry, SL distance in ATR, realized R:R
  - WMA(144)/SMMA(5) alignment with trade direction (MA-confluence rate)
  - price vs WMA(144) (trend-baseline side)
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.indicators.technical import wma, smma, atr  # noqa: E402

df = pd.read_csv(ROOT / 'data/cache/oanda_gold_10y_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
df['ATR'] = atr(df, 14)
df['WMA144'] = wma(df['Close'], 144)
df['SMMA5'] = smma(df['Close'], 5)

t = pd.read_csv(ROOT / 'analysis/real_trades/trades.csv')
t['dt'] = pd.to_datetime(t['entry_local'])
t['off'] = t['dt'].apply(lambda d: 1 if d >= pd.Timestamp('2026-03-29') else 0)


def locate(row):
    """Price-anchor entry bar within +-3d of DST-corrected stated time."""
    target = (row['dt'] - pd.Timedelta(hours=row['off'])).tz_localize('UTC')
    win = df.loc[target - pd.Timedelta(days=3): target + pd.Timedelta(days=3)]
    hit = win[(win.Low <= row['entry_price']) & (win.High >= row['entry_price'])]
    if len(hit):
        # nearest to stated time among containing bars
        return hit.index[(hit.index - target).to_series().abs().values.argmin()]
    return None


rows = []
for _, r in t.iterrows():
    idx = locate(r)
    if idx is None:
        rows.append({'id': int(r['id']), 'note': 'NOT FOUND'}); continue
    bar = df.loc[idx]
    sl_dist = abs(r['entry_price'] - r['sl'])
    tp_dist = abs(r['tp'] - r['entry_price'])
    smma_v, wma_v = bar['SMMA5'], bar['WMA144']
    bull_ma = smma_v > wma_v
    want_bull = (r['direction'] == 'long')
    rows.append({
        'id': int(r['id']), 'dir': r['direction'], 'tf': r['timeframe'],
        'atr': round(bar['ATR'], 2),
        'sl_atr': round(sl_dist / bar['ATR'], 2) if bar['ATR'] else None,
        'rr': round(tp_dist / sl_dist, 2),
        'ma_aligned': bool(bull_ma == want_bull),
        'px_vs_wma': 'above' if r['entry_price'] > wma_v else 'below',
        'px_side_ok': bool((r['entry_price'] > wma_v) == want_bull),
        'outcome': r['outcome'],
    })

res = pd.DataFrame(rows)
pd.set_option('display.width', 200, 'display.max_columns', 20)
print(res.to_string(index=False))
ok = res[res.get('note').isna()] if 'note' in res else res
print(f"\nLocated: {len(ok)}/25")
print(f"SL distance in ATR — median {ok['sl_atr'].median():.2f}, range {ok['sl_atr'].min():.2f}-{ok['sl_atr'].max():.2f}")
print(f"Realized R:R — median {ok['rr'].median():.2f}, range {ok['rr'].min():.2f}-{ok['rr'].max():.2f}")
print(f"MA(SMMA5/WMA144) aligned with direction: {ok['ma_aligned'].sum()}/{len(ok)} ({100*ok['ma_aligned'].mean():.0f}%)")
print(f"Price on trend-baseline side (px vs WMA144): {ok['px_side_ok'].sum()}/{len(ok)} ({100*ok['px_side_ok'].mean():.0f}%)")
