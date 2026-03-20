"""
Data Fetcher for SCAF 2.0

Dual data source: OANDA (Gold + Forex, 2005+) with Yahoo Finance fallback (Crypto).
P5: OANDA integration for 20+ years of Gold/Forex historical data.

Priority 3: Added GBP/USD, USD/JPY forex pairs.
Priority 4: Added ETH alongside BTC for crypto.
"""

import pandas as pd
import yfinance as yf
from typing import Optional, Dict, List

from .oanda_fetcher import is_oanda_available, is_oanda_instrument, fetch_oanda


# ============================================================
# Supported Symbol Registry
# ============================================================

SYMBOLS = {
    'gold': [
        'GC=F',         # Gold Futures (COMEX)
    ],
    'forex': [
        'EURUSD=X',     # EUR/USD (original)
        'GBPUSD=X',     # GBP/USD (Priority 3)
        'USDJPY=X',     # USD/JPY (Priority 3)
        # P6: AUD/USD tested and rejected — Pacific currency, Asian session is primary
        # move (not a trap). Killzone fade doesn't work. Same applies to NZD/USD.
    ],
    'crypto': [
        'BTC-USD',      # Bitcoin (original)
        'ETH-USD',      # Ethereum (Priority 4)
    ],
    'indices': [
        '^GSPC',        # S&P 500
        '^IXIC',        # NASDAQ Composite
        '^GDAXI',       # DAX (Germany)
    ],
}

# Human-readable names for reporting
SYMBOL_NAMES = {
    'GC=F': 'Gold (XAUUSD)',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^GDAXI': 'DAX',
}


def detect_asset_class(symbol: str) -> str:
    """Auto-detect asset class from symbol format."""
    s = symbol.upper()
    
    # Indices: ^GSPC, ^IXIC, ^GDAXI etc.
    if s.startswith('^'):
        return 'indices'
    
    if s.endswith('=X'):
        return 'forex'
    if s.endswith('=F') or s in ('XAUUSD', 'XAGUSD'):
        return 'gold' if s.startswith('GC') or 'XAU' in s else 'commodity'
    
    crypto_suffixes = ['-USD', '-USDT', '-BTC', '-ETH']
    for suffix in crypto_suffixes:
        if s.endswith(suffix):
            return 'crypto'
    
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
    Fetch OHLCV data. Tries OANDA first for Gold/Forex, falls back to Yahoo Finance.
    
    P5: OANDA provides 20+ years of Gold/Forex data (back to 2005).
    Yahoo Finance is used for Crypto and as fallback.
    
    Args:
        symbol: Ticker (e.g., 'GC=F', 'EURUSD=X', 'BTC-USD')
        interval: '1m','5m','15m','1h','4h','1d','1wk'
        period: '1mo','3mo','6mo','1y','2y','5y','10y','max'
        start_date: Optional 'YYYY-MM-DD' (overrides period)
        end_date: Optional 'YYYY-MM-DD'
        source: Force data source ('oanda', 'yahoo', or None for auto)
    
    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    # P5: Try OANDA first for Gold and Forex (20+ years of data)
    use_oanda = (
        source != 'yahoo'
        and is_oanda_available()
        and is_oanda_instrument(symbol)
        and (source == 'oanda' or True)  # Default to OANDA when available
    )
    
    if use_oanda:
        try:
            df = fetch_oanda(symbol, interval, period, start_date, end_date)
            if len(df) > 0:
                return df
        except Exception as e:
            print(f"  OANDA fetch failed for {symbol}, falling back to Yahoo: {e}")
    
    # Fallback: Yahoo Finance (crypto, or when OANDA fails)
    return _fetch_yahoo(symbol, interval, period, start_date, end_date)


def _fetch_yahoo(
    symbol: str,
    interval: str = "1h",
    period: str = "6mo",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """Fetch from Yahoo Finance (original implementation)."""
    ticker = yf.Ticker(symbol)
    
    if start_date and end_date:
        df = ticker.history(start=start_date, end=end_date, interval=interval)
    else:
        df = ticker.history(period=period, interval=interval)
    
    # Standardise columns
    df.columns = [col.replace(' ', '_') for col in df.columns]
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[[col for col in required if col in df.columns]]
    
    return df


def fetch_all(
    asset_class: str = 'all',
    interval: str = "4h",
    period: str = "1y",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for all symbols in an asset class (or all classes).
    
    Args:
        asset_class: 'gold', 'forex', 'crypto', or 'all'
        interval: Timeframe
        period: Lookback period
        start_date: Optional start date
        end_date: Optional end date
    
    Returns:
        Dict mapping symbol -> DataFrame
    """
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
