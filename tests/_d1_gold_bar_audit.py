"""
Round 6 D1 — Gold OANDA vs Yahoo bar-count + range audit.

Purpose: explain the 737 OANDA trade count vs the legacy 2,252 Yahoo-era
baseline. Hypothesis (arbiter-gold 2026-04-17): OANDA bars are mid-price
spread-adjusted and have systematically narrower High-Low ranges than
Yahoo's COMEX settlement feed, suppressing swing-point detection and
therefore SBRS 2.0 setup generation.

Method (diagnostic only — no code changes):
  1. Load cached OANDA Gold 10Y 1H from data/cache/oanda_gold_10y_1h.csv
  2. Fetch Yahoo GC=F 1H (max 2Y per Yahoo limitation)
  3. Restrict both to the 2Y overlap window
  4. Compute:
     (a) bar counts per month
     (b) mean (High-Low)/Close per bar (normalized range)
     (c) swing-point count per 1000 bars (SWING_LOOKBACK=20, SWING_WINDOW=3)
  5. Print deltas — no file writes from this script.

One-off diagnostic. Not part of the pytest suite.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from src.data.fetcher import fetch as yahoo_fetch

OANDA_CACHE = Path(__file__).resolve().parent.parent / "data" / "cache" / "oanda_gold_10y_1h.csv"


def load_oanda_10y() -> pd.DataFrame:
    df = pd.read_csv(OANDA_CACHE, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def count_swings(df: pd.DataFrame, lookback: int = 20, window: int = 3) -> tuple[int, int]:
    """Count swing highs and swing lows using the SBRS 2.0 convention.

    A swing high at index i is: High[i] == max(High[i-window : i+window+1])
    Only counts if the bar has `lookback` prior bars available.
    """
    highs = df["High"].values
    lows = df["Low"].values
    n = len(df)
    swing_highs = 0
    swing_lows = 0
    for i in range(max(lookback, window), n - window):
        window_hi = highs[i - window : i + window + 1]
        window_lo = lows[i - window : i + window + 1]
        if highs[i] == window_hi.max() and highs[i] > highs[i - 1]:
            swing_highs += 1
        if lows[i] == window_lo.min() and lows[i] < lows[i - 1]:
            swing_lows += 1
    return swing_highs, swing_lows


def monthly_bar_count(df: pd.DataFrame) -> pd.Series:
    return df.resample("MS").size()


def mean_normalized_range(df: pd.DataFrame) -> float:
    rng = (df["High"] - df["Low"]) / df["Close"]
    return float(rng.mean())


def main():
    print("[D1] Loading OANDA Gold 10Y cache...")
    oanda = load_oanda_10y()
    print(f"[D1] OANDA: {len(oanda)} bars, {oanda.index[0]} -> {oanda.index[-1]}")

    print("\n[D1] Fetching Yahoo GC=F 2Y 1H...")
    try:
        yahoo = yahoo_fetch("GC=F", "1h", "2y")
    except Exception as e:
        print(f"[D1] Yahoo fetch failed: {e}")
        print("[D1] Falling back to 1Y.")
        try:
            yahoo = yahoo_fetch("GC=F", "1h", "1y")
        except Exception as e2:
            print(f"[D1] Yahoo 1Y also failed: {e2}")
            return
    if yahoo.index.tz is None:
        yahoo.index = yahoo.index.tz_localize("UTC")
    else:
        yahoo.index = yahoo.index.tz_convert("UTC")
    print(f"[D1] Yahoo: {len(yahoo)} bars, {yahoo.index[0]} -> {yahoo.index[-1]}")

    # Overlap window
    overlap_start = max(oanda.index[0], yahoo.index[0])
    overlap_end = min(oanda.index[-1], yahoo.index[-1])
    print(f"\n[D1] Overlap: {overlap_start} -> {overlap_end}")

    oanda_ov = oanda.loc[(oanda.index >= overlap_start) & (oanda.index <= overlap_end)]
    yahoo_ov = yahoo.loc[(yahoo.index >= overlap_start) & (yahoo.index <= overlap_end)]

    print(f"[D1] OANDA overlap bars: {len(oanda_ov)}")
    print(f"[D1] Yahoo overlap bars: {len(yahoo_ov)}")
    ratio = len(oanda_ov) / max(len(yahoo_ov), 1)
    print(f"[D1] OANDA/Yahoo bar count ratio: {ratio:.2f}x")

    # Monthly profile
    print("\n[D1] Monthly bar count (OANDA vs Yahoo):")
    mo = monthly_bar_count(oanda_ov)
    mm = monthly_bar_count(yahoo_ov)
    merged = pd.concat({"oanda": mo, "yahoo": mm}, axis=1).fillna(0).astype(int)
    merged["oanda_vs_yahoo_pct"] = (merged["oanda"] - merged["yahoo"]) / merged["yahoo"].replace(0, np.nan) * 100
    print(merged.head(30).to_string())

    # H-L range
    oanda_rng = mean_normalized_range(oanda_ov)
    yahoo_rng = mean_normalized_range(yahoo_ov)
    print(f"\n[D1] Mean (High-Low)/Close per bar:")
    print(f"  OANDA: {oanda_rng*100:.4f}%")
    print(f"  Yahoo: {yahoo_rng*100:.4f}%")
    print(f"  Delta: {(oanda_rng/yahoo_rng - 1)*100:+.2f}% vs Yahoo")

    # Swing counts
    print("\n[D1] Counting swings (SWING_LOOKBACK=20, SWING_WINDOW=3)...")
    o_sh, o_sl = count_swings(oanda_ov)
    y_sh, y_sl = count_swings(yahoo_ov)
    print(f"  OANDA: {o_sh} swing highs + {o_sl} swing lows = {o_sh+o_sl} total ({(o_sh+o_sl)/len(oanda_ov)*1000:.1f} / 1000 bars)")
    print(f"  Yahoo: {y_sh} swing highs + {y_sl} swing lows = {y_sh+y_sl} total ({(y_sh+y_sl)/len(yahoo_ov)*1000:.1f} / 1000 bars)")
    if y_sh + y_sl > 0:
        swing_ratio = (o_sh + o_sl) / (y_sh + y_sl)
        print(f"  OANDA/Yahoo swing ratio: {swing_ratio:.2f}x")
    print(
        f"\n[D1] Verdict: "
        f"{'OANDA under-samples swings' if (o_sh+o_sl) / max(len(oanda_ov),1) < (y_sh+y_sl) / max(len(yahoo_ov),1) * 0.9 else 'swing rate comparable'}"
    )


if __name__ == "__main__":
    main()
