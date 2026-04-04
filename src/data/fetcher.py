"""
Data Fetcher — Triple Source Routing

OANDA (Gold, 20Y+) → IBKR (Indices, 10Y+) → Yahoo Finance (fallback).
"""

import pandas as pd
import yfinance as yf
from typing import Optional, Dict, List

from .oanda_fetcher import is_oanda_available, is_oanda_instrument, fetch_oanda
from .ibkr_fetcher import is_ibkr_available, is_ibkr_instrument, fetch_ibkr


# ============================================================
# Supported Symbol Registry
# ============================================================

SYMBOLS = {
    'gold': [
        'GC=F',         # Gold Futures (COMEX)
    ],
    'indices': [
        '^GSPC',        # S&P 500
        '^IXIC',        # NASDAQ Composite
        '^GDAXI',       # DAX (Germany)
    ],
}

SYMBOL_NAMES = {
    'GC=F': 'Gold (XAUUSD)',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^GDAXI': 'DAX',
}


def detect_asset_class(symbol: str) -> str:
    """Auto-detect asset class from symbol format."""
    s = symbol.upper()

    if s.startswith('^'):
        return 'indices'
    if s.endswith('=F') or s in ('XAUUSD', 'XAGUSD'):
        return 'gold' if s.startswith('GC') or 'XAU' in s else 'commodity'

    return 'equity'


def get_symbol_name(symbol: str) -> str:
    """Get human-readable name for a symbol."""
    return SYMBOL_NAMES.get(symbol, symbol)


def get_symbols_for_class(asset_class: str) -> List[str]:
    """Get all supported symbols for an asset class."""
    return SYMBOLS.get(asset_class, [])


def fetch(
    symbol: str,
    interval: str = "1h",
    period: str = "6mo",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch OHLCV data with automatic source routing.

    Priority: OANDA (Gold) → IBKR (Indices) → Yahoo Finance (fallback).

    Args:
        symbol: Ticker (e.g., 'GC=F', '^GSPC')
        interval: '1m','5m','15m','1h','4h','1d','1wk'
        period: '1mo','3mo','6mo','1y','2y','5y','10y','max'
        start_date: Optional 'YYYY-MM-DD' (overrides period)
        end_date: Optional 'YYYY-MM-DD'
        source: Force data source ('oanda', 'ibkr', 'yahoo', or None for auto)

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    use_oanda = (
        source not in ('yahoo', 'ibkr')
        and is_oanda_available()
        and is_oanda_instrument(symbol)
        and (source == 'oanda' or True)
    )

    if use_oanda:
        try:
            df = fetch_oanda(symbol, interval, period, start_date, end_date)
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"  OANDA fetch failed for {symbol}, trying next source: {e}")

    use_ibkr = (
        source not in ('yahoo', 'oanda')
        and is_ibkr_instrument(symbol)
        and (source == 'ibkr' or True)
    )

    if use_ibkr:
        try:
            df = fetch_ibkr(symbol, interval, period, start_date, end_date)
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"  IBKR fetch failed for {symbol}, falling back to Yahoo: {e}")

    return _fetch_yahoo(symbol, interval, period, start_date, end_date)


def _fetch_yahoo(
    symbol: str,
    interval: str = "1h",
    period: str = "6mo",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """Fetch from Yahoo Finance (fallback)."""
    ticker = yf.Ticker(symbol)

    if start_date and end_date:
        df = ticker.history(start=start_date, end=end_date, interval=interval)
    else:
        df = ticker.history(period=period, interval=interval)

    df.columns = [col.replace(' ', '_') for col in df.columns]
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[[col for col in required if col in df.columns]]

    return df


def fetch_all(
    asset_class: str = 'all',
    interval: str = "1h",
    period: str = "1y",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """Fetch OHLCV data for all symbols in an asset class (or all classes)."""
    if asset_class == 'all':
        symbols = []
        for syms in SYMBOLS.values():
            symbols.extend(syms)
    else:
        symbols = SYMBOLS.get(asset_class, [])

    results = {}
    for symbol in symbols:
        try:
            df = fetch(symbol, interval, period, start_date, end_date)
            if len(df) > 0:
                results[symbol] = df
        except Exception as e:
            print(f"  Warning: Failed to fetch {symbol}: {e}")

    return results
