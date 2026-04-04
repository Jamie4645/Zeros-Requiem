---
tags: [phase-1, sqlite, database, mcp, trades]
aliases: [Phase 1, SQLite Database, Trade Database]
---

# Phase 1 — SQLite Trade Database

> JSON state won't scale past 500 trades across 5 strategies. SQLite + MCP lets Claude query trade history interactively.

---

## Architecture

```
state/sbrs_state.json  ←→  runner.py (fast hourly read/write)
                             ↓ on trade close
data/zeros_requiem.db  ←→  SQLite MCP (Claude interactive queries)
                             ↑ migration script
```

- **JSON state** remains the runner's primary state store (fast, simple, reliable)
- **SQLite** is the analytical store — written to on each trade close, queried by Claude via MCP
- **Migration script** seeds the DB from existing JSON state

---

## Schema

### `trades` table
Core trade data with R-multiple and OANDA trade ID for cross-referencing.

### `strategies` table
Strategy metadata (name, framework, status, metrics).

### `backtest_runs` table
Backtest results per strategy/period for walk-forward tracking.

### `daily_snapshots` table
Daily equity snapshots for drawdown tracking.

---

## MCP Configuration

Added `@anthropic/mcp-server-sqlite` to `.claude/settings.local.json`:
```json
"sqlite": {
  "command": "npx",
  "args": ["-y", "@anthropic/mcp-server-sqlite", "--db-path", "data/zeros_requiem.db"]
}
```

Requires restart of Claude Code session to activate.

---

## `/trades` Skill

Slash command for interactive trade analysis. Supports:
- `/trades` — overview + recent
- `/trades losers` — losing trades by PnL
- `/trades by-reason` — group by exit reason
- `/trades by-day` — daily P&L

---

## Files

| File | Action |
|------|--------|
| `.claude/settings.local.json` | Added SQLite MCP config |
| `src/data/migrate_to_sqlite.py` | New — migration script |
| `src/live/state.py` | Modified — writes to SQLite on `close_trade()` |
| `.claude/skills/trades/SKILL.md` | New — `/trades` slash command |
| `data/zeros_requiem.db` | New — SQLite database |

---

## Related

- [[37-Phase-0-Live-Runner-Bug-Fixes]] — fix data before storing it
- [[00-MOC-Zeros-Requiem]]
