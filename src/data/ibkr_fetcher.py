"""
IBKR Historical Data Fetcher

Downloads historical 1H bars from Interactive Brokers via ib_insync.
Provides 20+ years of index data (S&P 500, NASDAQ, DAX) that Yahoo Finance
cannot supply for intraday timeframes.

Prerequisites:
  1. IBKR paper or live account
  2. TWS or IB Gateway running with API enabled (port 7497 for paper)
  3. pip install ib_insync

Data is cached to CSV in data/cache/ so walk-forward works without TWS running.

Run: py -m src.data.ibkr_fetcher  (for testing)
"""

import os
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'cache'

# Map our symbols to IBKR contract specs
IBKR_CONTRACTS = {
    '^GSPC': {'symbol': 'SPX', 'exchange': 'CBOE', 'secType': 'IND', 'currency': 'USD'},
    '^IXIC': {'symbol': 'COMP', 'exchange': 'NASDAQ', 'secType': 'IND', 'currency': 'USD'},
    '^GDAXI': {'symbol': 'DAX', 'exchange': 'EUREX', 'secType': 'IND', 'currency': 'EUR'},
    'GC=F': {'symbol': 'XAUUSD', 'exchange': 'SMART', 'secType': 'CMDTY', 'currency': 'USD'},
}

# Map our interval strings to IBKR bar sizes
INTERVAL_MAP = {
    '1m': '1 min',
    '5m': '5 mins',
    '15m': '15 mins',
    '30m': '30 mins',
    '1h': '1 hour',
    '4h': '4 hours',
    '1d': '1 day',
    '1wk': '1 week',
}

# IBKR duration limits per bar size (max bars per request ~2000)
# Use conservative durations to stay under limits
DURATION_PER_REQUEST = {
    '1 min': '1 D',
    '5 mins': '5 D',
    '15 mins': '10 D',
    '30 mins': '20 D',
    '1 hour': '30 D',
    '4 hours': '120 D',
    '1 day': '1 Y',
    '1 week': '5 Y',
}


def is_ibkr_available() -> bool:
    """Check if ib_insync is installed and TWS/Gateway is reachable."""
    try:
        from ib_insync import IB
        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=99, timeout=5)
        ib.disconnect()
        return True
    except Exception:
        return False


def is_ibkr_instrument(symbol: str) -> bool:
    """Check if a symbol has an IBKR mapping."""
    return symbol in IBKR_CONTRACTS


def _get_cache_path(symbol: str, interval: str) -> Path:
    """Get the cache file path for a symbol/interval combination."""
    safe_symbol = symbol.replace('^', '').replace('=', '')
    return CACHE_DIR / f'{safe_symbol}_{interval}.csv'


def _load_cache(symbol: str, interval: str) -> Optional[pd.DataFrame]:
    """Load cached data if it exists and is recent enough."""
    path = _get_cache_path(symbol, interval)
    if not path.exists():
        return None

    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    except Exception:
        return None


