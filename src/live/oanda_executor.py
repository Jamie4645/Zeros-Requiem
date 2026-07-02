"""
SBRS 2.0 — OANDA v20 Order Execution (Multi-Instrument)

Handles all broker operations for Gold, Forex, and Index CFDs:
- Place market orders with SL/TP
- Modify stop loss (breakeven, trailing)
- Close positions
- Sync open positions with broker
- Fetch current price

Supports: XAU_USD, GBP_USD, EUR_USD, USD_JPY, DE30_EUR, NAS100_USD, etc.
Uses the same credentials and API as oanda_fetcher.py.
"""

import os
import time
import requests
from typing import Optional, Dict, List, Tuple
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

OANDA_API_KEY = os.getenv('OANDA_API_KEY', '')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID', '')
OANDA_ENV = os.getenv('OANDA_ENVIRONMENT', 'practice')

OANDA_URLS = {
    'practice': 'https://api-fxpractice.oanda.com',
    'live': 'https://api-fxtrade.oanda.com',
}
BASE_URL = OANDA_URLS.get(OANDA_ENV, OANDA_URLS['practice'])

DEFAULT_INSTRUMENT = 'XAU_USD'

INSTRUMENT_CONFIG = {
    'XAU_USD':    {'decimals': 2, 'unit_type': 'int'},
    'GBP_USD':    {'decimals': 5, 'unit_type': 'int'},
    'EUR_USD':    {'decimals': 5, 'unit_type': 'int'},
    'USD_JPY':    {'decimals': 3, 'unit_type': 'int'},
    'AUD_USD':    {'decimals': 5, 'unit_type': 'int'},
    'DE30_EUR':   {'decimals': 1, 'unit_type': 'decimal'},
    'NAS100_USD': {'decimals': 1, 'unit_type': 'decimal'},
    'SPX500_USD': {'decimals': 1, 'unit_type': 'decimal'},
}


def _headers() -> dict:
    return {
        'Authorization': f'Bearer {OANDA_API_KEY}',
        'Content-Type': 'application/json',
    }


def _account_url() -> str:
    return f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}"


def _format_price(price: float, instrument: str) -> str:
    """Format a price with the correct number of decimals for the instrument."""
    decimals = INSTRUMENT_CONFIG.get(instrument, {}).get('decimals', 2)
    return f"{price:.{decimals}f}"


def _format_units(units: float, instrument: str) -> str:
    """Format units as string — integer for most, decimal for index CFDs."""
    unit_type = INSTRUMENT_CONFIG.get(instrument, {}).get('unit_type', 'int')
    if unit_type == 'decimal':
        return f"{units:.2f}"
    return str(int(units))


# ── Price ─────────────────────────────────────────────────────

def get_current_price(instrument: str = DEFAULT_INSTRUMENT) -> Optional[Tuple[float, float, float]]:
    """
    Get current bid/ask/mid price for an instrument.

    Returns:
        (bid, ask, mid) or None if failed
    """
    try:
        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/pricing"
        params = {'instruments': instrument}
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        prices = data.get('prices', [])
        if prices:
            p = prices[0]
            bid = float(p['bids'][0]['price'])
            ask = float(p['asks'][0]['price'])
            mid = (bid + ask) / 2
            return (bid, ask, mid)
    except Exception as e:
        print(f"  Error getting price for {instrument}: {e}")
    return None


# ── Account ───────────────────────────────────────────────────

def get_account_balance() -> Optional[float]:
    """Get current account balance."""
    try:
        url = f"{_account_url()}/summary"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return float(data['account']['balance'])
    except Exception as e:
        print(f"  Error getting balance: {e}")
    return None


def get_account_summary() -> Optional[Dict]:
    """Get account summary (balance, unrealizedPL, NAV, etc.)."""
    try:
        url = f"{_account_url()}/summary"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get('account', {})
    except Exception as e:
        print(f"  Error getting summary: {e}")
    return None


# ── Order Placement ───────────────────────────────────────────

# Populated by place_market_order() whenever OANDA returns an
# orderFillTransaction. Callers can read this right after the call to
# reconcile against the expected (modeled) entry. See src/live/slip_logger.py.
_last_fill_price: Optional[float] = None


