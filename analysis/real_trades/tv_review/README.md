# ZTT TradingView Review Loop

The **audit-overlay** half of the screener feedback loop (`ZTT_PLAN.md` open paths).
Purpose: see the EXACT setups ZTT produced on a TradingView chart, judge each with your
discretionary eye, and label take/skip + why. Your labels accumulate the **negatives** the
25 real trades never gave us — the data needed to one day learn the discrimination filter.

## Generate a batch
```
py analysis/real_trades/tv_review/export_ztt_trades.py [config] [days] [period_file]
  config      base | raw | full     (default base — the screener's balanced selectivity)
  days        trailing window        (default 31 — fits Pine's ~500-object limit)
  period_file 1y | 10y               (default 1y)
```
Produces three files tagged with the window:
- `ztt_trades_<window>.csv` — full trade list + features + phantom-safe outcome + realized-R
- `ztt_review_<window>.csv` — same rows with blank `decision` / `reason` / `notes` to fill
- `ztt_overlay_<window>.pine` — the TradingView overlay

## View in TradingView
1. Open **OANDA:XAUUSD** (matches our data source closest), timeframe **10m**.
2. Pine editor → paste the `.pine` file → **Add to chart**.
3. Each setup draws:
   - **green box** = profit zone (entry → TP), **red box** = risk zone (entry → SL),
     spanning the entry bar to the bar the trade actually closed.
   - **gray dashed line** = the respected/flipped level.
   - **label** at entry: `#n mode dir realized-R`. Green label = win, red = loss, gray = timeout.
   - **WMA(144) / SMMA(5)** plotted natively = the same trend context the engine used.

## Give feedback
Fill `decision` (take/skip), `reason` (the discretionary signal — "level disrespected",
"no clean retest", "against HTF", "perfect continuation", …) and `notes` in the review CSV.
Hand it back and I ingest it: take/skip become labels, reasons become candidate rules.

## Fidelity notes
- Setups come straight from `src/regimes/ztt.generate_setups` — no re-derivation.
- Outcomes use the SAME phantom-safe walk as `phase4/backtest_ztt.py` (exit only when price
  truly trades to SL/TP; SL wins an intrabar tie) + session-gated cost applied adverse.
- Outcomes are computed **independently per setup** (no overlap-blocking) — you're judging
  each setup on its own merits, not a sequential P&L curve.
- Times are UTC ms; the overlay positions everything by time, so a missing TV bar won't
  misplace a trade. TradingView's XAUUSD feed differs slightly from OANDA REST — treat the
  geometry as authoritative, the exact candle wicks as approximate.

## Honest baseline (first batch, 2026-05-11 → 2026-06-09, base config)
60 setups, geometry hit-rate **8%** (5 win / 34 loss / 21 timeout), net **−14.5R** at 1R each.
This is the unfiltered mechanical edge = none. The whole exercise is to find out whether YOUR
take/skip turns this negative population positive — i.e. to capture the discretionary filter.
