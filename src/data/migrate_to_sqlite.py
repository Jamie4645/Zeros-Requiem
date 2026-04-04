"""
Migrate trade history from sbrs_state.json to SQLite database.

Creates the database schema and inserts all existing trades.
Safe to run multiple times — skips existing trades by trade_id.

Run: py -m src.data.migrate_to_sqlite
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = PROJECT_ROOT / 'state' / 'sbrs_state.json'
DB_PATH = PROJECT_ROOT / 'data' / 'zeros_requiem.db'


def create_schema(conn: sqlite3.Connection) -> None:
    """Create database tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT UNIQUE NOT NULL,
            oanda_trade_id TEXT,
            strategy TEXT NOT NULL DEFAULT 'SBRS 1.1',
            symbol TEXT NOT NULL DEFAULT 'GC=F',
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL DEFAULT 0.0,
            stop_loss REAL,
            take_profit REAL,
            original_sl REAL,
            position_size REAL,
            entry_time TEXT,
            exit_time TEXT,
            exit_reason TEXT,
            pnl REAL DEFAULT 0.0,
            r_multiple REAL DEFAULT 0.0,
            bars_held INTEGER DEFAULT 0,
            stop_moved_to_be INTEGER DEFAULT 0,
            regime TEXT DEFAULT 'sbrs_gold',
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            framework TEXT NOT NULL,
            symbol TEXT,
            interval TEXT,
            status TEXT DEFAULT 'testing',
            sharpe REAL,
            profit_factor REAL,
            walk_forward_consistency REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS backtest_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER REFERENCES strategies(id),
            run_date TEXT DEFAULT CURRENT_TIMESTAMP,
            period TEXT,
            total_trades INTEGER,
            win_rate REAL,
            total_pnl REAL,
            sharpe REAL,
            profit_factor REAL,
            max_drawdown REAL,
            consistency REAL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            strategy TEXT DEFAULT 'SBRS 1.1',
            equity REAL,
            drawdown_pct REAL,
            daily_pnl REAL,
            trades_today INTEGER DEFAULT 0,
            UNIQUE(date, strategy)
        );

        CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
        CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
        CREATE INDEX IF NOT EXISTS idx_trades_exit_reason ON trades(exit_reason);
        CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
        CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(date);
    """)


def compute_r_multiple(trade: dict) -> float:
    """Compute R-multiple for a trade."""
    entry = trade.get('entry_price', 0)
    original_sl = trade.get('original_sl', 0)
    exit_price = trade.get('exit_price', 0)
    direction = trade.get('direction', 'long')

    initial_risk = abs(entry - original_sl)
    if initial_risk <= 0:
        return 0.0

    if direction == 'long':
        profit = exit_price - entry
    else:
        profit = entry - exit_price

    return profit / initial_risk


def migrate_trades(conn: sqlite3.Connection, state: dict) -> int:
    """Insert trades from state JSON into SQLite. Returns count of new trades."""
    trades = state.get('trade_history', [])
    inserted = 0

    for t in trades:
        trade_id = t.get('trade_id', '')
        if not trade_id:
            continue

        # Skip if already exists
        existing = conn.execute(
            "SELECT 1 FROM trades WHERE trade_id = ?", (trade_id,)
        ).fetchone()
        if existing:
            continue

        r_mult = compute_r_multiple(t)

        conn.execute("""
            INSERT INTO trades (
                trade_id, oanda_trade_id, strategy, symbol, direction,
                entry_price, exit_price, stop_loss, take_profit, original_sl,
                position_size, entry_time, exit_time, exit_reason, pnl,
                r_multiple, bars_held, stop_moved_to_be, regime, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id,
            t.get('oanda_trade_id', ''),
            state.get('strategy', 'SBRS 1.1'),
            state.get('symbol', 'GC=F'),
            t.get('direction', ''),
            t.get('entry_price', 0),
            t.get('exit_price', 0),
            t.get('stop_loss', 0),
            t.get('take_profit', 0),
            t.get('original_sl', 0),
            t.get('position_size', 0),
            t.get('entry_time', ''),
            t.get('exit_time', ''),
            t.get('exit_reason', ''),
            t.get('pnl', 0),
            r_mult,
            t.get('bars_held', 0),
            1 if t.get('stop_moved_to_be', False) else 0,
            t.get('regime', 'sbrs_gold'),
            t.get('status', 'closed'),
        ))
        inserted += 1

    return inserted


def seed_strategies(conn: sqlite3.Connection) -> None:
    """Insert known strategies."""
    strategies = [
        ('SBRS 1.1 Gold 1H', 'SBRS', 'GC=F', '1h', 'live_paper', 0.90, 1.26, 0.75),
        ('SBRS 1.1 S&P 500 1H', 'SBRS', '^GSPC', '1h', 'testing', None, 1.52, None),
        ('SBRS 1.1 NASDAQ 1H', 'SBRS', '^IXIC', '1h', 'testing', None, 1.65, None),
        ('SBRS 1.1 DAX 1H', 'SBRS', '^GDAXI', '1h', 'testing', None, 1.64, None),
    ]
    for name, framework, symbol, interval, status, sharpe, pf, wf in strategies:
        conn.execute("""
            INSERT OR IGNORE INTO strategies
            (name, framework, symbol, interval, status, sharpe, profit_factor, walk_forward_consistency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, framework, symbol, interval, status, sharpe, pf, wf))


def main():
    print(f"Database path: {DB_PATH}")
    print(f"State file: {STATE_FILE}")

    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load state
    if not STATE_FILE.exists():
        print("ERROR: State file not found. Nothing to migrate.")
        return

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    print(f"Found {len(state.get('trade_history', []))} trades in state file")

    # Connect and migrate
    conn = sqlite3.connect(str(DB_PATH))
    try:
        create_schema(conn)
        print("Schema created/verified")

        count = migrate_trades(conn, state)
        print(f"Inserted {count} new trades")

        seed_strategies(conn)
        print("Strategies seeded")

        conn.commit()

        # Verify
        total = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        print(f"\nVerification:")
        print(f"  Total trades in DB: {total}")

        reasons = conn.execute(
            "SELECT exit_reason, COUNT(*) FROM trades GROUP BY exit_reason"
        ).fetchall()
        for reason, cnt in reasons:
            print(f"  {reason}: {cnt}")

        strats = conn.execute("SELECT name, status FROM strategies").fetchall()
        print(f"\n  Strategies:")
        for name, status in strats:
            print(f"    {name}: {status}")

    finally:
        conn.close()

    print(f"\nMigration complete. DB at: {DB_PATH}")


if __name__ == '__main__':
    main()
