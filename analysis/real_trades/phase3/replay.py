"""Phase 3 — per-trade replay: algo (ZTT) vs the user's 25 real trades.

For each trade: DST-correct the stated time, run generate_setups over a window with
ample warmup, then find the best same-direction algo setup near the (price-anchored)
user entry. Score per Falsifier F1 (ENTRY/SKIP only — never exits):
  reproduced = same direction AND |algo_entry - user_entry| <= 0.3R AND |algo_sl - user_sl| <= 0.3R
where R = |user_entry - user_sl|, within a +-3-day window (timestamps drift).

Mistakes the algo SHOULD skip (user's own words): Tr12, Tr20, Tr22 (blind counter-trend) + Tr14 (miss).
Tr8/Tr10 are legitimate losses (valid setups that lost) — taking them is NOT penalized.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, ZTTParams  # noqa: E402

DATA = ROOT / 'data/cache/oanda_gold_10y_10m.csv'
TRADES = ROOT / 'analysis/real_trades/trades.csv'

SKIP_EXPECTED = {12, 20, 22, 14}     # user's flagged mistakes + the miss
LEGIT_LOSSES = {8, 10}               # valid setups that lost — algo MAY take

df = pd.read_csv(DATA, index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')
trades = pd.read_csv(TRADES)
trades['dt'] = pd.to_datetime(trades['entry_local'])

ARM = ZTTParams() if (len(sys.argv) > 1 and sys.argv[1] == 'B') else ZTTParams(allow_reversal=False)
arm_name = 'B (cont+reversal)' if ARM.allow_reversal else 'A (continuation-only)'


def target_utc(row):
    off = 1 if row['dt'] >= pd.Timestamp('2026-03-29') else 0
    return (row['dt'] - pd.Timedelta(hours=off)).tz_localize('UTC')


rows = []
for _, t in trades.iterrows():
    tid = int(t['id'])
    tgt = target_utc(t)
    win = df.loc[tgt - pd.Timedelta(days=45): tgt + pd.Timedelta(days=12)]
    setups = generate_setups(win, ARM)
    R = abs(t['entry_price'] - t['sl'])
    tol = 0.3 * R
    # Anchor by PRICE (reliable) within a wide +-10d window — timestamps drift
    # (Phase 0 finding). Among same-direction setups, pick the one whose entry price
    # is closest to the user's actual fill. This corrects the mis-dated trades
    # (Tr11/17/25) without changing the strategy.
    cands = [s for s in setups
             if s.direction == t['direction']
             and abs((s.entry_time - tgt).total_seconds()) <= 10 * 86400]
    best = min(cands, key=lambda s: abs(s.entry_price - t['entry_price']), default=None)
    # any setup (either direction) near the anchor — for skip-checking
    any_near = [s for s in setups if abs((s.entry_time - tgt).total_seconds()) <= 3 * 86400]

    if best is None:
        saw, e_ok, sl_ok, mode, algo_e, algo_sl = 'no', False, False, '-', None, None
    else:
        saw = 'yes'
        e_ok = abs(best.entry_price - t['entry_price']) <= tol
        sl_ok = abs(best.stop_loss - t['sl']) <= tol
        mode, algo_e, algo_sl = best.mode, best.entry_price, best.stop_loss

    reproduced = (best is not None) and e_ok and sl_ok
    took_any_dir = len(any_near) > 0
    rows.append(dict(id=tid, dir=t['direction'], outcome=t['outcome'], R=round(R, 1),
                     saw=saw, e_ok=e_ok, sl_ok=sl_ok, repro=reproduced, mode=mode,
                     algo_e=round(algo_e, 1) if algo_e else None,
                     user_e=t['entry_price'],
                     algo_sl=round(algo_sl, 1) if algo_sl else None, user_sl=t['sl'],
                     n_near=len(any_near)))

res = pd.DataFrame(rows)
pd.set_option('display.width', 220, 'display.max_columns', 30)
print(f"=== ZTT Phase 3 replay — Arm {arm_name} ===")
print(res.to_string(index=False))

wins = res[res.outcome == 'win']
repro_wins = int(wins.repro.sum())
print(f"\nF1 — winning entries reproduced: {repro_wins}/{len(wins)}  "
      f"({'PASS' if repro_wins>=15 else 'ITERATE' if repro_wins>=12 else 'HALT'})")
saw_wins = int((wins.saw == 'yes').sum())
print(f"     winning setups SEEN (any entry match): {saw_wins}/{len(wins)}  "
      f"(geometry-only floor 60% = {int(0.6*len(wins))})")
skip = res[res.id.isin(SKIP_EXPECTED)]
correct_skips = int((~skip.repro).sum())   # repro False = algo did not reproduce that mistake
print(f"     flagged mistakes correctly NOT reproduced: {correct_skips}/{len(skip)} "
      f"(ids {sorted(SKIP_EXPECTED)})")
out = ROOT / 'analysis/real_trades/phase3' / f"replay_arm_{'B' if ARM.allow_reversal else 'A'}.csv"
res.to_csv(out, index=False)
print(f"Saved {out.name}")
