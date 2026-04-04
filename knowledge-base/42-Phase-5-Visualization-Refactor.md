---
tags: [phase-5, visualization, charts, skill]
aliases: [Phase 5, Visualization, Charts]
---

# Phase 5 — Visualization Refactor + `/chart` Skill

> 3 chart scripts in `tests/` consolidated into `src/visualization/charts.py` with a `/chart` slash command.

---

## Module: `src/visualization/charts.py`

| Function | Output | Input |
|----------|--------|-------|
| `plot_equity_curve()` | Equity + drawdown overlay | Equity values list |
| `plot_trades_on_price()` | Trade markers on price chart | DataFrame + BacktestTrade list |
| `plot_session_heatmap()` | P&L by hour-of-day | Trade dicts with entry_time, pnl |
| `plot_r_distribution()` | R-multiple histogram | Trade dicts with entry/exit/sl |

All functions:
- Save to `charts/` directory as PNG (150 DPI)
- Accept optional `save_path` override
- Return the file path

---

## `/chart` Skill

```
/chart equity       — equity curve from backtest
/chart trades       — trade map on price
/chart session      — session P&L heatmap
/chart r-dist       — R-multiple distribution
/chart all          — generate all four
```

---

## Original Chart Scripts (Kept)

The original scripts in `tests/` remain for backward compatibility:
- `tests/chart_trades.py` — detailed trade visualization
- `tests/chart_candles.py` — candlestick close-ups
- `tests/chart_full_candles.py` — full candle rendering

---

## Related

- [[31-Tool-Backtest]] — backtest skill (provides data for charts)
- [[00-MOC-Zeros-Requiem]]
