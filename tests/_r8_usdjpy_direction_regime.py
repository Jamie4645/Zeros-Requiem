"""
Round 8 USDJPY Direction + Regime Analysis (arbiter-forex | 2026-04-20)

Mirror of _r8_gold_direction_regime.py for USDJPY. Rules out short-stream
concentration before any reconsideration of USDJPY live inclusion.

Usage:
    python tests/_r8_usdjpy_direction_regime.py

Output:
    logs/round8/usdjpy_direction_regime_live.log
"""

import sys, warnings, numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.data.fetcher import fetch, detect_asset_class
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval

SYMBOL, INTERVAL, PERIOD, CAPITAL, RISK = "USDJPY=X", "1h", "10y", 10_000.0, 0.01
LOG = Path(__file__).resolve().parent.parent / "logs" / "round8" / "usdjpy_direction_regime_live.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

REGIMES = [
    ("ZIRP",       pd.Timestamp("2016-01-01", tz="UTC"), pd.Timestamp("2022-03-16", tz="UTC")),
    ("Tightening", pd.Timestamp("2022-03-16", tz="UTC"), pd.Timestamp("2024-03-20", tz="UTC")),
    ("Post-hike",  pd.Timestamp("2024-03-20", tz="UTC"), pd.Timestamp("2027-01-01", tz="UTC")),
]

def get_regime(ts):
    if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
    else: ts = ts.astimezone(timezone.utc)
    for name, s, e in REGIMES:
        if s <= ts < e: return name
    return "Unknown"

def stats(trades, label=""):
    if not trades: return dict(label=label, n=0, wr=0, pf=0, exp=0, hold=0)
    pnls = np.array([t.pnl for t in trades])
    wins = pnls[pnls > 0]; loss = pnls[pnls <= 0]
    pf = wins.sum() / abs(loss.sum()) if len(loss) and loss.sum() != 0 else 9999
    wr = (pnls > 0).mean() * 100
    hold = np.mean([t.exit_index - t.entry_index for t in trades if t.exit_index > t.entry_index])
    return dict(label=label, n=len(trades), wr=wr, pf=pf, exp=pnls.mean(), hold=hold)

def row(s):
    if s["n"] == 0: return f"  {s['label']:<28} |   --- |   ---  |  ---  |    ---  |  ---"
    return (f"  {s['label']:<28} | {s['n']:>5} | {s['wr']:>5.1f}% | {s['pf']:>5.2f} |"
            f" {s['exp']:>+8.2f} | {s['hold']:>5.1f}h")

HDR = "  {:<28} | {:>5} | {:>6} | {:>5} | {:>8} | {:>7}".format(
    "Subset", "n", "WR", "PF", "Exp$/tr", "AvgHold")
SEP = "  " + "-" * 68

lines = []
p = lambda s: (lines.append(s), print(s))

p("=" * 72)
p("  ARBITER-FOREX R8 | USDJPY Direction + Regime | LIVE | 2026-04-20")
p("=" * 72)

p('Fetching OANDA USDJPY 10Y...')
df = fetch(SYMBOL, INTERVAL, PERIOD)
p(f'    bars loaded: {len(df)}')

ac = detect_asset_class(SYMBOL)
setups = analyze_sbrs_v2(df, CAPITAL, RISK, asset_class=ac, symbol=SYMBOL)
p(f'    setups: {len(setups)}')
rc = risk_config_for_interval(INTERVAL, RISK, ac, symbol=SYMBOL)
ind = get_sbrs_v2_indicators(df)
res = run_backtest(df, setups, CAPITAL, rc, apply_slippage=True, sbrs_v2_indicators=ind)
p(f'    {res.total_trades} trades WR={res.win_rate:.1f} PF={res.profit_factor:.2f} Sharpe={res.sharpe_ratio:.2f}')
closed = [t for t in res.trades if t.exit_index > 0]
longs  = [t for t in closed if t.direction == "long"]
shorts = [t for t in closed if t.direction == "short"]
for t in closed:
    idx = t.entry_index if t.entry_index < len(df) else len(df)-1
    t._regime = get_regime(df.index[idx])

p('TABLE 1 -- Per-Direction')
p(HDR); p(SEP)
for s in [stats(closed,"ALL"), stats(longs,"LONG"), stats(shorts,"SHORT")]: p(row(s))
sl = stats(longs, "L"); ss = stats(shorts, "S")
if ss["pf"] > 0:
    _wr_gap = sl["wr"] - ss["wr"]
    _pf_ratio = sl["pf"] / ss["pf"]
    p(f"WR gap: {_wr_gap:+.1f}pp  PF ratio: {_pf_ratio:.2f}x")

p('TABLE 2 -- Per-Regime x Per-Direction')
p(HDR); p(SEP)
for rname, _, _ in REGIMES:
    rt = [t for t in closed if t._regime == rname]
    rl = [t for t in rt if t.direction == "long"]
    rs = [t for t in rt if t.direction == "short"]
    for s in [stats(rt,rname+" ALL"), stats(rl,"  "+rname+" LONG"), stats(rs,"  "+rname+" SHORT")]: p(row(s))
    p("")

# Falsifier #5 equivalent for USDJPY: Long PF >= 1.5 AND Short PF >= 1.2
_l_pf = stats(longs,"L")["pf"]; _s_pf = stats(shorts,"S")["pf"]
_verdict = "PASS" if (_l_pf >= 1.5 and _s_pf >= 1.2) else "FAIL"
p(f"Falsifier (Long PF>=1.5 & Short PF>=1.2): L={_l_pf:.2f} S={_s_pf:.2f} -> {_verdict}")

with open(LOG, "w", encoding="utf-8") as f: f.write("\n".join(lines))
print(f"Written to {LOG}")
