"""
Binance Historical Data Fetcher

Downloads historical kline (candlestick) data from Binance public API.
Provides 5Y+ of hourly BTC/ETH data (back to 2017).
No API key required for historical data (public endpoint).

Rate limit: 1200 requests/min (public). Each request returns up to 1000 candles.

Data is cached to CSV in data/cache/ for offline walk-forward.

Run: py -m src.data.binance_fetcher
"""

import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / 'data' / 'cache'

BASE_URL = 'https://api.binance.com'

SYMBOL_MAP = {
    'BTC-USD': 'BTCUSDT',
    'ETH-USD': 'ETHUSDT',
    'SOL-USD': 'SOLUSDT',
    'XRP-USD': 'XRPUSDT',
    'BNB-USD': 'BNBUSDT',
}

INTERVAL_MAP = {
    '1m': '1m',
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h',
    '4h': '4h',
    '1d': '1d',
    '1wk': '1w',
}


def is_binance_available() -> bool:
    """Check if Binance API is reachable."""
    try:
        resp = requests.get(f'{BASE_URL}/api/v3/ping', timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def is_binance_instrument(symbol: str) -> bool:
    """Check if a symbol has a Binance mapping."""
    return symbol in SYMBOL_MAP


def _get_cache_path(symbol: str, interval: str) -> Path:
    safe_symbol = symbol.replace('-', '').replace('=', '')
    return CACHE_DIR / f'{safe_symbol}_{interval}_binance.csv'


def _load_cache(symbol: str, interval: str) -> Optional[pd.DataFrame]:
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
    import os
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _get_cache_path(symbol, interval)
    tmp = path.with_suffix(path.suffix + '.tmp')
    df.to_csv(tmp)
    os.replace(tmp, path)


def _period_to_start_ms(period: str) -> int:
    """Convert period string to a start timestamp in milliseconds (UTC)."""
    now = datetime.now(timezone.utc)
    if period.endswith('y'):
        years = int(period[:-1])
        start = now - timedelta(days=years * 365)
    elif period.endswith('mo'):
        months = int(period[:-2])
        start = now - timedelta(days=months * 30)
    elif period == 'max':
        start = datetime(2017, 1, 1, tzinfo=timezone.utc)
    else:
        start = now - timedelta(days=365)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return int(start.timestamp() * 1000)


def fetch_binance(
    symbol: str,
    interval: str = '1h',
    period: str = '5y',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Fetch historical kline data from Binance.

    Args:
        symbol: Our standard symbol ('BTC-USD', 'ETH-USD')
        interval: Timeframe ('1h', '4h', '1d', etc.)
        period: Lookback ('1y', '2y', '5y', 'max')
        start_date: Optional 'YYYY-MM-DD'
        end_date: Optional 'YYYY-MM-DD'
        use_cache: Check CSV cache first

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    if use_cache:
        cached = _load_cache(symbol, interval)
        if cached is not None and len(cached) > 100:
            cache_end = pd.Timestamp(cached.index[-1])
            if cache_end.tzinfo is None:
                cache_end = cache_end.tz_localize('UTC')
            else:
                cache_end = cache_end.tz_convert('UTC')
            if (pd.Timestamp.now(tz='UTC') - cache_end).days < 3:
                print(f"  Using cached Binance data for {symbol} ({len(cached)} bars)")
                return cached

    if symbol not in SYMBOL_MAP:
        raise ValueError(f"Symbol '{symbol}' not on Binance. Available: {list(SYMBOL_MAP.keys())}")

    binance_symbol = SYMBOL_MAP[symbol]
    binance_interval = INTERVAL_MAP.get(interval)
    if not binance_interval:
        raise ValueError(f"Interval '{interval}' not supported on Binance.")

    if start_date:
        sd = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        start_ms = int(sd.timestamp() * 1000)
    else:
        start_ms = _period_to_start_ms(period)

    if end_date:
        ed = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end_ms = int(ed.timestamp() * 1000)
    else:
        end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    all_klines = []
    current_start = start_ms
    request_count = 0

    print(f"  Fetching {symbol} {interval} from Binance...")

    while current_start < end_ms:
        params = {
            'symbol': binance_symbol,
            'interval': binance_interval,
            'startTime': current_start,
            'endTime': end_ms,
            'limit': 1000,
        }

        try:
            resp = requests.get(f'{BASE_URL}/api/v3/klines', params=params, timeout=15)
            if resp.status_code == 429:
                print(f"  Binance rate limited, waiting 10s...")
                time.sleep(10)
                continue
            resp.raise_for_status()
            klines = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  Binance API error: {e}")
            if all_klines:
                raise ValueError(
                    f"Binance fetch interrupted after {len(all_klines)} bars: {e}"
                ) from e
            break

        if not klines:
            break

        all_klines.extend(klines)
        request_count += 1

        last_close_time = klines[-1][6]  # Close time of last candle
        current_start = last_close_time + 1

        if len(klines) < 1000:
            break

        if request_count % 10 == 0:
            time.sleep(0.5)
            print(f"    ...{request_count} requests, {len(all_klines)} bars")

        if request_count >= 500:
            break

    if not all_klines:
        cached = _load_cache(symbol, interval)
        if cached is not None:
            return cached
        raise ValueError(f"No data from Binance for {symbol} {interval}")

    records = []
    for k in all_klines:
        records.append({
            'Datetime': pd.to_datetime(k[0], unit='ms', utc=True),
            'Open': float(k[1]),
            'High': float(k[2]),
            'Low': float(k[3]),
            'Close': float(k[4]),
            'Volume': float(k[5]),
        })

    df = pd.DataFrame(records)
    df.set_index('Datetime', inplace=True)
    df = df[~df.index.duplicated(keep='last')]
    df.sort_index(inplace=True)

    print(f"  Downloaded {len(df)} bars ({df.index[0]} to {df.index[-1]})")

    _save_cache(df, symbol, interval)
    print(f"  Cached to {_get_cache_path(symbol, interval)}")

    return df


def main():
    """Test Binance connection and download sample data."""
    print("Binance Data Fetcher Test")
    print(f"{'=' * 50}")

    if not is_binance_available():
        print("Binance API not reachable. Check internet connection.")
        return

    print("Binance API connected!")
    for symbol in ['BTC-USD', 'ETH-USD']:
        try:
            df = fetch_binance(symbol, '1h', '5y')
            print(f"  {symbol}: {len(df)} bars ({df.index[0]} to {df.index[-1]})")
        except Exception as e:
            print(f"  {symbol}: FAILED - {e}")


if __name__ == '__main__':
    main()
