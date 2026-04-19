"""
OANDA Data Fetcher

Fetches historical candle data from OANDA's v20 REST API.
Provides 20+ years of Gold data (back to 2005).

Uses the free demo/practice API endpoint. Requires:
- OANDA_API_KEY in .env file
- OANDA_ACCOUNT_ID in .env file

OANDA v20 API limits: 5000 candles per request.
For large date ranges, the fetcher automatically paginates.
"""

import os
import time
import requests
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    # Find .env relative to this file (project root)
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars


# ============================================================
# OANDA Configuration
# ============================================================

OANDA_API_KEY = os.getenv('OANDA_API_KEY', '')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID', '')
OANDA_ENV = os.getenv('OANDA_ENVIRONMENT', 'practice')

# API endpoints
OANDA_URLS = {
    'practice': 'https://api-fxpractice.oanda.com',
    'live': 'https://api-fxtrade.oanda.com',
}

BASE_URL = OANDA_URLS.get(OANDA_ENV, OANDA_URLS['practice'])

# Maximum candles per OANDA API request
MAX_CANDLES_PER_REQUEST = 5000

# Map our interval strings to OANDA granularities
INTERVAL_MAP = {
    '1m': 'M1',
    '5m': 'M5',
    '15m': 'M15',
    '30m': 'M30',
    '1h': 'H1',
    '4h': 'H4',
    '1d': 'D',
    '1wk': 'W',
}

# Map our symbols to OANDA instrument names
SYMBOL_MAP = {
    'GC=F': 'XAU_USD',          # Gold
    'EURUSD=X': 'EUR_USD',      # EUR/USD
    'GBPUSD=X': 'GBP_USD',     # GBP/USD
    'USDJPY=X': 'USD_JPY',     # USD/JPY
    'AUDUSD=X': 'AUD_USD',     # AUD/USD
    'AUDJPY=X': 'AUD_JPY',     # AUD/JPY (Round 7 scout)
    'EURJPY=X': 'EUR_JPY',     # EUR/JPY (Round 7 scout)
    'NZDUSD=X': 'NZD_USD',     # NZD/USD (Round 7 scout)
    'USDCHF=X': 'USD_CHF',     # USD/CHF (Round 7 scout)
    '^GDAXI': 'DE30_EUR',      # DAX (Germany 30 CFD)
    '^IXIC': 'NAS100_USD',     # NASDAQ (US Nas 100 CFD)
    '^GSPC': 'SPX500_USD',     # S&P 500 CFD (for future use)
}

# Reverse map for lookups
OANDA_TO_SYMBOL = {v: k for k, v in SYMBOL_MAP.items()}


def is_oanda_available() -> bool:
    """Check if OANDA credentials are configured."""
    return bool(OANDA_API_KEY) and bool(OANDA_ACCOUNT_ID)


def is_oanda_instrument(symbol: str) -> bool:
    """Check if a symbol is available on OANDA."""
    return symbol in SYMBOL_MAP


def _get_headers() -> dict:
    """Build OANDA API request headers."""
    return {
        'Authorization': f'Bearer {OANDA_API_KEY}',
        'Content-Type': 'application/json',
    }


def _period_to_start_date(period: str) -> datetime:
    """Convert a period string (e.g., '5y', '2y', '6mo') to a start datetime."""
    now = datetime.utcnow()
    
    if period.endswith('y'):
        years = int(period[:-1])
        return now - timedelta(days=years * 365)
    elif period.endswith('mo'):
        months = int(period[:-2])
        return now - timedelta(days=months * 30)
    elif period == 'max':
        return datetime(2005, 1, 1)  # OANDA data starts ~2005
    else:
        return now - timedelta(days=365)  # Default 1 year


def _estimate_bars_per_day(granularity: str) -> float:
    """Estimate how many candles per calendar day for a given granularity."""
    estimates = {
        'M1': 1440,
        'M5': 288,
        'M15': 96,
        'M30': 48,
        'H1': 24,
        'H4': 6,
        'D': 1,
        'W': 0.143,
    }
    return estimates.get(granularity, 6)


