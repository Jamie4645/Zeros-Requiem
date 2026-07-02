"""
Data Fetcher — Tiered Source Routing

Priority:
  Gold (GC=F):    OANDA (20Y+) — mandatory, no Yahoo fallback
  Forex:          OANDA (20Y+) — mandatory for registered pairs
  Indices:        IBKR (10Y+)  — mandatory when available, Yahoo fallback ONLY
  Crypto:         Binance (5Y+) — preferred, Yahoo fallback
  Other:          Yahoo Finance

Yahoo Finance is ONLY used for symbols not supported by premium sources.
"""

import pandas as pd
import yfinance as yf
from typing import Optional, Dict, List

from .oanda_fetcher import is_oanda_available, is_oanda_instrument, fetch_oanda
from .ibkr_fetcher import is_ibkr_available, is_ibkr_instrument, fetch_ibkr
from .binance_fetcher import is_binance_available, is_binance_instrument, fetch_binance

# Symbols that MUST use premium sources — Yahoo is forbidden for these
PREMIUM_ONLY_SYMBOLS = {'GC=F', '^GSPC', '^IXIC', '^GDAXI'}


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
    'forex': [
        'EURUSD=X',     # EUR/USD
        'GBPUSD=X',     # GBP/USD
        'USDJPY=X',     # USD/JPY
        'AUDUSD=X',     # AUD/USD
    ],
    'crypto': [
        'BTC-USD',      # Bitcoin
        'ETH-USD',      # Ethereum
    ],
}

SYMBOL_NAMES = {
    'GC=F': 'Gold (XAUUSD)',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^GDAXI': 'DAX',
    'EURUSD=X': 'EUR/USD',
    'GBPUSD=X': 'GBP/USD',
    'USDJPY=X': 'USD/JPY',
    'AUDUSD=X': 'AUD/USD',
    'BTC-USD': 'Bitcoin (BTC)',
    'ETH-USD': 'Ethereum (ETH)',
}


FOREX_SYMBOLS = {'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X',
                  'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 'EURGBP=X'}
CRYPTO_SYMBOLS = {'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'BNB-USD'}


def detect_asset_class(symbol: str) -> str:
    """Auto-detect asset class from symbol format."""
    s = symbol.upper()

    if symbol in CRYPTO_SYMBOLS or s.endswith('-USD') and not s.startswith('^'):
        return 'crypto'
    if symbol in FOREX_SYMBOLS or (s.endswith('=X') and not s.endswith('=F')):
        return 'forex'
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

    Raises:
        RuntimeError: If a premium-only symbol (Gold, indices) cannot be fetched
                      from its required source. Yahoo is never used for these.
    """
    # ── OANDA: Gold and Forex ─────────────────────────────────
    # OANDA is the mandatory source for Gold. No Yahoo fallback.
    if source != 'yahoo' and source != 'ibkr':
        if is_oanda_instrument(symbol):
            if not is_oanda_available():
                raise RuntimeError(
                    f"OANDA credentials not configured but {symbol} requires OANDA. "
                    f"Check your .env file (OANDA_API_KEY, OANDA_ACCOUNT_ID)."
                )
            print(f"  Fetching {symbol} from OANDA...")
            df = fetch_oanda(symbol, interval, period, start_date, end_date)
            if len(df) > 0:
                return df
            raise RuntimeError(f"OANDA returned empty data for {symbol}.")

    # ── IBKR: Indices ─────────────────────────────────────────
    # IBKR is the mandatory source for indices. Yahoo only as last resort
    # if IBKR is unavailable (TWS not running) AND symbol is not premium-only.
    if source != 'yahoo' and source != 'oanda':
        if is_ibkr_instrument(symbol):
            if symbol == '^IXIC':
                # 2026-07-02 audit: OANDA resolves ^IXIC to NAS100 (Nasdaq-100)
                # but IBKR resolves it to COMP (Nasdaq Composite) — a DIFFERENT
                # index. Mixing sources silently corrupts any validation run.
                print("  WARNING: ^IXIC via IBKR = Nasdaq COMPOSITE (COMP), but "
                      "OANDA/canon = Nasdaq-100 (NAS100). These are different "
                      "indices — do NOT mix this data with OANDA-based results.")
            if is_ibkr_available():
                print(f"  Fetching {symbol} from IBKR...")
                try:
                    df = fetch_ibkr(symbol, interval, period, start_date, end_date)
                    if len(df) > 0:
                        return df
                except Exception as e:
                    print(f"  IBKR fetch failed for {symbol}: {e}")
            else:
                print(f"  IBKR not available (TWS/Gateway not running).")

            # Check cache before falling back
            from .ibkr_fetcher import _load_cache
            cached = _load_cache(symbol, interval)
            if cached is not None and len(cached) > 100:
                print(f"  Using cached IBKR data for {symbol} ({len(cached)} bars)")
                return cached

            if symbol in PREMIUM_ONLY_SYMBOLS:
                raise RuntimeError(
                    f"{symbol} requires IBKR (10Y+ data). "
                    f"Start TWS or IB Gateway on port 7497, then retry."
                )
            print(f"  WARNING: Falling back to Yahoo for {symbol} (limited to ~2Y for 1H)")

    # ── Binance: Crypto ─────────────────────────────────────────
    if source != 'yahoo' and source != 'oanda' and source != 'ibkr':
        if is_binance_instrument(symbol):
            if is_binance_available():
                print(f"  Fetching {symbol} from Binance...")
                try:
                    df = fetch_binance(symbol, interval, period, start_date, end_date)
                    if len(df) > 0:
                        return df
                except Exception as e:
                    print(f"  Binance fetch failed for {symbol}: {e}")
            else:
                print(f"  Binance not available. Checking cache...")

            from .binance_fetcher import _load_cache as _load_binance_cache
            cached = _load_binance_cache(symbol, interval)
            if cached is not None and len(cached) > 100:
                print(f"  Using cached Binance data for {symbol} ({len(cached)} bars)")
                return cached

            print(f"  WARNING: Falling back to Yahoo for {symbol}")

    # ── Yahoo Finance: fallback for non-premium symbols only ──
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
