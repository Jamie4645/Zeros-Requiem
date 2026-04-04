# Pipeline Documentation

#trading #pipeline #docs

## How It Works (Simple Version)

1. **You drop PDFs** into `strategy_pipeline/books/`
2. **Claude Code reads each book** — extracts text AND reads charts/diagrams as images
   - Finds every strategy: entry rules, exit rules, risk management
   - Tags which markets and timeframes each strategy works for
   - Scores how clear and complete each strategy is
3. **Claude Code compares notes across all books**
   - Clusters similar strategies (even if named differently by different authors)
   - Ranks by how many books mention the same idea (more books = battle-tested)
   - Flags contradictions between authors
4. **Claude Code writes Python code** for each strategy cluster
   - Each file has `entry_signal()`, `exit_signal()`, `position_size()`
   - Plug directly into the backtester
5. **Obsidian notes are created** with links connecting everything

No API key needed — Claude Code does all the analysis directly through your Pro subscription.

## How to Run

Tell Claude Code:
```
Read all the PDFs in strategy_pipeline/books/ one at a time. For each book:
1. Use the pdf_parser to extract text
2. Use the image_encoder to rasterize chart pages
3. Analyse every page and extract ALL trading strategies
4. Save the analysis as JSON in output/book_analyses/
5. Create an Obsidian note in obsidian/Book Analyses/

After all books are done:
6. Compare all analyses — find overlaps, clusters, contradictions
7. Save comparison as JSON in output/comparisons/
8. Generate Python strategy files in output/strategies/
9. Create Obsidian notes for each strategy cluster
10. Update the Master Report and Strategy Comparison Overview
```

## Backtesting a Strategy

```bash
python -m strategy_pipeline.backtesting.bt_runner \
    --strategy strategy_pipeline/output/strategies/strategy_001_xxx.py \
    --data your_data.csv \
    --capital 100000 --risk 0.01
```

## What Each Output Folder Contains

| Folder | What's In It |
|--------|-------------|
| `output/strategies/` | One `.py` file per strategy — plug into backtester |
| `output/comparisons/` | JSON showing how strategies overlap across books |
| `output/book_analyses/` | Full JSON analysis of each book |
| `output/reports/` | Master report in markdown |
| `obsidian/` | All the linked notes for your vault |

## Related Project Notes
- [[00-MOC-Zeros-Requiem]] — Main project map of content
- [[19-Priority-1-Signal-Generation]] — SBRS signal generation context
- [[46-SBRS-Parameters-Reference]] — SBRS parameters (for comparison with book strategies)
- [[Pipeline Instructions v2]] — Full original instructions for this pipeline

## Links

- [[Strategy Comparison Overview]]
- [[Master Report]]
