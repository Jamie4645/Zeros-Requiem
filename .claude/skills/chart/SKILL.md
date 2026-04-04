---
name: chart
description: Generate charts for SBRS backtest and trade analysis
user_invocable: true
---

# /chart — Generate Analysis Charts

Generate charts using `src/visualization/charts.py`. Charts are saved to the `charts/` directory.

## Usage

When the user invokes `/chart`, determine what chart they want and generate it.

## Available Charts

### 1. Equity Curve
```python
from src.visualization.charts import plot_equity_curve
path = plot_equity_curve(equity_values, trade_dates, title="SBRS Gold 1H Equity")
```

### 2. Trade Map (entries/exits on price)
```python
from src.visualization.charts import plot_trades_on_price
path = plot_trades_on_price(df, trades, title="SBRS Gold 1H Trades")
```
Requires running a backtest first to get `df` and `trades`.

### 3. Session Heatmap (P&L by hour)
```python
from src.visualization.charts import plot_session_heatmap
path = plot_session_heatmap(trade_dicts, title="Gold Session Analysis")
```
`trade_dicts` is a list of dicts with `entry_time` and `pnl` keys.

### 4. R-Multiple Distribution
```python
from src.visualization.charts import plot_r_distribution
path = plot_r_distribution(trade_dicts, title="Gold R-Distribution")
```
`trade_dicts` needs `entry_price`, `exit_price`, `original_sl`, `direction`.

## Interpreting Arguments

- `/chart equity` or `/chart equity Gold 1H` — equity curve
- `/chart trades` or `/chart trade map` — trade map on price
- `/chart session` or `/chart heatmap` — session P&L heatmap
- `/chart r-dist` or `/chart distribution` — R-multiple histogram
- `/chart all` — generate all four charts

## Data Sources

For backtest charts, run a backtest first:
```python
from src.data.fetcher import fetch
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval

df = fetch("GC=F", "1h", "1y")
setups = analyze_gold_sbrs(df, 10000, 0.01, asset_class='gold')
sbrs_ind = get_sbrs_indicators(df)
risk_config = risk_config_for_interval("1h", 0.01)
result = run_backtest(df, setups, 10000, risk_config, apply_slippage=True, sbrs_indicators=sbrs_ind)
```

For live trade charts, query the SQLite database:
```python
import sqlite3
conn = sqlite3.connect('data/zeros_requiem.db')
trades = [dict(row) for row in conn.execute("SELECT * FROM trades").fetchall()]
```

## Output

After generating, tell the user the file path so they can view it.
Charts are saved as PNG at 150 DPI in the `charts/` directory.
