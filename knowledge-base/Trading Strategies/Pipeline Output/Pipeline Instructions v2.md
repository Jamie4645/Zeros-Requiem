# TRADING STRATEGY EXTRACTION PIPELINE — CLAUDE CODE INSTRUCTIONS

## IMPORTANT CONTEXT

I'm on the Claude Pro plan using Claude Code through my subscription. There is NO separate API key. You (Claude Code) ARE the analysis agent. Do NOT write code that calls the Anthropic API. Instead, YOU will read each book, analyse it, extract strategies, and write all the output files directly.

## WHAT I NEED YOU TO BUILD AND DO

This is a two-part job:
1. **BUILD** the folder structure, utility code, and Obsidian documentation
2. **RUN** the analysis on my trading books (I'll drop PDFs into the books folder)

---

## PART 1: BUILD THE INFRASTRUCTURE

### STEP 1: Create the folder structure

Create a subfolder called `strategy_pipeline` in the root of this repo:

```
strategy_pipeline/
├── books/                       # I will drop my PDFs here
├── ingestion/
│   ├── __init__.py
│   ├── pdf_parser.py            # Extracts text + detects chart pages from PDFs
│   └── image_encoder.py         # Rasterizes chart pages as images you can read
├── backtesting/
│   ├── __init__.py
│   └── bt_runner.py             # Lightweight backtester for generated strategies
├── output/
│   ├── strategies/              # One .py file per strategy (backtestable)
│   ├── comparisons/             # Cross-book comparison JSON
│   ├── book_analyses/           # Per-book analysis JSON
│   └── reports/                 # Master report markdown
├── obsidian/                    # Obsidian notes (copy these to my vault)
│   ├── Pipeline Documentation.md
│   ├── Strategy Comparison Overview.md
│   ├── Master Report.md
│   ├── Book Analyses/           # One note per book
│   └── Strategies/              # One note per strategy cluster
└── README.md
```

### STEP 2: Install dependencies

```bash
pip install pymupdf pillow pandas numpy
```

No `anthropic` package needed — you're doing the analysis directly.

### STEP 3: Create the utility code files

Create these files exactly as written. These are tools YOU will use to parse PDFs and that I will use to backtest strategies.

---

#### FILE: `strategy_pipeline/ingestion/__init__.py`
(empty file)

#### FILE: `strategy_pipeline/backtesting/__init__.py`
(empty file)

---

#### FILE: `strategy_pipeline/ingestion/pdf_parser.py`

```python
"""
PDF Parser — extracts text and detects visual/chart pages from trading book PDFs.
Used by Claude Code to read books page by page.
"""

import fitz  # PyMuPDF
import os
from pathlib import Path


class PDFParser:
    VISUAL_PAGE_TEXT_THRESHOLD = 100

    def parse(self, pdf_path: str) -> dict:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)

        metadata = {
            "title": doc.metadata.get("title", Path(pdf_path).stem),
            "author": doc.metadata.get("author", "Unknown"),
            "page_count": len(doc),
            "file_name": Path(pdf_path).name,
            "file_path": pdf_path,
        }

        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            word_count = len(text.split())
            image_list = page.get_images(full=True)
            is_visual = (
                len(image_list) > 0
                or len(text.strip()) < self.VISUAL_PAGE_TEXT_THRESHOLD
            )
            pages.append({
                "page_num": page_num + 1,
                "text": text,
                "is_visual": is_visual,
                "word_count": word_count,
                "image_count": len(image_list),
            })

        doc.close()
        return {"metadata": metadata, "pages": pages}

    def extract_text_chunks(self, pages: list, chunk_size: int = 15) -> list:
        chunks = []
        for i in range(0, len(pages), chunk_size):
            chunk_pages = pages[i:i + chunk_size]
            combined_text = "\n\n".join(
                f"--- PAGE {p['page_num']} ---\n{p['text']}"
                for p in chunk_pages
            )
            chunks.append({
                "chunk_index": len(chunks),
                "start_page": chunk_pages[0]["page_num"],
                "end_page": chunk_pages[-1]["page_num"],
                "text": combined_text,
                "total_words": sum(p["word_count"] for p in chunk_pages),
                "visual_pages": [p["page_num"] for p in chunk_pages if p["is_visual"]],
            })
        return chunks

    def get_table_of_contents(self, pdf_path: str) -> list:
        doc = fitz.open(pdf_path)
        toc = doc.get_toc()
        doc.close()
        return [{"level": e[0], "title": e[1], "page": e[2]} for e in toc]
```

---

#### FILE: `strategy_pipeline/ingestion/image_encoder.py`

```python
"""
Image Encoder — rasterizes PDF pages with charts/diagrams into images
so Claude Code can visually read candlestick patterns, indicator overlays, etc.
"""

import base64
import io
import fitz
from PIL import Image


class ImageEncoder:
    DEFAULT_DPI = 200
    MAX_DIMENSION = 1568
    JPEG_QUALITY = 85

    def encode_visual_pages(self, pages: list, pdf_path: str, dpi: int = None) -> list:
        dpi = dpi or self.DEFAULT_DPI
        visual_pages = [p for p in pages if p.get("is_visual")]
        if not visual_pages:
            return []

        doc = fitz.open(pdf_path)
        encoded = []

        for page_info in visual_pages:
            page_num = page_info["page_num"] - 1
            if page_num >= len(doc):
                continue

            page = doc[page_num]
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img = self._resize_if_needed(img)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY)
            buffer.seek(0)

            b64 = base64.standard_b64encode(buffer.read()).decode("utf-8")
            encoded.append({
                "page_num": page_info["page_num"],
                "base64_data": b64,
                "media_type": "image/jpeg",
                "width": img.width,
                "height": img.height,
                "text_on_page": page_info.get("text", ""),
            })

        doc.close()
        return encoded

    def encode_specific_pages(self, pdf_path: str, page_numbers: list, dpi: int = None) -> list:
        dpi = dpi or self.DEFAULT_DPI
        doc = fitz.open(pdf_path)
        encoded = []

        for page_num in page_numbers:
            idx = page_num - 1
            if idx < 0 or idx >= len(doc):
                continue
            page = doc[idx]
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            img = self._resize_if_needed(img)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.JPEG_QUALITY)
            buffer.seek(0)

            b64 = base64.standard_b64encode(buffer.read()).decode("utf-8")
            encoded.append({
                "page_num": page_num,
                "base64_data": b64,
                "media_type": "image/jpeg",
                "width": img.width,
                "height": img.height,
            })

        doc.close()
        return encoded

    def _resize_if_needed(self, img):
        w, h = img.size
        if max(w, h) <= self.MAX_DIMENSION:
            return img
        if w > h:
            new_w = self.MAX_DIMENSION
            new_h = int(h * (self.MAX_DIMENSION / w))
        else:
            new_h = self.MAX_DIMENSION
            new_w = int(w * (self.MAX_DIMENSION / h))
        return img.resize((new_w, new_h), Image.LANCZOS)
```

---

#### FILE: `strategy_pipeline/backtesting/bt_runner.py`

```python
"""
Backtest Runner — lightweight backtesting engine for pipeline-generated strategies.
Each strategy file has entry_signal(), exit_signal(), position_size() functions.

Usage:
    python -m strategy_pipeline.backtesting.bt_runner --strategy output/strategies/strategy_001.py --data data.csv
"""

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class TradeRecord:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    position_size: float
    direction: str
    pnl: float
    pnl_pct: float
    hold_bars: int
    exit_reason: str


@dataclass
class BacktestResults:
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_hold_bars: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    trades: list = field(default_factory=list)
    equity_curve: Optional[pd.Series] = None


class BacktestRunner:
    def __init__(self, initial_capital=100_000, commission_pct=0.001, slippage_pct=0.0005):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def load_strategy(self, strategy_path):
        if not os.path.exists(strategy_path):
            raise FileNotFoundError(f"Strategy file not found: {strategy_path}")
        spec = importlib.util.spec_from_file_location("strategy", strategy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in ["entry_signal", "exit_signal", "STRATEGY_META"]:
            if not hasattr(module, attr):
                raise AttributeError(f"Strategy missing: {attr}")
        return module

    def run(self, strategy_path, df, risk_pct=0.01, params=None):
        strategy = self.load_strategy(strategy_path)
        meta = strategy.STRATEGY_META
        strategy_name = meta.get("name", os.path.basename(strategy_path))

        df = df.copy()
        df.columns = df.columns.str.lower()

        if hasattr(strategy, "compute_indicators"):
            df = strategy.compute_indicators(df, params)

        entries = strategy.entry_signal(df, params)
        exits = strategy.exit_signal(df, params)

        trades = []
        capital = self.initial_capital
        equity_curve = [capital]
        in_position = False
        entry_price = entry_idx = pos_size = 0

        for i in range(1, len(df)):
            if not in_position and entries.iloc[i]:
                entry_price = df["close"].iloc[i] * (1 + self.slippage_pct)
                stop = (strategy.get_stop_loss(df, i, params)
                        if hasattr(strategy, "get_stop_loss")
                        else entry_price * 0.98)
                if hasattr(strategy, "position_size"):
                    pos_size = strategy.position_size(capital, entry_price, stop, risk_pct)
                else:
                    price_risk = abs(entry_price - stop)
                    pos_size = (capital * risk_pct / price_risk) if price_risk > 0 else 0
                pos_size = min(pos_size, capital / entry_price)
                if pos_size > 0:
                    in_position = True
                    entry_idx = i
                    capital -= pos_size * entry_price * self.commission_pct

            elif in_position and exits.iloc[i]:
                exit_price = df["close"].iloc[i] * (1 - self.slippage_pct)
                pnl = (exit_price - entry_price) * pos_size
                pnl -= pos_size * exit_price * self.commission_pct
                capital += pnl
                trades.append(TradeRecord(
                    entry_date=str(df.index[entry_idx]),
                    exit_date=str(df.index[i]),
                    entry_price=entry_price, exit_price=exit_price,
                    position_size=pos_size, direction="long",
                    pnl=pnl, pnl_pct=(exit_price - entry_price) / entry_price,
                    hold_bars=i - entry_idx, exit_reason="signal",
                ))
                in_position = False

            equity_curve.append(
                capital if not in_position
                else capital + (df["close"].iloc[i] - entry_price) * pos_size
            )

        equity_series = pd.Series(equity_curve)
        if not trades:
            return BacktestResults(
                strategy_name=strategy_name,
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, total_pnl=0, total_return_pct=0,
                max_drawdown_pct=0, sharpe_ratio=0, profit_factor=0,
                avg_win=0, avg_loss=0, avg_hold_bars=0,
                max_consecutive_wins=0, max_consecutive_losses=0,
                trades=[], equity_curve=equity_series,
            )

        pnls = [t.pnl for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        peak = equity_series.expanding().max()
        max_dd = ((equity_series - peak) / peak).min()
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        gross_losses = abs(sum(losses)) if losses else 1
        pf = (sum(wins) / gross_losses) if gross_losses > 0 else float("inf")

        max_w = max_l = curr_w = curr_l = 0
        for p in pnls:
            if p > 0:
                curr_w += 1; curr_l = 0; max_w = max(max_w, curr_w)
            else:
                curr_l += 1; curr_w = 0; max_l = max(max_l, curr_l)

        return BacktestResults(
            strategy_name=strategy_name,
            total_trades=len(trades), winning_trades=len(wins), losing_trades=len(losses),
            win_rate=len(wins)/len(trades), total_pnl=sum(pnls),
            total_return_pct=(capital - self.initial_capital) / self.initial_capital,
            max_drawdown_pct=max_dd, sharpe_ratio=sharpe, profit_factor=pf,
            avg_win=np.mean(wins) if wins else 0,
            avg_loss=np.mean(losses) if losses else 0,
            avg_hold_bars=np.mean([t.hold_bars for t in trades]),
            max_consecutive_wins=max_w, max_consecutive_losses=max_l,
            trades=trades, equity_curve=equity_series,
        )

    def run_all(self, strategies_dir, df, risk_pct=0.01):
        results = {}
        for sf in sorted(f for f in os.listdir(strategies_dir) if f.endswith(".py")):
            path = os.path.join(strategies_dir, sf)
            try:
                result = self.run(path, df, risk_pct)
                results[sf] = result
                print(f"  {sf}: {result.total_trades} trades | "
                      f"WR: {result.win_rate:.1%} | Sharpe: {result.sharpe_ratio:.2f}")
            except Exception as e:
                print(f"  [ERROR] {sf}: {e}")
        return results

    @staticmethod
    def results_to_dataframe(results):
        rows = [{
            "strategy": r.strategy_name, "file": n, "trades": r.total_trades,
            "win_rate": r.win_rate, "total_pnl": r.total_pnl,
            "return_pct": r.total_return_pct, "max_drawdown": r.max_drawdown_pct,
            "sharpe": r.sharpe_ratio, "profit_factor": r.profit_factor,
        } for n, r in results.items()]
        return pd.DataFrame(rows).sort_values("sharpe", ascending=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--capital", type=float, default=100000)
    parser.add_argument("--risk", type=float, default=0.01)
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=True, index_col=0)
    result = BacktestRunner(initial_capital=args.capital).run(args.strategy, df, args.risk)
    print(f"\nStrategy: {result.strategy_name}")
    print(f"Trades: {result.total_trades} | Win Rate: {result.win_rate:.1%}")
    print(f"Return: {result.total_return_pct:.2%} | Sharpe: {result.sharpe_ratio:.2f}")
    print(f"Max DD: {result.max_drawdown_pct:.2%} | PF: {result.profit_factor:.2f}")
```

---

### STEP 4: Create the initial Obsidian notes

Find my Obsidian vault — it's likely integrated in this repo already. If you can't find it, ask me for the path. Create these files inside the vault under `Trading Strategies/Pipeline Output/`. Also create copies in `strategy_pipeline/obsidian/` as a backup.

**CRITICAL: All these notes MUST use `[[wikilinks]]` so they connect in Obsidian's graph view.**

---

#### FILE: `Pipeline Documentation.md`

```markdown
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

## Links

- [[Strategy Comparison Overview]]
- [[Master Report]]
```

---

#### FILE: `Strategy Comparison Overview.md`

```markdown
# Strategy Comparison Overview

#trading #pipeline #overview

## What This Is

This is the central hub for all strategies extracted from trading books by the pipeline. After Claude Code processes your books, this note will be updated with links to every book analysis and every strategy cluster.

## Books Analysed

(Will be populated after the pipeline runs)

## Strategy Clusters

Strategies grouped by similarity across books. Higher overlap = higher confidence that a strategy concept is battle-tested.

(Will be populated after the pipeline runs)

## Consensus Rules

Rules that multiple authors agree on — these are your safest bets.

(Will be populated after the pipeline runs)

## Contradictions

Where authors disagree — investigate these before backtesting.

(Will be populated after the pipeline runs)

## Links

- [[Pipeline Documentation]]
- [[Master Report]]
```

---

#### FILE: `Master Report.md`

```markdown
# Master Report

#trading #pipeline #report

This file is auto-generated when Claude Code processes your trading books.

It will contain:
- List of all books processed with strategy counts
- All strategy clusters with confidence ratings
- Cross-book overlaps and contradictions
- Links to individual [[Book Analyses]] and [[Strategies]]

## How to Generate

See [[Pipeline Documentation]] for instructions.

## Links

- [[Pipeline Documentation]]
- [[Strategy Comparison Overview]]
```

---

### STEP 5: Create the README

#### FILE: `strategy_pipeline/README.md`

```markdown
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
```

---

### STEP 6: Verify everything

After creating all files:

1. Run `python -c "from strategy_pipeline.ingestion.pdf_parser import PDFParser; print('Parser OK')"`
2. Run `python -c "from strategy_pipeline.backtesting.bt_runner import BacktestRunner; print('Backtester OK')"`
3. Check the Obsidian vault has the 3 documentation notes
4. Tell me: **"Pipeline is built. Drop your PDFs into strategy_pipeline/books/ and tell me when you're ready to process them."**

---

## PART 2: PROCESSING BOOKS (do this after I drop PDFs in)

When I tell you to process the books, here is EXACTLY what you need to do for each book:

### FOR EACH BOOK:

1. **Parse the PDF** using the pdf_parser:
```python
from strategy_pipeline.ingestion.pdf_parser import PDFParser
parser = PDFParser()
result = parser.parse("strategy_pipeline/books/BOOKNAME.pdf")
```

2. **Read through all the text** extracted from every page. Also use the image_encoder to rasterize pages that contain charts/diagrams so you can visually read them.

3. **Extract EVERY usable trading strategy**. For each strategy, capture:
   - **name**: Clear descriptive name
   - **type**: momentum, mean-reversion, breakout, trend-following, volatility, pattern-based, etc.
   - **markets**: equities, forex, futures, crypto, options, commodities, bonds
   - **timeframes**: 1m, 5m, 15m, 1H, 4H, 1D, 1W, 1M
   - **entry_rules**: Precise conditions you could code
   - **exit_rules**: Take profit, stop loss, trailing stop, time-based exits
   - **risk_management**: Position sizing, max drawdown, risk per trade
   - **indicators**: With specific parameters (e.g. "20-period SMA" not just "SMA")
   - **source_chapter**: Where in the book this appears
   - **source_pages**: Page numbers
   - **clarity_score**: 1-10, how clearly defined and codifiable
   - **completeness**: 1-10 (entry + exit + risk = complete)
   - **notes**: Caveats, when it fails, author warnings

   **IMPORTANT RULES:**
   - Extract BOTH explicitly named strategies AND implied ones
   - If it can be coded, it counts as a strategy
   - Chart patterns described visually count — describe them precisely
   - Include risk rules from ANYWHERE in the book
   - Note any backtesting results the author claims
   - Capture indicator parameters PRECISELY

4. **Save the analysis** as JSON:
   ```
   strategy_pipeline/output/book_analyses/BOOKNAME_analysis.json
   ```

5. **Create an Obsidian note** at `strategy_pipeline/obsidian/Book Analyses/BOOKNAME.md`:
   ```markdown
   # BOOKNAME

   #trading #book-analysis

   ## Book Philosophy
   (1-2 sentence summary of the book's approach)

   ## Strategies Found: X

   ### [[Strategy Name 1]]
   - Type: momentum
   - Markets: equities, futures
   - Entry: (rules)
   - Exit: (rules)
   - Clarity: 8/10

   ### [[Strategy Name 2]]
   ...

   ## Key Concepts
   - concept 1
   - concept 2

   ## Author Warnings
   - warning 1

   ## Related Books
   - [[Other Book Name]]

   ## Links
   - [[Master Report]]
   - [[Strategy Comparison Overview]]
   ```

   **Note: Strategy names MUST be [[wikilinked]] so they connect to the strategy cluster notes in graph view.**

### AFTER ALL BOOKS ARE PROCESSED:

6. **Cross-compare all analyses.** Read through every book's analysis JSON and find:
   - **Strategy clusters**: Strategies that appear in multiple books (even with different names). For example, "Bollinger Squeeze" and "Volatility Contraction" are the same concept.
   - **Overlap count**: How many books contain each strategy cluster
   - **Confidence rating**: high (4+ books), medium (2-3), low (1 book)
   - **Consensus rules**: Risk management principles multiple authors agree on
   - **Contradictions**: Where one author says "do X" and another says "never do X"
   - **Recommended backtest order**: Which strategies to test first and why

   Save as: `strategy_pipeline/output/comparisons/comparison.json`

7. **Generate Python strategy files.** For each strategy cluster, create a standalone `.py` file in `output/strategies/` with this exact interface:

   ```python
   """
   Strategy: [Name]
   Source: [Books where found]
   Markets: [list] | Timeframes: [list]
   Overlap: X books | Confidence: high/medium/low
   """
   import numpy as np
   import pandas as pd

   STRATEGY_META = {
       "name": "...",
       "type": "...",
       "markets": [...],
       "timeframes": [...],
       "overlap_count": X,
       "confidence": "high/medium/low",
       "indicators": [...],
       "source_books": [...],
       "parameters": { ... }  # all tuneable params with defaults
   }

   def compute_indicators(df, params=None):
       """Add indicator columns. df has: open, high, low, close, volume"""
       params = params or STRATEGY_META["parameters"]
       df = df.copy()
       # ... calculations using pandas/numpy only (NO ta-lib)
       return df

   def entry_signal(df, params=None):
       """Returns boolean Series — True where entry conditions are met."""
       params = params or STRATEGY_META["parameters"]
       if "needed_column" not in df.columns:
           df = compute_indicators(df, params)
       # ... entry logic
       return signal

   def exit_signal(df, params=None):
       """Returns boolean Series — True where exit conditions are met."""
       params = params or STRATEGY_META["parameters"]
       if "needed_column" not in df.columns:
           df = compute_indicators(df, params)
       # ... exit logic
       return signal

   def position_size(capital, entry_price, stop_price, risk_pct=0.01):
       """Calculate position size based on risk."""
       risk_amount = capital * risk_pct
       price_risk = abs(entry_price - stop_price)
       if price_risk == 0:
           return 0
       return risk_amount / price_risk

   def get_stop_loss(df, entry_idx, params=None):
       """Calculate stop loss price."""
       # ... logic
       return stop_price

   def get_take_profit(df, entry_idx, params=None):
       """Calculate take profit target."""
       # ... logic
       return target_price
   ```

   **CRITICAL: The code must be syntactically valid, use only pandas/numpy, handle NaN edge cases, and have comments explaining the trading logic.**

   Name files: `strategy_001_momentum_breakout.py`, `strategy_002_mean_reversion.py`, etc.

8. **Create Obsidian notes for each strategy cluster** at `strategy_pipeline/obsidian/Strategies/`:

   ```markdown
   # Strategy Name

   #trading #strategy #high-confidence

   ## Overview
   (What this strategy does in plain English)

   ## Found In
   - [[Book 1 Name]]
   - [[Book 2 Name]]
   - [[Book 3 Name]]

   Overlap: 3 books | Confidence: high

   ## Markets
   equities, futures

   ## Timeframes
   1D, 4H

   ## Entry Rules
   (Precise rules)

   ## Exit Rules
   (Precise rules)

   ## Risk Management
   (Rules)

   ## Indicators Used
   - 20-period SMA
   - RSI(14)

   ## Variations Between Books
   - Book 1 uses 20 SMA, Book 3 uses 50 SMA
   - Book 2 adds volume confirmation

   ## Related Strategies
   - [[Other Strategy Name]] (shared books: Book 1, Book 3)

   ## Python File
   `strategy_001_momentum_breakout.py`

   ## Links
   - [[Master Report]]
   - [[Strategy Comparison Overview]]
   ```

9. **Update the Master Report** and **Strategy Comparison Overview** notes with actual data, full wikilinks to all books and strategies.

10. **Update the README** with a summary of what was found.

---

## HOW IT ALL CONNECTS — SIMPLE EXPLANATION

Think of it like a university study group:

1. **15 students** each read a different trading book (Claude Code reads each one)
2. Each student writes detailed notes: every strategy, how to enter, how to exit, what market
3. The **class president** compares everyone's notes and finds:
   - "8 of you found the same momentum breakout — just with different names"
   - "Books 3 and 7 disagree about stop losses — we should check"
   - "This mean reversion setup appeared in 12 books — it's probably legit"
4. A **coder** writes Python for each clustered strategy
5. You backtest each one, and the winners become bots

The Obsidian notes are the study group's shared whiteboard — everything connected so you can see which books support which strategies at a glance in graph view.

---

## BEFORE PROCESSING — CHECKLIST

- [ ] All code files are created and imports verified
- [ ] Obsidian documentation notes exist with wikilinks
- [ ] PDFs are in `strategy_pipeline/books/`
- [ ] I've told Claude Code which books to start with (start with 1-2 to test)
