"""Phase 4 closing tests — formally close mechanical break-retest Gold.

(1) Long-only base-gated 10Y  — shorts may bleed in a decade-long bull (Gold arbiter).
(2) Efficiency-Ratio regime gate — ER(20d)>=0.30 = trending, frozen threshold, one shot
    (Regime arbiter). Pass bars PRE-REGISTERED, expect failure, brings closure.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, ZTTParams  # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST  # noqa: E402

df = pd.read_csv(ROOT / 'data/cache/oanda_gold_10y_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
HIGH, LOW, CLOSE = df['High'].values, df['Low'].values, df['Close'].values
HOURS = df.index.hour.values
RISK, START_EQ, MAX_HOLD = 0.01, 10000.0, 144

# ER(20d) on 10m: 20 trading days = 2880 bars
W = 2880
diff_abs = pd.Series(CLOSE).diff().abs()
er = (pd.Series(CLOSE).diff(W).abs() / diff_abs.rolling(W).sum()).values


def simulate(setups):
    setups = sorted(setups, key=lambda s: s.entry_index)
    eq = START_EQ; curve = [eq]; nf = -1; w = l = 0; gw = gl = 0.0
    for s in setups:
        ei = s.entry_index
        if ei <= nf:
            continue
        owc = COST.fill_cost_one_way(int(HOURS[ei]))
        entry = s.entry_price + owc if s.direction == 'long' else s.entry_price - owc
        rd = abs(entry - s.stop_loss)
        if rd <= 0:
            continue
        size = (eq * RISK) / rd
        xp = None; end = min(len(df), ei + 1 + MAX_HOLD); xj = end - 1
        for j in range(ei + 1, end):
            if s.direction == 'long':
                if LOW[j] <= s.stop_loss: xp = s.stop_loss; xj = j; break
                if HIGH[j] >= s.take_profit: xp = s.take_profit; xj = j; break
            else:
                if HIGH[j] >= s.stop_loss: xp = s.stop_loss; xj = j; break
                if LOW[j] <= s.take_profit: xp = s.take_profit; xj = j; break
        if xp is None: xp = CLOSE[xj]
        oxc = COST.fill_cost_one_way(int(HOURS[xj]))
        pnl = size * ((xp - oxc) - entry) if s.direction == 'long' else size * (entry - (xp + oxc))
        eq += pnl; curve.append(eq); nf = xj
        if pnl >= 0: w += 1; gw += pnl
        else: l += 1; gl += -pnl
    n = w + l
    if n == 0: return dict(n=0)
    c = np.array(curve); pk = np.maximum.accumulate(c)
    return dict(n=n, wr=100 * w / n, pf=(gw / gl if gl > 0 else float('inf')),
                pnl=eq - START_EQ, dd=float(np.max((pk - c) / pk)) * 100)


base = generate_setups(df, ZTTParams(req_momentum=False, req_fvg=False, req_sweep=False), apply_gates=True)
print(f"base-gated 10Y setups: {len(base)}")

# Test 1 — long-only
longs = [s for s in base if s.direction == 'long']
r = simulate(longs)
print(f"\n[TEST 1] LONG-ONLY base-gated 10Y: n={r['n']} WR{r['wr']:.0f}% PF {r['pf']:.2f} "
      f"PnL {r['pnl']:.0f} DD {r['dd']:.0f}%  -> {'PASS' if r['pf']>=1.3 else 'FAIL'} (bar PF>=1.3)")

# Test 2 — ER regime gate (frozen 0.30)
trend = [s for s in base if not np.isnan(er[s.entry_index]) and er[s.entry_index] >= 0.30]
rng = [s for s in base if not np.isnan(er[s.entry_index]) and er[s.entry_index] < 0.30]
rt, rr = simulate(trend), simulate(rng)
print(f"\n[TEST 2] ER(20d)>=0.30 REGIME GATE (frozen):")
print(f"  trending: n={rt.get('n',0)} PF {rt.get('pf',0):.2f} PnL {rt.get('pnl',0):.0f} DD {rt.get('dd',0):.0f}%")
print(f"  ranging : n={rr.get('n',0)} PF {rr.get('pf',0):.2f} PnL {rr.get('pnl',0):.0f}")
ok = rt.get('n',0) >= 200 and rt.get('pf',0) >= 1.5
print(f"  -> {'PASS' if ok else 'FAIL'} (bar: trending PF>=1.5 AND n>=200)")
