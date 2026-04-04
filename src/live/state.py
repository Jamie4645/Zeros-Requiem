"""
SBRS 1.1 — State Persistence

Saves and loads algo state between hourly runs:
- Pending setups (structure breaks waiting for retest)
- Open trades (positions being managed)
- Trade history (completed trades for tracking)
- Daily P&L tracking

State is stored as JSON in the project root (state/sbrs_state.json).
"""

import json
import os
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict


STATE_DIR = Path(__file__).resolve().parent.parent.parent / 'state'
STATE_FILE = STATE_DIR / 'sbrs_state.json'
DB_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'zeros_requiem.db'


@dataclass
class LivePendingSetup:
    """A structure break waiting for retest — persisted between runs."""
    direction: str           # 'long' or 'short'
    broken_level: float
    break_bar_time: str      # ISO timestamp of break bar
    bars_waiting: int = 0
    created_at: str = ""


@dataclass
class LiveTrade:
    """An open or completed trade — persisted between runs."""
    trade_id: str             # Unique ID (timestamp-based)
    oanda_trade_id: str       # OANDA's trade ID for API operations
    direction: str            # 'long' or 'short'
    entry_price: float
    stop_loss: float
    take_profit: float
    original_sl: float        # For R calculations (never changes)
    position_size: float      # Units
    entry_time: str           # ISO timestamp
    entry_bar_index: int      # Which bar we entered on (for timeout counting)
    regime: str               # 'sbrs_gold'
    status: str               # 'open', 'closed_tp', 'closed_sl', 'closed_managed'
    stop_moved_to_be: bool = False
    exit_price: float = 0.0
    exit_time: str = ""
    exit_reason: str = ""
    pnl: float = 0.0
    bars_held: int = 0


@dataclass
class AlgoState:
    """Complete algo state — serialized to JSON between runs."""
    # Strategy info
    strategy: str = "SBRS 1.1"
    symbol: str = "GC=F"
    instrument: str = "XAU_USD"
    interval: str = "1h"
    
    # Capital tracking
    initial_capital: float = 10000.0
    current_capital: float = 10000.0
    peak_equity: float = 10000.0
    
    # Daily tracking
    daily_start_capital: float = 10000.0
    daily_pnl: float = 0.0
    current_date: str = ""
    
    # State
    pending_setups: List[Dict] = field(default_factory=list)
    open_trades: List[Dict] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)
    
    # Counters
    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    bars_processed: int = 0
    last_bar_time: str = ""
    last_run_time: str = ""
    
    # Risk state
    paused: bool = False
    pause_reason: str = ""


def load_state() -> AlgoState:
    """Load state from JSON file. Returns fresh state if file doesn't exist."""
    if not STATE_FILE.exists():
        return AlgoState()
    
    try:
        with open(STATE_FILE, 'r') as f:
            data = json.load(f)
        
        state = AlgoState()
        # Populate from JSON, keeping defaults for missing fields
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        return state
    except (json.JSONDecodeError, Exception) as e:
        print(f"  WARNING: Failed to load state: {e}. Starting fresh.")
        # Backup corrupted file
        if STATE_FILE.exists():
            backup = STATE_FILE.with_suffix('.json.bak')
            STATE_FILE.rename(backup)
        return AlgoState()


def save_state(state: AlgoState) -> None:
    """Save state to JSON file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    state.last_run_time = datetime.utcnow().isoformat() + 'Z'
    
    data = asdict(state)
    
    with open(STATE_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def reset_daily_if_needed(state: AlgoState) -> bool:
    """Reset daily P&L tracking if it's a new day. Returns True if reset occurred."""
    today = date.today().isoformat()
    if state.current_date != today:
        state.current_date = today
        state.daily_start_capital = state.current_capital
        state.daily_pnl = 0.0
        return True
    return False


def add_pending_setup(state: AlgoState, setup: LivePendingSetup) -> None:
    """Add a pending setup to state."""
    state.pending_setups.append(asdict(setup))


def remove_pending_setup(state: AlgoState, index: int) -> None:
    """Remove a pending setup by index."""
    if 0 <= index < len(state.pending_setups):
        state.pending_setups.pop(index)


def add_open_trade(state: AlgoState, trade: LiveTrade) -> None:
    """Add an open trade to state."""
    state.open_trades.append(asdict(trade))
    state.total_trades += 1


def _write_trade_to_sqlite(trade: Dict, strategy: str = 'SBRS 1.1',
                           symbol: str = 'GC=F') -> None:
    """Write a closed trade to SQLite database (best-effort, never blocks runner)."""
    if not DB_PATH.exists():
        return

    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        # Compute R-multiple
        entry = trade.get('entry_price', 0)
        original_sl = trade.get('original_sl', 0)
        exit_price = trade.get('exit_price', 0)
        direction = trade.get('direction', 'long')
        initial_risk = abs(entry - original_sl)
        if initial_risk > 0:
            profit = (exit_price - entry) if direction == 'long' else (entry - exit_price)
            r_mult = profit / initial_risk
        else:
            r_mult = 0.0

        conn.execute("""
            INSERT OR IGNORE INTO trades (
                trade_id, oanda_trade_id, strategy, symbol, direction,
                entry_price, exit_price, stop_loss, take_profit, original_sl,
                position_size, entry_time, exit_time, exit_reason, pnl,
                r_multiple, bars_held, stop_moved_to_be, regime, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.get('trade_id', ''),
            trade.get('oanda_trade_id', ''),
            strategy,
            symbol,
            direction,
            entry,
            exit_price,
            trade.get('stop_loss', 0),
            trade.get('take_profit', 0),
            original_sl,
            trade.get('position_size', 0),
            trade.get('entry_time', ''),
            trade.get('exit_time', ''),
            trade.get('exit_reason', ''),
            trade.get('pnl', 0),
            r_mult,
            trade.get('bars_held', 0),
            1 if trade.get('stop_moved_to_be', False) else 0,
            trade.get('regime', 'sbrs_gold'),
            trade.get('status', 'closed'),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Never let DB errors block the runner


def close_trade(state: AlgoState, oanda_trade_id: str, exit_price: float,
                exit_reason: str, pnl: float) -> Optional[Dict]:
    """Close an open trade, move to history, and write to SQLite."""
    for i, t in enumerate(state.open_trades):
        if t['oanda_trade_id'] == oanda_trade_id:
            t['status'] = f'closed_{exit_reason}'
            t['exit_price'] = exit_price
            t['exit_time'] = datetime.utcnow().isoformat() + 'Z'
            t['exit_reason'] = exit_reason
            t['pnl'] = pnl

            state.trade_history.append(t)
            state.open_trades.pop(i)

            state.current_capital += pnl
            state.daily_pnl += pnl

            if pnl > 0:
                state.total_wins += 1
            else:
                state.total_losses += 1

            if state.current_capital > state.peak_equity:
                state.peak_equity = state.current_capital

            # Write to SQLite (best-effort)
            _write_trade_to_sqlite(t, state.strategy, state.symbol)

            return t
    return None


def generate_trade_id() -> str:
    """Generate a unique trade ID based on timestamp."""
    return f"SBRS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
