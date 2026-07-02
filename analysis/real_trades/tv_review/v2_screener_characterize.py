"""Characterize the VALIDATED ZTT v2 screener config (defaults: base geometry +
false-bo + session, %-cap TP, no autonomous selection filter).

(1) replication on the review window — recall / skip-reject (expect ~93% / ~27%).
(2) standalone MECHANICAL backtest over 1y + 10y across the TP-cap grid, realistic cost.
    NB: the mechanical strategy is NOT the deliverable — the user's selection is. This
    just characterizes what the high-recall population looks like un-judged.
"""
import sys, csv
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params  # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST          # noqa: E402

REVIEW = ROOT / 'analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv'
WS, WE = '2026-05-11', '2026-06-09'
MAX_HOLD, RISK, EQ0 = 144, 0.01, 10000.0


def load(period):
    f = ROOT / f'data/cache/oanda_gold_{period}_10m.csv'
    if not f.exists():
        return None
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    return df


def et(ts):
    return pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M')


def simulate(df, setups):
    H, L, C = df['High'].values, df['Low'].values, df['Close'].values
    HR = df.index.hour.values
    eq = EQ0; curve = [eq]; nf = -1; w = l = 0; gw = gl = 0.0
    for s in sorted(setups, key=lambda x: x.entry_index):
        ei = s.entry_index
        if ei <= nf:
            continue
        owc = COST.fill_cost_one_way(int(HR[ei]))
        entry = s.entry_price + owc if s.direction == 'long' else s.entry_price - owc
        rd = abs(entry - s.stop_loss)
        if rd <= 0:
            continue
        size = eq * RISK / rd; xp = None; end = min(len(df), ei + 1 + MAX_HOLD)
        for j in range(ei + 1, end):
            if s.direction == 'long':
                if L[j] <= s.stop_loss: xp = s.stop_loss; xj = j; break
                if H[j] >= s.take_profit: xp = s.take_profit; xj = j; break
            else:
                if H[j] >= s.stop_loss: xp = s.stop_loss; xj = j; break
                if L[j] <= s.take_profit: xp = s.take_profit; xj = j; break
        if xp is None: xj = end - 1; xp = C[xj]
        oxc = COST.fill_cost_one_way(int(HR[xj]))
        pnl = size * ((xp - oxc) - entry) if s.direction == 'long' else size * (entry - (xp + oxc))
        eq += pnl; curve.append(eq)
        if pnl >= 0: w += 1; gw += pnl
        else: l += 1; gl += -pnl
        nf = xj
    n = w + l
    if n == 0:
        return dict(n=0)
    cu = np.array(curve); pk = np.maximum.accumulate(cu)
    return dict(n=n, wr=100 * w / n, pf=(gw / gl if gl else float('inf')),
                pnl=eq - EQ0, dd=float(np.max((pk - cu) / pk)) * 100)


# (1) replication
labels = {}
with open(REVIEW, newline='') as fh:
    rdr = csv.reader(fh); h = next(rdr)
    ti, di, li = h.index('entry_time'), h.index('decision'), h.index('level_price')
    for row in rdr:
        if len(row) > max(ti, di, li):
            labels[(row[ti][:16], round(float(row[li]), 1))] = row[di].strip()
nt = sum(1 for v in labels.values() if v == 'take'); ns = sum(1 for v in labels.values() if v == 'skip')
df1 = load('1y')
scr = generate_setups_v2(df1, ZTTV2Params(), True)
keys = {(et(s.entry_time), round(s.level_price, 1)) for s in scr if WS <= et(s.entry_time)[:10] <= WE}
kt = sum(1 for k, d in labels.items() if d == 'take' and k in keys)
rs = sum(1 for k, d in labels.items() if d == 'skip' and k not in keys)
print("=== ZTT v2 SCREENER (validated default config) ===")
print(f"replication on review window: recall {kt}/{nt}={kt/nt:.0%}  skip-reject {rs}/{ns}={rs/ns:.0%}")
print("(screener = high recall by design; the user is the selection layer)\n")

# (2) standalone mechanical backtest, cap grid
for period in ('1y', '10y'):
    dfp = load(period)
    if dfp is None:
        print(f"[skip] {period} absent"); continue
    print(f"--- mechanical backtest, {period} 10m Gold, session-gated cost, 1% risk ---")
    print(f"  {'cap%':>5s} {'n':>5s} {'WR%':>5s} {'PF':>6s} {'PnL$':>9s} {'DD%':>6s}")
    for cap in (0.015, 0.020, 0.025):
        r = simulate(dfp, generate_setups_v2(dfp, ZTTV2Params(MAX_MOVE_PCT=cap), True))
        if r['n'] == 0:
            print(f"  {cap*100:5.1f}   no trades"); continue
        print(f"  {cap*100:5.1f} {r['n']:5d} {r['wr']:5.1f} {r['pf']:6.2f} {r['pnl']:9.0f} {r['dd']:6.1f}")
