"""Falsifier F3 — re-exit transfer test for ZTT v2 redesign.

Does the +10.29R edge in the 30 human-TAKE setups survive when the wide fixed-3R
take-profit is replaced by a tighter %-capped TP, once win-rate floats by walking
REAL 10m price?

Phantom-safe walk replicating analysis/real_trades/phase4/backtest_ztt.py:
  MAX_HOLD bars, exit only when [low,high] trades to level, SL wins adverse ties,
  timeout -> close of last in-window bar.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(r"C:\Users\jamie\OneDrive\Documents\Jamie VS Code\Git\Zeros Requiem")
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_costs import DEFAULT_COST as COST  # noqa: E402

MAX_HOLD = 144  # matches phase4 harness

TAKES_CSV = ROOT / "analysis/real_trades/tv_review/ztt_review_2026-05-11_to_2026-06-09_base.csv"
PRICE_CSV = ROOT / "data/cache/oanda_gold_10y_10m.csv"

# ---- load price ----
px = pd.read_csv(PRICE_CSV, parse_dates=["Datetime"])
if px["Datetime"].dt.tz is None:
    px["Datetime"] = px["Datetime"].dt.tz_localize("UTC")
else:
    px["Datetime"] = px["Datetime"].dt.tz_convert("UTC")
px = px.sort_values("Datetime").reset_index(drop=True)
# index by minute for fast match
ts_to_idx = {t: i for i, t in enumerate(px["Datetime"])}
HIGH = px["High"].values
LOW = px["Low"].values
CLOSE = px["Close"].values
HOUR = px["Datetime"].dt.hour.values
DT = px["Datetime"].values

# ---- load takes ----
# Two rows (n=54,55) have an unescaped delimiter producing a 17th overflow field
# in the trailing 'notes' column. We only need fields 0..13 (n..decision), so we
# parse with the csv module and keep the leading 16 columns.
import csv as _csv
with open(TAKES_CSV, encoding="utf-8") as fh:
    _rows = list(_csv.reader(fh))
_hdr = _rows[0]
_data = [r[: len(_hdr)] for r in _rows[1:] if r]
df = pd.DataFrame(_data, columns=_hdr)
takes = df[df["decision"] == "take"].copy()
print(f"Loaded {len(takes)} take rows (expected 30)")

CAPS = {"cap_1.5%": 0.015, "cap_2.0%": 0.020, "cap_2.5%": 0.025}


def round_trip_cost(entry_hour, exit_hour):
    return COST.fill_cost_one_way(int(entry_hour)) + COST.fill_cost_one_way(int(exit_hour))


def walk(entry_idx, direction, entry, sl, tp):
    """Phantom-safe walk. Returns (exit_price, exit_idx, kind) kind in win/loss/timeout."""
    end = min(len(px), entry_idx + 1 + MAX_HOLD)
    for j in range(entry_idx + 1, end):
        lo, hi = LOW[j], HIGH[j]
        if direction == "long":
            sl_hit = lo <= sl <= hi or lo <= sl  # SL is below entry: price trades down to it
            tp_hit = lo <= tp <= hi or hi >= tp
            # use the inside-[low,high] convention strictly:
            sl_in = lo <= sl <= hi
            tp_in = lo <= tp <= hi
            if sl_in and tp_in:
                return sl, j, "loss"
            if sl_in:
                return sl, j, "loss"
            if tp_in:
                return tp, j, "win"
        else:
            sl_in = lo <= sl <= hi
            tp_in = lo <= tp <= hi
            if sl_in and tp_in:
                return sl, j, "loss"
            if sl_in:
                return sl, j, "loss"
            if tp_in:
                return tp, j, "win"
    xj = end - 1
    return CLOSE[xj], xj, "timeout"


def run_scenario(name, tp_mode):
    rows = []
    matched = 0
    unmatched = []
    for _, r in takes.iterrows():
        n = int(r["n"])
        et = pd.Timestamp(r["entry_time"], tz="UTC")
        direction = r["direction"]
        entry = float(r["entry_price"])
        sl = float(r["stop_loss"])
        sl_dist = abs(entry - sl)
        if sl_dist <= 0:
            continue
        # TP per scenario
        sign = 1 if direction == "long" else -1
        if tp_mode == "3R":
            tp = entry + sign * 3.0 * sl_dist
        else:
            cap = CAPS[tp_mode]
            tp = entry + sign * cap * entry
        # match entry bar
        if et not in ts_to_idx:
            unmatched.append((n, str(et)))
            continue
        ei = ts_to_idx[et]
        matched += 1
        exit_price, xj, kind = walk(ei, direction, entry, sl, tp)
        gross_R = sign * (exit_price - entry) / sl_dist
        cost = round_trip_cost(HOUR[ei], HOUR[xj])
        cost_R = cost / sl_dist
        net_R = gross_R - cost_R
        rows.append(dict(n=n, direction=direction, kind=kind,
                         gross_R=gross_R, net_R=net_R, cost_R=cost_R))
    return pd.DataFrame(rows), matched, unmatched


# ---- run all scenarios ----
scenarios = ["3R", "cap_1.5%", "cap_2.0%", "cap_2.5%"]
results = {}
for sc in scenarios:
    res, matched, unmatched = run_scenario(sc, sc)
    results[sc] = res
    if sc == "3R" and unmatched:
        print(f"UNMATCHED entry_times ({len(unmatched)}): {unmatched}")
    if sc == "3R":
        print(f"Matched {matched}/{len(takes)} take rows to 10m bars\n")

# ---- sanity check on control gross vs CSV realized_r ----
csv_realized_sum = takes["realized_r"].astype(float).sum()
ctrl = results["3R"]
ctrl_gross_sum = ctrl["gross_R"].sum()
ctrl_net_sum = ctrl["net_R"].sum()
print("=== SANITY CHECK (3R control) ===")
print(f"CSV realized_r sum (reference)      : {csv_realized_sum:+.2f}R")
print(f"Walk 3R_control GROSS sum            : {ctrl_gross_sum:+.2f}R")
print(f"Walk 3R_control NET sum (after cost) : {ctrl_net_sum:+.2f}R")
print(f"Gap (walk gross - CSV)               : {ctrl_gross_sum - csv_realized_sum:+.2f}R")
print()

# ---- per-scenario report ----
def metrics(res, label):
    res = res.sort_values("net_R")
    net_sum = res["net_R"].sum()
    mean_net = res["net_R"].mean()
    n = len(res)
    wins = (res["kind"] == "win").sum()
    losses = (res["kind"] == "loss").sum()
    tos = (res["kind"] == "timeout").sum()
    wr = wins / n
    top2_removed = res["net_R"].iloc[:-2].sum()  # drop the 2 largest net_R
    long_sum = res[res["direction"] == "long"]["net_R"].sum()
    short_sum = res[res["direction"] == "short"]["net_R"].sum()
    return dict(label=label, n=n, net_sum=net_sum, mean_net=mean_net, wr=wr,
                wins=wins, losses=losses, tos=tos, top2_removed=top2_removed,
                long_sum=long_sum, short_sum=short_sum)


print("=== SCENARIO TABLE (30 takes, net R after round-trip cost) ===")
hdr = f"{'scenario':12s} {'netR':>8s} {'meanR':>7s} {'WR':>6s} {'W/L/TO':>9s} {'top2off':>8s} {'longR':>8s} {'shortR':>8s}"
print(hdr)
all_m = {}
for sc in scenarios:
    label = "3R_control" if sc == "3R" else sc
    m = metrics(results[sc], label)
    all_m[sc] = m
    print(f"{m['label']:12s} {m['net_sum']:+8.2f} {m['mean_net']:+7.3f} {m['wr']*100:5.1f}% "
          f"{m['wins']:>2d}/{m['losses']:>2d}/{m['tos']:<2d} {m['top2_removed']:+8.2f} "
          f"{m['long_sum']:+8.2f} {m['short_sum']:+8.2f}")

# ---- F3 verdict ----
print("\n=== F3 DECISION ===")
cap_scenarios = ["cap_1.5%", "cap_2.0%", "cap_2.5%"]
best = max(cap_scenarios, key=lambda s: all_m[s]["net_sum"])
bm = all_m[best]
print(f"Best %-cap scenario: {best}  netR={bm['net_sum']:+.2f}  meanR={bm['mean_net']:+.3f}  top2off={bm['top2_removed']:+.2f}")
cond1 = bm["net_sum"] >= 5.0
cond2 = bm["mean_net"] >= 0.15
cond3 = bm["top2_removed"] > 0
print(f"  netR >= +5.0R      : {bm['net_sum']:+.2f}  -> {'PASS' if cond1 else 'FAIL'}")
print(f"  meanR >= +0.15R    : {bm['mean_net']:+.3f} -> {'PASS' if cond2 else 'FAIL'}")
print(f"  top2-removed > 0   : {bm['top2_removed']:+.2f}  -> {'PASS' if cond3 else 'FAIL'}")
verdict = "F3 PASS (edge transfers)" if (cond1 and cond2 and cond3) else "F3 TRIPS (edge does NOT transfer)"
print(f"\nVERDICT: {verdict}")
