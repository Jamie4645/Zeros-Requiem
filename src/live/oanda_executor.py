"""
SBRS 1.1 — OANDA v20 Order Execution

Handles all broker operations:
- Place market orders with SL/TP
- Modify stop loss (breakeven, trailing)
- Close positions
- Sync open positions with broker
- Fetch current price

Uses the same credentials and API as oanda_fetcher.py.
"""

import os
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

INSTRUMENT = 'XAU_USD'  # Gold


def _headers() -> dict:
    return {
        'Authorization': f'Bearer {OANDA_API_KEY}',
        'Content-Type': 'application/json',
    }


def _account_url() -> str:
    return f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}"


# ── Price ─────────────────────────────────────────────────────

def get_current_price() -> Optional[Tuple[float, float, float]]:
    """
    Get current bid/ask/mid price for Gold.
    
    Returns:
        (bid, ask, mid) or None if failed
    """
    try:
        url = f"{BASE_URL}/v3/accounts/{OANDA_ACCOUNT_ID}/pricing"
        params = {'instruments': INSTRUMENT}
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
        print(f"  Error getting price: {e}")
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

def place_market_order(
    direction: str,
    units: float,
    stop_loss: float,
    take_profit: float
) -> Optional[str]:
    """
    Place a market order on Gold with SL and TP.
    
    Args:
        direction: 'long' or 'short'
        units: Number of units (positive for long, negative for short)
        stop_loss: Stop loss price
        take_profit: Take profit price
    
    Returns:
        OANDA trade ID if successful, None if failed
    """
    # OANDA uses positive units for buy, negative for sell
    signed_units = abs(units) if direction == 'long' else -abs(units)
    
    order_data = {
        'order': {
            'type': 'MARKET',
            'instrument': INSTRUMENT,
            'units': str(int(signed_units)),  # OANDA expects string, integer units for Gold
            'stopLossOnFill': {
                'price': f"{stop_loss:.2f}",  # Gold uses 2 decimal places
            },
            'takeProfitOnFill': {
                'price': f"{take_profit:.2f}",
            },
            'timeInForce': 'FOK',  # Fill or Kill
        }
    }
    
    try:
        url = f"{_account_url()}/orders"
        resp = requests.post(url, headers=_headers(), json=order_data, timeout=15)
        resp.raise_for_status()
        
        data = resp.json()
        
        # Check if order was filled
        if 'orderFillTransaction' in data:
            fill = data['orderFillTransaction']
            trade_id = fill.get('tradeOpened', {}).get('tradeID', '')
            if trade_id:
                return trade_id
        
        # Check for rejection
        if 'orderRejectTransaction' in data:
            reject = data['orderRejectTransaction']
            reason = reject.get('rejectReason', 'unknown')
            print(f"  Order REJECTED: {reason}")
            return None
        
        # Fallback: try to extract trade ID from response
        if 'relatedTransactionIDs' in data:
            # Get the most recent trade from open trades
            return _get_latest_trade_id()
        
        print(f"  Unexpected order response: {data}")
        return None
        
    except Exception as e:
        print(f"  Error placing order: {e}")
    return None


def _get_latest_trade_id() -> Optional[str]:
    """Get the most recent open trade ID."""
    trades = get_open_trades()
    if trades:
        return trades[-1].get('id', None)
    return None


# ── Trade Management ──────────────────────────────────────────

def modify_stop_loss(trade_id: str, new_sl: float) -> bool:
    """
    Modify the stop loss on an open trade.
    
    Args:
        trade_id: OANDA trade ID
        new_sl: New stop loss price
    
    Returns:
        True if successful
    """
    try:
        url = f"{_account_url()}/trades/{trade_id}/orders"
        data = {
            'stopLoss': {
                'price': f"{new_sl:.2f}",
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
    
    Args:
        trade_id: OANDA trade ID
    
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
    """
    Get all open trades on the account.
    
    Returns:
        List of trade dicts with id, instrument, currentUnits, price, 
        stopLossOrder, takeProfitOrder, unrealizedPL
    """
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
    from OANDA's transaction history.

    Returns:
        Dict with 'exit_price', 'pnl', 'close_reason' or None if not found
    """
    try:
        # First try getting the trade directly — OANDA keeps closed trades
        url = f"{_account_url()}/trades/{trade_id}"
        resp = requests.get(url, headers=_headers(), timeout=10)
        resp.raise_for_status()
        trade = resp.json().get('trade', {})

        if trade.get('state') == 'CLOSED':
            pnl = float(trade.get('realizedPL', 0))
            close_price = float(trade.get('averageClosePrice', 0))

            # Determine close reason from closing transaction
            close_reason = 'unknown'
            closing_ids = trade.get('closingTransactionIDs', [])
            if closing_ids:
                # Look up the closing transaction to determine reason
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
        print(f"  Error getting closed trade details for {trade_id}: {e}")
    return None


def sync_positions(state_trades: List[Dict]) -> List[Dict]:
    """
    Sync local state with broker positions.

    Checks if trades we think are open are still open on the broker.
    Returns list of trades that were closed on the broker side
    (TP/SL hit between runs), enriched with actual exit price and P&L.
    """
    broker_trades = get_open_trades()
    broker_ids = {t['id'] for t in broker_trades}

    closed_on_broker = []
    for st in state_trades:
        oanda_id = st.get('oanda_trade_id', '')
        if oanda_id and oanda_id not in broker_ids:
            # Trade was closed on broker (TP/SL hit between runs)
            # Look up actual exit details from OANDA
            details = get_closed_trade_details(oanda_id)
            if details:
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