def get_last_fill_price() -> Optional[float]:
    """Return the actual fill price from the most recent place_market_order call."""
    return _last_fill_price


def place_market_order(
    direction: str,
    units: float,
    stop_loss: float,
    take_profit: float,
    instrument: str = DEFAULT_INSTRUMENT
) -> Optional[str]:
    """
    Place a market order with SL and TP.

    Args:
        direction: 'long' or 'short'
        units: Number of units (positive)
        stop_loss: Stop loss price
        take_profit: Take profit price
        instrument: OANDA instrument name (e.g. 'XAU_USD', 'GBP_USD', 'DE30_EUR')

    Returns:
        OANDA trade ID if successful, None if failed
    """
    # Reset the module-level fill slot at entry so a failed/rejected order on
    # THIS call can never let the slip logger reconcile against a prior trade's
    # (possibly prior instrument's) fill price. See src/live/slip_logger.py.
    globals()['_last_fill_price'] = None

    signed_units = abs(units) if direction == 'long' else -abs(units)

    order_data = {
        'order': {
            'type': 'MARKET',
            'instrument': instrument,
            'units': _format_units(signed_units, instrument),
            'stopLossOnFill': {
                'price': _format_price(stop_loss, instrument),
            },
            'takeProfitOnFill': {
                'price': _format_price(take_profit, instrument),
            },
            'timeInForce': 'FOK',
        }
    }

    try:
        url = f"{_account_url()}/orders"
        resp = requests.post(url, headers=_headers(), json=order_data, timeout=15)
        resp.raise_for_status()

        data = resp.json()

        if 'orderFillTransaction' in data:
            fill = data['orderFillTransaction']
            trade_id = fill.get('tradeOpened', {}).get('tradeID', '')
            # Capture the fill price so the slip logger (Falsifier #1) can
            # reconcile against the modeled entry. Stored in a module-level
            # slot the runner reads after calling place_market_order().
            try:
                globals()['_last_fill_price'] = float(fill.get('price'))
            except (TypeError, ValueError):
                globals()['_last_fill_price'] = None
            if trade_id:
                return trade_id

        if 'orderRejectTransaction' in data:
            reject = data['orderRejectTransaction']
            reason = reject.get('rejectReason', 'unknown')
            print(f"  Order REJECTED on {instrument}: {reason}")
            return None

        if 'relatedTransactionIDs' in data:
            # Fill succeeded but the response did not inline orderFillTransaction.
            # Recover both the trade ID and the actual fill price from the open
            # trade so Falsifier #1 reconciliation stays correct for THIS symbol.
            trades = get_open_trades()
            if trades:
                latest = trades[-1]
                try:
                    globals()['_last_fill_price'] = float(latest.get('price'))
                except (TypeError, ValueError):
                    globals()['_last_fill_price'] = None
                return latest.get('id', None)
            return None

        print(f"  Unexpected order response for {instrument}: {data}")
        return None

    except Exception as e:
        print(f"  Error placing order on {instrument}: {e}")
    return None


# ── Trade Management ──────────────────────────────────────────

def modify_stop_loss(trade_id: str, new_sl: float, instrument: str = DEFAULT_INSTRUMENT) -> bool:
    """
    Modify the stop loss on an open trade.

    Args:
        trade_id: OANDA trade ID
        new_sl: New stop loss price
        instrument: For price formatting

    Returns:
        True if successful
    """
    try:
        url = f"{_account_url()}/trades/{trade_id}/orders"
        data = {
            'stopLoss': {
                'price': _format_price(new_sl, instrument),
            }
        }
        resp = requests.put(url, headers=_headers(), json=data, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"  Error modifying SL on trade {trade_id}: {e}")
    return False


