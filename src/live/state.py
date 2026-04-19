"""
SBRS 2.0 — State Persistence (Multi-Symbol)

Saves and loads algo state between hourly runs:
- Pending setups per symbol (structure breaks waiting for retest)
- Open trades per symbol (positions being managed)
- Trade history (completed trades for tracking)
- Daily P&L tracking
- Portfolio-level risk tracking

State is stored as JSON per symbol: state/sbrs_state_{symbol_key}.json
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict


STATE_DIR = Path(__file__).resolve().parent.parent.parent / 'state'
DB_PATH = Path(__file__).resolve().parent.parent.parent / 'data' / 'zeros_requiem.db'


def _state_file_for_symbol(symbol_key: str) -> Path:
    """Get the state file path for a given symbol key."""
    safe = symbol_key.replace('^', '').replace('=', '').replace('/', '').replace('-', '')
    return STATE_DIR / f'sbrs_state_{safe}.json'


@dataclass
class LivePendingSetup:
    """A structure break waiting for retest — persisted between runs."""
    direction: str
    broken_level: float
    break_bar_time: str
    bars_waiting: int = 0
    created_at: str = ""
    is_counter_trend: bool = False
    confluence_score: float = 0.0
    level_touches: int = 0
    in_squeeze: bool = False
    breakout_attempt: int = 1
    false_breakout_at_level: bool = False


@dataclass
class LiveTrade:
    """An open or completed trade — persisted between runs."""
    trade_id: str
    oanda_trade_id: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    original_sl: float
    position_size: float
    entry_time: str
    entry_bar_index: int
    regime: str               # 'sbrs_v2_gold', 'sbrs_v2_indices', 'sbrs_v2_forex'
    status: str               # 'open', 'closed_tp', 'closed_sl', 'closed_managed'
    symbol: str = "GC=F"
    asset_class: str = "gold"
    confluence_score: float = 0.0
    is_counter_trend: bool = False
    stop_moved_to_be: bool = False
    exit_price: float = 0.0
    exit_time: str = ""
    exit_reason: str = ""
    pnl: float = 0.0
    bars_held: int = 0


@dataclass
class AlgoState:
    """Per-symbol algo state — serialized to JSON between runs."""
    strategy: str = "SBRS 2.0"
    strategy_version: str = "2.0"
    symbol: str = "GC=F"
    instrument: str = "XAU_USD"
    asset_class: str = "gold"
    interval: str = "1h"

    initial_capital: float = 10000.0
    current_capital: float = 10000.0
    peak_equity: float = 10000.0

    daily_start_capital: float = 10000.0
    daily_pnl: float = 0.0
    current_date: str = ""

    pending_setups: List[Dict] = field(default_factory=list)
    open_trades: List[Dict] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)

    total_trades: int = 0
    total_wins: int = 0
    total_losses: int = 0
    bars_processed: int = 0
    last_bar_time: str = ""
    last_run_time: str = ""

    paused: bool = False
    pause_reason: str = ""


def load_state(symbol_key: str = 'GCF') -> AlgoState:
    """Load state from JSON file for a given symbol. Returns fresh state if missing."""
    state_file = _state_file_for_symbol(symbol_key)

    # Migrate: if old single-file state exists and no per-symbol file, use it
    old_file = STATE_DIR / 'sbrs_state.json'
    if not state_file.exists() and old_file.exists() and symbol_key == 'GCF':
        state_file = old_file

    if not state_file.exists():
        return AlgoState()

    try:
        with open(state_file, 'r') as f:
            data = json.load(f)

        state = AlgoState()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)

        # Ensure v2 fields exist
        if state.strategy_version == "":
            state.strategy_version = "2.0"
        if state.strategy == "SBRS 1.1":
            state.strategy = "SBRS 2.0"

        return state
    except (json.JSONDecodeError, Exception) as e:
        print(f"  WARNING: Failed to load state for {symbol_key}: {e}. Starting fresh.")
        if state_file.exists():
            backup = state_file.with_suffix('.json.bak')
            state_file.rename(backup)
        return AlgoState()


def save_state(state: AlgoState, symbol_key: str = 'GCF') -> None:
    """Save state to JSON file for a given symbol (atomic replace)."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state.last_run_time = datetime.utcnow().isoformat() + 'Z'
    data = asdict(state)
    state_file = _state_file_for_symbol(symbol_key)
    fd, tmp_path = tempfile.mkstemp(suffix='.tmp', dir=STATE_DIR, text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, state_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def reset_daily_if_needed(state: AlgoState) -> bool:
    """Reset daily P&L tracking if it's a new day."""
    today = date.today().isoformat()
    if state.current_date != today:
        state.current_date = today
        state.daily_start_capital = state.current_capital
        state.daily_pnl = 0.0
        return True
    return False


def add_pending_setup(state: AlgoState, setup: LivePendingSetup) -> None:
    state.pending_setups.append(asdict(setup))


def remove_pending_setup(state: AlgoState, index: int) -> None:
    if 0 <= index < len(state.pending_setups):
        state.pending_setups.pop(index)


def add_open_trade(state: AlgoState, trade: LiveTrade) -> None:
    state.open_trades.append(asdict(trade))
    state.total_trades += 1


def _write_trade_to_sqlite(trade: Dict, strategy: str = 'SBRS 2.0',
                           symbol: str = 'GC=F') -> None:
    """Write a closed trade to SQLite database (best-effort)."""
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5)
        entry = trade.get('entry_price', 0)
        original_sl = trade.get('original_sl', 0)
        exit_price = trade.get('exit_price', 0)
        direction = trade.get('direction', 'long')
        initial_risk = abs(entry - original_sl)
        r_mult = 0.0
        if initial_risk > 0:
            profit = (exit_price - entry) if direction == 'long' else (entry - exit_price)
            r_mult = profit / initial_risk

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
            trade.get('regime', 'sbrs_v2_gold'),
            trade.get('status', 'closed'),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


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

            _write_trade_to_sqlite(t, state.strategy, state.symbol)
            return t
    return None


def generate_trade_id() -> str:
    return f"SBRS_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
