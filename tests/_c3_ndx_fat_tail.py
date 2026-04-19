"""
Round 5 C3 — NDX PF 3.49 fat-tail forensic.

Runs a 10Y NASDAQ backtest and dumps the top-5 gross-win trades with entry
timestamps so the council can cross-reference each with macro events
(COVID 2020-03, ChatGPT 2022-11, AI rally 2023-Q1, etc.).

One-off diagnostic script. Not part of the pytest suite.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.data.fetcher import fetch, detect_asset_class
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


SYMBOL = "^IXIC"
INTERVAL = "1h"
PERIOD = "10y"
CAPITAL = 10_000.0
RISK = 0.01


def main():
    print(f"[C3] Fetching {SYMBOL} {INTERVAL} {PERIOD}...")
    df = fetch(SYMBOL, INTERVAL, PERIOD)
    print(f"[C3] {len(df)} bars {df.index[0]} -> {df.index[-1]}")

    asset_class = detect_asset_class(SYMBOL)
    print(f"[C3] asset_class={asset_class}")

    setups = analyze_sbrs_v2(df, CAPITAL, RISK, asset_class=asset_class, symbol=SYMBOL)
    print(f"[C3] {len(setups)} setups")

    risk_config = risk_config_for_interval(INTERVAL, RISK, asset_class, symbol=SYMBOL)
    ind = get_sbrs_v2_indicators(df)
    result = run_backtest(df, setups, CAPITAL, risk_config, apply_slippage=True, sbrs_v2_indicators=ind)

    print(f"[C3] total_trades={result.total_trades} PF={result.profit_factor:.2f} "
          f"Sharpe={result.sharpe_ratio:.2f} DD={result.max_drawdown_pct:.2f}%")

    top = sorted(result.trades, key=lambda t: t.pnl, reverse=True)[:10]
    total_positive = sum(t.pnl for t in result.trades if t.pnl > 0)
    print(f"[C3] gross_wins_total=${total_positive:,.2f}")

    print("\n[C3] TOP 10 GROSS WINS (pnl, entry_ts, exit_ts, direction, pct_of_wins):")
    for i, t in enumerate(top, 1):
        try:
            entry_ts = df.index[t.entry_index]
            exit_ts = df.index[t.exit_index]
        except Exception:
            entry_ts = "?"
            exit_ts = "?"
        pct = 100.0 * t.pnl / total_positive if total_positive else 0.0
        print(f"  #{i:2d}  ${t.pnl:>9,.2f}  {entry_ts}  ->  {exit_ts}  "
              f"{t.direction:>5s}  {pct:5.1f}%  reason={t.exit_reason}")


if __name__ == "__main__":
    main()