def _save_cache(df: pd.DataFrame, symbol: str, interval: str) -> None:
    """Save data to CSV cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _get_cache_path(symbol, interval)
    df.to_csv(path)


def fetch_ibkr(
    symbol: str,
    interval: str = '1h',
    period: str = '10y',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch historical data from IBKR with automatic pagination.

    Args:
        symbol: Our standard symbol ('^GSPC', '^IXIC', '^GDAXI', 'GC=F')
        interval: Timeframe ('1h', '4h', '1d', etc.)
        period: Lookback ('1y', '5y', '10y')
        start_date: Optional 'YYYY-MM-DD'
        end_date: Optional 'YYYY-MM-DD'
        use_cache: If True, check CSV cache first

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    # Try cache first
    if use_cache:
        cached = _load_cache(symbol, interval)
        if cached is not None and len(cached) > 100:
            # If we have cached data and it's not too stale, use it
            cache_end = cached.index[-1]
            if (datetime.utcnow() - cache_end.replace(tzinfo=None)).days < 7:
                print(f"  Using cached IBKR data for {symbol} ({len(cached)} bars)")
                return cached

    if symbol not in IBKR_CONTRACTS:
        raise ValueError(f"Symbol '{symbol}' not available on IBKR. "
                         f"Available: {list(IBKR_CONTRACTS.keys())}")

    bar_size = INTERVAL_MAP.get(interval)
    if not bar_size:
        raise ValueError(f"Interval '{interval}' not supported. "
                         f"Available: {list(INTERVAL_MAP.keys())}")

    try:
        from ib_insync import IB, Contract, Index, Commodity
    except ImportError:
        raise ImportError(
            "ib_insync not installed. Run: pip install ib_insync\n"
            "Also ensure TWS or IB Gateway is running with API enabled on port 7497."
        )

    # Build contract
    spec = IBKR_CONTRACTS[symbol]
    if spec['secType'] == 'IND':
        contract = Index(spec['symbol'], spec['exchange'], spec['currency'])
    elif spec['secType'] == 'CMDTY':
        contract = Commodity(spec['symbol'], spec['exchange'], spec['currency'])
    else:
        contract = Contract(**spec)

    # Determine date range (naive datetimes — IBKR API expects naive UTC)
    if end_date:
        dt_end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        dt_end = datetime.utcnow()

    if start_date:
        dt_start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        years = int(period.replace('y', '').replace('mo', ''))
        if period.endswith('y'):
            dt_start = dt_end - timedelta(days=years * 365)
        elif period.endswith('mo'):
            dt_start = dt_end - timedelta(days=years * 30)
        else:
            dt_start = dt_end - timedelta(days=365)

    def _to_naive(dt_obj):
        """Strip timezone info for comparison (IBKR returns tz-aware datetimes)."""
        if hasattr(dt_obj, 'tzinfo') and dt_obj.tzinfo is not None:
            return dt_obj.replace(tzinfo=None)
        return dt_obj

    # Connect to TWS/Gateway
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=10, timeout=15)
    except Exception as e:
        # Fall back to cached data if available
        cached = _load_cache(symbol, interval)
        if cached is not None:
            print(f"  IBKR connection failed, using cached data ({len(cached)} bars)")
            return cached
        raise ConnectionError(
            f"Cannot connect to TWS/IB Gateway: {e}\n"
            f"Ensure TWS or IB Gateway is running with API enabled on port 7497."
        )

    # Paginated fetch (IBKR limits ~2000 bars per request)
    all_bars = []
    current_end = dt_end
    duration = DURATION_PER_REQUEST.get(bar_size, '30 D')
    request_count = 0

    print(f"  Fetching {symbol} {interval} from IBKR ({dt_start.date()} to {dt_end.date()})...")

    try:
        while current_end > dt_start:
            bars = ib.reqHistoricalData(
                contract,
                endDateTime=current_end.strftime('%Y%m%d %H:%M:%S'),
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES' if spec['secType'] != 'CMDTY' else 'MIDPOINT',
                useRTH=False,  # Include extended hours
                formatDate=1,
            )

            if not bars:
                break

            all_bars = bars + all_bars  # Prepend (we're going backwards)
            request_count += 1

            # Move end to before the earliest bar
            earliest = bars[0].date
            if isinstance(earliest, str):
                earliest = datetime.strptime(earliest, '%Y%m%d  %H:%M:%S')
            else:
                earliest = _to_naive(earliest)
            current_end = earliest - timedelta(seconds=1)

            # Rate limiting
            if request_count % 5 == 0:
                time.sleep(1)
                print(f"    ...{request_count} requests, {len(all_bars)} bars so far")

            # Safety: max 200 requests
            if request_count >= 200:
                break

    finally:
        ib.disconnect()

    if not all_bars:
        # Fall back to cache
        cached = _load_cache(symbol, interval)
        if cached is not None:
            return cached
        raise ValueError(f"No data returned from IBKR for {symbol} {interval}")

    # Convert to DataFrame
    records = []
    for bar in all_bars:
        dt = bar.date
        if isinstance(dt, str):
            dt = pd.to_datetime(dt)
        records.append({
            'Datetime': dt,
            'Open': bar.open,
            'High': bar.high,
            'Low': bar.low,
            'Close': bar.close,
            'Volume': bar.volume,
        })

    df = pd.DataFrame(records)
    df.set_index('Datetime', inplace=True)
    df.index = pd.to_datetime(df.index, utc=True)
    df = df[~df.index.duplicated(keep='last')]
    df.sort_index(inplace=True)

    # Filter to requested range
    if dt_start:
        df = df[df.index >= pd.Timestamp(dt_start, tz='UTC')]

    print(f"  Downloaded {len(df)} bars ({df.index[0]} to {df.index[-1]})")

    # Cache for offline use
    _save_cache(df, symbol, interval)
    print(f"  Cached to {_get_cache_path(symbol, interval)}")

    return df


def main():
    """Test IBKR connection and download sample data."""
    print("IBKR Data Fetcher Test")
    print(f"{'='*50}")

    if not is_ibkr_available():
        print("IBKR not available. Checking cache...")
        for symbol in ['^GSPC', '^IXIC', '^GDAXI']:
            cached = _load_cache(symbol, '1h')
            if cached is not None:
                print(f"  {symbol}: {len(cached)} cached bars")
            else:
                print(f"  {symbol}: no cached data")
        print("\nTo use IBKR:")
        print("  1. Install: pip install ib_insync")
        print("  2. Start TWS or IB Gateway")
        print("  3. Enable API on port 7497 (paper trading)")
        return

    print("IBKR connected!")
    for symbol in ['^GSPC', '^IXIC', '^GDAXI']:
        try:
            df = fetch_ibkr(symbol, '1h', '1y')
            print(f"  {symbol}: {len(df)} bars ({df.index[0]} to {df.index[-1]})")
        except Exception as e:
            print(f"  {symbol}: FAILED — {e}")


if __name__ == '__main__':
    main()
