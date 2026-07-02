"""Diagnose WHICH v2 filter over-rejects the user's takes (recall = 7% is broken).

Leave-one-IN: start from base geometry (all new filters OFF) and turn ON exactly one.
Leave-one-OUT: start from full v2 and turn OFF exactly one.
Reports recall (keep takes) + skip-reject for each, over the review window.
"""
import sys, csv
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params  # noqa: E402

REVIEW_CSV = ROOT / 'analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv'
WIN_START, WIN_END = '2026-05-11', '2026-06-09'

df = pd.read_csv(ROOT / 'data/cache/oanda_gold_1y_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')

# labels keyed by (entry_time, level_price rounded) to avoid duplicate-time collisions
labels = {}
with open(REVIEW_CSV, newline='') as fh:
    rdr = csv.reader(fh); h = next(rdr)
    ti, di, li = h.index('entry_time'), h.index('decision'), h.index('level_price')
    for row in rdr:
        if len(row) <= max(ti, di, li):
            continue
        labels[(row[ti][:16], round(float(row[li]), 1))] = row[di].strip()
n_take = sum(1 for v in labels.values() if v == 'take')
n_skip = sum(1 for v in labels.values() if v == 'skip')


def etime(ts):
    return pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M')


def score(p):
    sus = generate_setups_v2(df, p, True)
    keys = {(etime(s.entry_time), round(s.level_price, 1)) for s in sus
            if WIN_START <= etime(s.entry_time)[:10] <= WIN_END}
    kt = sum(1 for k, d in labels.items() if d == 'take' and k in keys)
    rs = sum(1 for k, d in labels.items() if d == 'skip' and k not in keys)
    n_win = len([1 for s in sus if WIN_START <= etime(s.entry_time)[:10] <= WIN_END])
    return n_win, kt / n_take, rs / n_skip


ALL_OFF = dict(enforce_significance=False, enforce_opposing=False, enforce_false_bo=False,
               enforce_session=False, req_momentum=False, RR_FLOOR=0.0, MAX_MOVE_PCT=0.015)


def disc(rc, sr):
    """discrimination: skip-rej gained per recall lost (vs base 93%/13%). >1 = separates."""
    lose = max(0.93 - rc, 1e-9); gain = max(sr - 0.13, 0.0)
    return gain / lose


print(f"labels: {n_take} take / {n_skip} skip (keyed by time+level)\n")
n, rc0, sr0 = score(ZTTV2Params(**ALL_OFF))
print(f"{'BASE geometry (all filters OFF)':46s}  n={n:3d}  recall={rc0:4.0%}  skip-rej={sr0:4.0%}")

print("\nLEAVE-ONE-IN (base + one filter)  [disc>1 = separates takes from skips]:")
for name, over in [
    ('+ opposing-level cap + RRfloor1.0 (S1b/E2)', dict(enforce_opposing=True, RR_FLOOR=1.0)),
    ('+ opposing-level cap + RRfloor1.5',          dict(enforce_opposing=True, RR_FLOOR=1.5)),
    ('+ significance pivot (S1a)', dict(enforce_significance=True)),
    ('+ momentum (S2)',     dict(req_momentum=True)),
    ('+ false-bo (S3)',     dict(enforce_false_bo=True)),
    ('+ session (S4)',      dict(enforce_session=True)),
]:
    n, rc, sr = score(ZTTV2Params(**{**ALL_OFF, **over}))
    print(f"  {name:44s}  n={n:3d}  recall={rc:4.0%}  skip-rej={sr:4.0%}  disc={disc(rc,sr):4.1f}")

print("\nCANDIDATE v2 (opposing + false-bo + session, RRfloor grid; no pivot-sig, no momentum):")
for floor in (0.0, 1.0, 1.5):
    cfg = dict(ALL_OFF); cfg.update(enforce_opposing=True, enforce_false_bo=True,
                                    enforce_session=True, RR_FLOOR=floor)
    n, rc, sr = score(ZTTV2Params(**cfg))
    print(f"  {'RRfloor='+str(floor):44s}  n={n:3d}  recall={rc:4.0%}  skip-rej={sr:4.0%}  disc={disc(rc,sr):4.1f}")