def fetch_oanda(
    symbol: str,
    interval: str = '4h',
    period: str = '5y',
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch historical candle data from OANDA v20 API.
    
    Handles pagination automatically (OANDA limits 5000 candles/request).
    
    Args:
        symbol: Our standard symbol (e.g., 'GC=F', 'EURUSD=X')
        interval: Timeframe ('1m','5m','15m','30m','1h','4h','1d','1wk')
        period: Lookback period ('6mo','1y','2y','5y','10y','max')
        start_date: Optional 'YYYY-MM-DD' (overrides period)
        end_date: Optional 'YYYY-MM-DD'
    
    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
        (same format as Yahoo Finance fetch)
    
    Raises:
        ValueError: If symbol not available on OANDA or credentials missing
    """
    if not is_oanda_available():
        raise ValueError("OANDA credentials not configured. Check .env file.")
    
    if symbol not in SYMBOL_MAP:
        raise ValueError(f"Symbol '{symbol}' not available on OANDA. "
                         f"Available: {list(SYMBOL_MAP.keys())}")
    
    instrument = SYMBOL_MAP[symbol]
    granularity = INTERVAL_MAP.get(interval)
    if not granularity:
        raise ValueError(f"Interval '{interval}' not supported. "
                         f"Available: {list(INTERVAL_MAP.keys())}")
    
    # Determine date range
    if start_date:
        dt_start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        dt_start = _period_to_start_date(period)
    
    if end_date:
        dt_end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        dt_end = datetime.utcnow()
    
    # ============================================================
    # Paginated fetch (OANDA max 5000 candles per request)
    # ============================================================
    all_candles = []
    current_start = dt_start
    bars_per_day = _estimate_bars_per_day(granularity)
    request_count = 0
    prev_start = None  # Track to detect infinite loops
    
    while current_start < dt_end:
        # Safety: break if we haven't advanced since last iteration
        if prev_start is not None and current_start <= prev_start:
            break
        prev_start = current_start
        
        # Calculate how many days to request to stay under 5000 candles
        if bars_per_day > 0:
            days_per_chunk = int(MAX_CANDLES_PER_REQUEST / bars_per_day * 0.9)  # 90% safety margin
        else:
            days_per_chunk = 3650  # ~10 years for weekly
        
        chunk_end = min(current_start + timedelta(days=days_per_chunk), dt_end)
        
        # Skip if chunk is too small (less than 1 hour remaining)
        if (chunk_end - current_start).total_seconds() < 3600:
            break
        
        params = {
            'granularity': granularity,
            'from': current_start.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'to': chunk_end.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'price': 'M',  # Midpoint prices
        }
        
        url = f"{BASE_URL}/v3/instruments/{instrument}/candles"
        
        try:
            response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
            
            if response.status_code == 429:
                # Rate limited -- wait and retry
                print(f"  OANDA rate limited, waiting 2s...")
                time.sleep(2)
                continue
            
            response.raise_for_status()
            data = response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"  OANDA API error: {e}")
            if all_candles:
                raise ValueError(
                    f"OANDA fetch interrupted after {len(all_candles)} candles "
                    f"(partial history is invalid for research): {e}"
                ) from e
            break
        
        candles = data.get('candles', [])
        if not candles:
            break
        
        all_candles.extend(candles)
        request_count += 1
        
        # Move start to after the last candle we received
        last_time = candles[-1]['time']
        new_start = datetime.strptime(last_time[:19], '%Y-%m-%dT%H:%M:%S') + timedelta(seconds=1)
        
        # If we didn't advance, we're at the end of available data
        if new_start <= current_start:
            break
        current_start = new_start
        
        # Small delay to respect rate limits (max ~25 requests/second on practice)
        if request_count % 10 == 0:
            time.sleep(0.5)
    
    if not all_candles:
        raise ValueError(f"No data returned from OANDA for {instrument} {granularity}")
    
    # ============================================================
    # Convert to DataFrame (same format as Yahoo Finance)
    # ============================================================
    records = []
    for candle in all_candles:
        if not candle.get('complete', True):
            continue  # Skip incomplete (current) candle
        
        mid = candle['mid']
        records.append({
            'Datetime': pd.to_datetime(candle['time']),
            'Open': float(mid['o']),
            'High': float(mid['h']),
            'Low': float(mid['l']),
            'Close': float(mid['c']),
            'Volume': int(candle.get('volume', 0)),
        })
    
    df = pd.DataFrame(records)
    df.set_index('Datetime', inplace=True)
    df.index = pd.to_datetime(df.index, utc=True)
    
    # Remove duplicates (pagination overlap)
    df = df[~df.index.duplicated(keep='last')]
    df.sort_index(inplace=True)
    
    return df
