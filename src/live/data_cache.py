"""
Live Data Cache — Resilient Fetch Wrapper

Provides a retry-and-fallback layer around the primary data fetcher for live
runs. Wraps `fetch()` with:

  1. A smaller live lookback (1mo instead of 6mo) since live only needs
     ~300 bars.
  2. Persistent per-symbol CSV cache of the last successful fetch.
  3. Freshness check: if fetch fails but cache is recent (<= 3 hours), return
     cached data rather than aborting the whole run.

This is Round-8 Step-2 infrastructure: prevents transient OANDA 502/SSL errors
from raising Telegram alerts when the next hourly trigger will succeed
normally.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional
import pandas as pd

from src.data.fetcher import fetch as _primary_fetch


CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'live_cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MAX_STALE_SECONDS = 3 * 3600  # 3 hours — covers one skipped run + buffer


def _cache_path(symbol: str, interval: str) -> Path:
    safe = symbol.replace('=', '_').replace('^', '').replace('/', '_').replace('-', '_')
    return CACHE_DIR / f"{safe}_{interval}.parquet"


def _write_cache(symbol: str, interval: str, df: pd.DataFrame) -> None:
    try:
        df.to_parquet(_cache_path(symbol, interval))
    except Exception:
        try:
            df.to_csv(_cache_path(symbol, interval).with_suffix('.csv'))
        except Exception:
            pass


def _read_cache(symbol: str, interval: str) -> Optional[pd.DataFrame]:
    p = _cache_path(symbol, interval)
    if p.exists():
        try:
            return pd.read_parquet(p)
        except Exception:
            pass
    p_csv = p.with_suffix('.csv')
    if p_csv.exists():
        try:
            df = pd.read_csv(p_csv, index_col=0, parse_dates=True)
            return df
        except Exception:
            pass
    return None


def _cache_age_seconds(symbol: str, interval: str) -> Optional[float]:
    p = _cache_path(symbol, interval)
    if p.exists():
        return time.time() - p.stat().st_mtime
    p_csv = p.with_suffix('.csv')
    if p_csv.exists():
        return time.time() - p_csv.stat().st_mtime
    return None


def fetch_live(
    symbol: str,
    interval: str = '1h',
    period: str = '1mo',
    min_bars: int = 300,
) -> pd.DataFrame:
    """
    Fetch data for live trading with automatic retry-and-cache fallback.

    Returns a DataFrame with at least `min_bars` rows, or raises RuntimeError
    if neither network nor cache can satisfy the request.

    Behaviour:
      - Try primary fetch (OANDA / IBKR / Binance / Yahoo tiered routing).
      - On success: write cache and return.
      - On failure: if cache exists and is fresher than MAX_STALE_SECONDS,
        return cached data (with a warning).
      - Otherwise: raise the original error.
    """
    last_err = None
    try:
        df = _primary_fetch(symbol, interval, period)
        if len(df) >= min_bars:
            _write_cache(symbol, interval, df)
            return df
        last_err = RuntimeError(f"primary fetch returned only {len(df)} bars (<{min_bars})")
    except Exception as e:
        last_err = e

    cached = _read_cache(symbol, interval)
    age = _cache_age_seconds(symbol, interval)
    if cached is not None and age is not None and age <= MAX_STALE_SECONDS:
        if len(cached) >= min_bars:
            print(f"  [cache-fallback] {symbol} fetch failed ({last_err}); using cache ({len(cached)} bars, age {age/60:.1f}min)")
            return cached

    raise RuntimeError(f"live fetch failed and cache unusable: {last_err}") from last_err
