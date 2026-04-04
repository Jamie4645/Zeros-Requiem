# Trading Strategy Extraction Pipeline

Multi-agent system where Claude Code reads trading books (PDFs), extracts every usable strategy, cross-compares them across books, and outputs backtestable Python code.

## How It Works

No API key needed — Claude Code does all the analysis directly through your Pro subscription.

1. Drop PDFs into `books/`
2. Tell Claude Code to process them (see instructions in `obsidian/Pipeline Documentation.md`)
3. Claude Code reads each book, extracts strategies, finds overlaps
4. Output: Python strategy files + Obsidian knowledge base

## Structure

```
strategy_pipeline/
├── books/               # Drop your PDFs here
├── ingestion/           # PDF parsing + image encoding tools
├── backtesting/         # Backtest runner for generated strategies
├── output/              # All pipeline outputs
│   ├── strategies/      # Backtestable Python files
│   ├── comparisons/     # Cross-book comparison JSON
│   ├── book_analyses/   # Per-book analysis JSON
│   └── reports/         # Master report
└── obsidian/            # Linked Obsidian notes
```

## Backtesting

```bash
python -m strategy_pipeline.backtesting.bt_runner \
    --strategy output/strategies/strategy_001.py \
    --data your_ohlcv_data.csv
```
