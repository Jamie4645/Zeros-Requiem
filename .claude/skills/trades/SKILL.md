---
name: trades
description: Query and analyze trade history from the SQLite database
user_invocable: true
---

# /trades — Trade History Analysis

Query the SBRS trade database at `data/zeros_requiem.db` using the SQLite MCP server.

## Usage

When the user invokes `/trades`, use the SQLite MCP tools to query the database and present results.

## Common Queries

### Overview
```sql
SELECT COUNT(*) as total_trades,
       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
       SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
       ROUND(SUM(CASE WHEN pnl > 0 THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1) as win_rate,
       ROUND(SUM(pnl), 2) as total_pnl,
       ROUND(AVG(r_multiple), 2) as avg_r
FROM trades;
```

### By Exit Reason
```sql
SELECT exit_reason, COUNT(*) as count,
       ROUND(SUM(pnl), 2) as total_pnl,
       ROUND(AVG(pnl), 2) as avg_pnl
FROM trades GROUP BY exit_reason ORDER BY count DESC;
```

### Recent Trades
```sql
SELECT trade_id, direction, entry_price, exit_price,
       ROUND(pnl, 2) as pnl, ROUND(r_multiple, 2) as r_mult,
       exit_reason, bars_held
FROM trades ORDER BY entry_time DESC LIMIT 10;
```

### Losing Trades Analysis
```sql
SELECT trade_id, direction, entry_price, exit_price,
       ROUND(pnl, 2) as pnl, exit_reason, bars_held,
       stop_moved_to_be
FROM trades WHERE pnl <= 0 ORDER BY pnl ASC;
```

### Daily P&L
```sql
SELECT date(entry_time) as day, COUNT(*) as trades,
       ROUND(SUM(pnl), 2) as daily_pnl
FROM trades GROUP BY day ORDER BY day;
```

## Presentation

- Format results as markdown tables
- Highlight key metrics: win rate, profit factor, average R-multiple
- Flag any trades with $0 PnL (indicates broker_closed bug — may need manual correction)
- Compare to elite benchmarks from CLAUDE.md (Sharpe >= 1.5, PF >= 1.5, WR ~43%)

## If Arguments Provided

The user may specify what they want to see:
- `/trades` — show overview + recent trades
- `/trades losers` — show all losing trades sorted by PnL
- `/trades by-reason` — group by exit reason
- `/trades by-day` — daily P&L breakdown
- `/trades <trade_id>` — show details for a specific trade
