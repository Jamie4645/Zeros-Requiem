# Real Trade Intake — Supervised SBRS Rebuild

Purpose: compare what YOU actually did, setup-by-setup, against what the algorithm
does on the *same* bars — to find the discretionary judgment the rules miss.
(Audit 2026-06-01/02 showed the codified strategy tops out at PF ~1.07; the edge
lives in judgment the narrative rules don't capture.)

## What to drop in this folder

### 1. Chart screenshots (most important)
Export each real trade from TradingView as a PNG/JPG. On each chart, show:
- the level(s) you drew (support/resistance, consolidation zones)
- entry point, stop-loss, take-profit
- the outcome (where it actually closed)
Name them `trade_01.png`, `trade_02.png`, … (matching the CSV row below).
I can open and read images directly.

### 2. Trade list (CSV or table) — `trades.csv`
One row per trade with these columns:

```
id,instrument,timeframe,direction,entry_time,entry_price,stop_loss,take_profit,exit_time,exit_price,outcome,reasoning
1,XAUUSD,1h,long,2024-03-12 14:00,2158.40,2151.00,2180.00,2024-03-13 09:00,2180.00,win,"retest of broken resistance, SMMA>WMA, FVG on break"
```
- `entry_time` / `exit_time` in UTC if possible (or tell me the timezone).
- `reasoning`: 1 line on WHY you took it and where you placed TP/SL and why.
- If it's a TradingView "List of Trades" export, just drop that CSV as-is and I'll map the columns.

### 3. (Optional) The losers too
A few trades you SKIPPED or that LOST are gold — they show what your judgment
filters out that the algo doesn't.

## What I'll do with it
1. Map each trade's timestamps onto our OANDA 1H/4H data.
2. Run SBRS 3.0 (and the bare core) over those exact windows.
3. Produce a per-trade diff: did the algo see the setup? enter where you did?
   place SL/TP where you did? exit where you did? — and quantify the gap.
4. Use the pattern of gaps to propose the specific rule/feature that's missing.

## Parallel track: TradingView visual backtest
I'm also writing `pine/sbrs_v3.pine` — paste it into TradingView's Pine editor
(v5 strategy) to see SBRS 3.0's entries/exits and Strategy Tester stats natively
on your charts, on any instrument/timeframe.
