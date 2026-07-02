"""Phase 0 — fetch native M10 Gold from OANDA and cache to CSV.

Usage:
    python analysis/real_trades/phase0/fetch_gold_10m.py 1y
    python analysis/real_trades/phase0/fetch_gold_10m.py 10y
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.data.oanda_fetcher import fetch_oanda  # noqa: E402

period = sys.argv[1] if len(sys.argv) > 1 else '1y'
out = ROOT / 'data' / 'cache' / f'oanda_gold_{period}_10m.csv'

print(f"Fetching XAU_USD M10 for period={period} ...")
df = fetch_oanda('GC=F', interval='10m', period=period)
df.to_csv(out)
print(f"Saved {len(df):,} bars -> {out}")
print(f"Range: {df.index[0]}  ->  {df.index[-1]}")
# Gap / sanity report
import pandas as pd  # noqa: E402
deltas = df.index.to_series().diff().dropna()
print(f"Median bar spacing: {deltas.median()}")
print(f"Bars with >1h gap (weekend/daily breaks): {(deltas > pd.Timedelta('1h')).sum()}")
print(f"Expected ~{int((df.index[-1]-df.index[0]).days * 144 * 5/7):,} bars if continuous 24x5")