def close_trade(trade_id: str) -> Optional[Dict]:
    """
    Close an open trade at market price.

    Returns:
        Close transaction details or None
    """
    try:
        url = f"{_account_url()}/trades/{trade_id}/close"
        resp = requests.put(url, headers=_headers(), json={}, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        if 'orderFillTransaction' in data:
            fill = data['orderFillTransaction']
            return {
                'price': float(fill.get('price', 0)),
                'pnl': float(fill.get('pl', 0)),
                'trade_id': trade_id,
            }
        return data
    except Exception as e:
        print(f"  Error closing trade {trade_id}: {e}")
    return None


# ── Position Sync ─────────────────────────────────────────────

def get_open_trades() -> List[Dict]:
    """Get all open trades on the account."""
    try:
        url = f"{_account_url()}/openTrades"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get('trades', [])
    except Exception as e:
        print(f"  Error getting open trades: {e}")
    return []


def get_trade_details(trade_id: str) -> Optional[Dict]:
    """Get details for a specific trade."""
    try:
        url = f"{_account_url()}/trades/{trade_id}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        return resp.json().get('trade', None)
    except Exception as e:
        print(f"  Error getting trade {trade_id}: {e}")
    return None


def get_closed_trade_details(trade_id: str) -> Optional[Dict]:
    """
    Look up a closed trade's actual exit price, P&L, and close reason
    from OANDA's transaction history. Retries on transient API errors.
    """
    last_err: Optional[Exception] = None
    for attempt in range(3):
        try:
            url = f"{_account_url()}/trades/{trade_id}"
            resp = requests.get(url, headers=_headers(), timeout=10)
            resp.raise_for_status()
            trade = resp.json().get('trade', {})

            if trade.get('state') != 'CLOSED':
                return None

            pnl = float(trade.get('realizedPL', 0))
            close_price = float(trade.get('averageClosePrice', 0))

            close_reason = 'unknown'
            closing_ids = trade.get('closingTransactionIDs', [])
            if closing_ids:
                last_close_id = closing_ids[-1]
                tx_url = f"{_account_url()}/transactions/{last_close_id}"
                tx_resp = requests.get(tx_url, headers=_headers(), timeout=10)
                if tx_resp.status_code == 200:
                    tx = tx_resp.json().get('transaction', {})
                    tx_type = tx.get('type', '')
                    tx_reason = tx.get('reason', '')

                    if tx_reason == 'STOP_LOSS_ORDER':
                        close_reason = 'stop_loss'
                    elif tx_reason == 'TAKE_PROFIT_ORDER':
                        close_reason = 'take_profit'
                    elif tx_reason == 'TRAILING_STOP_LOSS_ORDER':
                        close_reason = 'trailing_stop'
                    elif tx_type == 'ORDER_FILL':
                        close_reason = tx_reason.lower() if tx_reason else 'broker_fill'
                    else:
                        close_reason = f"{tx_type}_{tx_reason}".lower().strip('_')

            return {
                'exit_price': close_price,
                'pnl': pnl,
                'close_reason': close_reason,
            }
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.4 * (attempt + 1))
    if last_err:
        print(f"  Error getting closed trade details for {trade_id}: {last_err}")
    return None


def sync_positions(state_trades: List[Dict]) -> List[Dict]:
    """
    Sync local state with broker positions.
    Returns list of trades closed on broker side (TP/SL hit between runs).
    """
    broker_trades = get_open_trades()
    broker_ids = {t['id'] for t in broker_trades}

    closed_on_broker = []
    for st in state_trades:
        oanda_id = st.get('oanda_trade_id', '')
        if oanda_id and oanda_id not in broker_ids:
            details = get_closed_trade_details(oanda_id)
            if not details:
                # Trade closed on broker but API did not return fill details — do not
                # treat as closed with $0 PnL (would corrupt equity and history).
                print(
                    f"  sync_positions: trade {oanda_id} missing close details — "
                    "skipping local close; retry next run"
                )
                continue
            st['_broker_exit_price'] = details['exit_price']
            st['_broker_pnl'] = details['pnl']
            st['_broker_close_reason'] = details['close_reason']
            closed_on_broker.append(st)

    return closed_on_broker


def is_connected() -> bool:
    """Check if we can reach the OANDA API."""
    try:
        url = f"{_account_url()}/summary"
        resp = requests.get(url, headers=_headers(), timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
