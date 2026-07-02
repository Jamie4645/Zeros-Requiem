"""ZTT v2 validation — replication (F1/F2) + grid backtest (F6).

1. REPLICATION: regenerate the base-config population over the review window, match
   to the 60 human labels, then ask which the v2 filter KEEPS. Reports recall (keep
   the user's takes), skip-rejection (drop the user's skips), precision.
2. GRID BACKTEST: run v2 over full 1y (and 10y if present) across the
   {MAX_MOVE_PCT x RR_FLOOR} grid at realistic session-gated cost. NEVER hand-pick —
   the whole grid is printed.

Run: .\venv\Scripts\python.exe analysis/real_trades/tv_review/v2_validate.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, ZTTParams          # noqa: E402
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params  # noqa: E402
from src.regimes.ztt_costs import DEFAULT_COST as COST          # noqa: E402

REVIEW_CSV = ROOT / 'analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv'
WIN_START, WIN_END = '2026-05-11', '2026-06-09'
MAX_HOLD = 144
RISK, START_EQ = 0.01, 10000.0


def load_data(period):
    f = ROOT / f'data/cache/oanda_gold_{period}_10m.csv'
    if not f.exists():
        return None
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    return df


def etime(ts):
    return pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M')


def simulate(df, setups):
    HIGH, LOW, CLOSE = df['High'].values, df['Low'].values, df['Close'].values
    HOURS = df.index.hour.values
    setups = sorted(setups, key=lambda s: s.entry_index)
    eq = START_EQ; curve = [eq]; next_free = -1
    wins = losses = 0; gross_win = gross_loss = 0.0
    for s in setups:
        ei = s.entry_index
        if ei <= next_free:
            continue
        owc = COST.fill_cost_one_way(int(HOURS[ei]))
        entry = s.entry_price + owc if s.direction == 'long' else s.entry_price - owc
        risk_dist = abs(entry - s.stop_loss)
        if risk_dist <= 0:
            continue
        size = (eq * RISK) / risk_dist
        exit_price = None; end = min(len(df), ei + 1 + MAX_HOLD)
        for j in range(ei + 1, end):
            if s.direction == 'long':
                if LOW[j] <= s.stop_loss:
                    exit_price = s.stop_loss; xj = j; break
                if HIGH[j] >= s.take_profit:
                    exit_price = s.take_profit; xj = j; break
            else:
                if HIGH[j] >= s.stop_loss:
                    exit_price = s.stop_loss; xj = j; break
                if LOW[j] <= s.take_profit:
                    exit_price = s.take_profit; xj = j; break
        if exit_price is None:
            xj = end - 1; exit_price = CLOSE[xj]
        oxc = COST.fill_cost_one_way(int(HOURS[xj]))
        if s.direction == 'long':
            pnl = size * ((exit_price - oxc) - entry)
        else:
            pnl = size * (entry - (exit_price + oxc))
        eq += pnl; curve.append(eq)
        if pnl >= 0:
            wins += 1; gross_win += pnl
        else:
            losses += 1; gross_loss += -pnl
        next_free = xj
    n = wins + losses
    if n == 0:
        return dict(n=0)
    curve = np.array(curve); peak = np.maximum.accumulate(curve)
    maxdd = float(np.max((peak - curve) / peak)) * 100
    pf = gross_win / gross_loss if gross_loss > 0 else float('inf')
    return dict(n=n, wr=100 * wins / n, pf=pf, pnl=eq - START_EQ, dd=maxdd)


# ── 1. REPLICATION ───────────────────────────────────────────────────────
print("=" * 72)
print("1. REPLICATION — does v2 keep the user's TAKES and reject his SKIPS?")
print("=" * 72)
df1 = load_data('1y')
if df1 is None:
    print("  [blocker] data/cache/oanda_gold_1y_10m.csv missing"); sys.exit(1)

import csv
labels = {}
with open(REVIEW_CSV, newline='') as fh:
    rdr = csv.reader(fh)
    header = next(rdr)
    ti, di = header.index('entry_time'), header.index('decision')
    for row in rdr:                       # decision col precedes the notes spill -> safe
        if len(row) <= di:
            continue
        labels[row[ti][:16]] = row[di].strip()
n_take = sum(1 for v in labels.values() if v == 'take')
n_skip = sum(1 for v in labels.values() if v == 'skip')

base = generate_setups(df1, ZTTParams(req_momentum=False, req_fvg=False, req_sweep=False), True)
base_win = [s for s in base if WIN_START <= etime(s.entry_time)[:10] <= WIN_END]
base_keys = {etime(s.entry_time) for s in base_win}
matched = base_keys & set(labels)
print(f"  base-config setups in window: {len(base_win)}  (labels: {len(labels)}; matched by entry_time: {len(matched)})")

v2p = ZTTV2Params(MAX_MOVE_PCT=0.015, RR_FLOOR=1.0)
v2 = generate_setups_v2(df1, v2p, True)
v2_win_keys = {etime(s.entry_time) for s in v2 if WIN_START <= etime(s.entry_time)[:10] <= WIN_END}

kept_take = kept_skip = rej_take = rej_skip = 0
for k, dec in labels.items():
    keep = k in v2_win_keys
    if dec == 'take' and keep:    kept_take += 1
    elif dec == 'take':           rej_take += 1
    elif dec == 'skip' and keep:  kept_skip += 1
    else:                          rej_skip += 1
recall = kept_take / n_take if n_take else 0
skiprej = rej_skip / n_skip if n_skip else 0
prec = kept_take / (kept_take + kept_skip) if (kept_take + kept_skip) else 0
print(f"  takes: kept {kept_take}/{n_take} (recall {recall:.0%})   "
      f"skips: rejected {rej_skip}/{n_skip} (skip-reject {skiprej:.0%})   precision {prec:.0%}")
print(f"  F1 (reject >=80% skips): {'PASS' if skiprej >= 0.80 else 'TRIP'}   "
      f"F2 (keep >=70% takes): {'PASS' if recall >= 0.70 else 'TRIP'}")
print("  NOTE: matching is by entry_time; rows where base didn't reproduce the label "
      "(data window/warmup) count as v2-reject by construction — see matched count above.")

# ── 2. GRID BACKTEST ─────────────────────────────────────────────────────
for period in ('1y', '10y'):
    dfp = load_data(period)
    if dfp is None:
        print(f"\n  [skip] {period} data absent"); continue
    print("\n" + "=" * 72)
    print(f"2. GRID BACKTEST — v2 over {period} 10m Gold, session-gated cost, 1% risk")
    print("=" * 72)
    print(f"  {'cap%':>5s} {'RRfloor':>7s} {'n':>5s} {'WR%':>5s} {'PF':>6s} {'PnL$':>9s} {'DD%':>6s}  verdict")
    for cap in (0.015, 0.020, 0.025):
        for floor in (1.0, 1.5, 2.0):
            setups = generate_setups_v2(dfp, ZTTV2Params(MAX_MOVE_PCT=cap, RR_FLOOR=floor), True)
            r = simulate(dfp, setups)
            if r['n'] == 0:
                print(f"  {cap*100:5.1f} {floor:7.1f}    no trades"); continue
            v = 'PASS' if (r['pf'] >= 1.5 and r['pnl'] > 0 and r['n'] >= 80) else \
                ('KILL' if r['pf'] < 1.2 or r['pnl'] <= 0 else 'marg')
            print(f"  {cap*100:5.1f} {floor:7.1f} {r['n']:5d} {r['wr']:5.1f} {r['pf']:6.2f} "
                  f"{r['pnl']:9.0f} {r['dd']:6.1f}  {v}")
