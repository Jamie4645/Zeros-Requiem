"""
Round 6 C4 — GBPUSD ATR threshold parametric sweep.

Runs 3 GBPUSD 10Y backtests at ATR_PCTILE_THRESHOLD ∈ {15, 20, 25} by
monkey-patching the threshold in sbrs_v2 before each run. Holds all
other parameters constant (post-Round-5 code: confluence-1.5 forex
floor, FVG 0.5, B1 slippage bracket, GBPUSD 0.25% cap).

Goal: identify the threshold that maximises trade count without
sacrificing PF > 1.4. Does not commit any edit — test harness only.

R5 0.25% sizing cap holds regardless until WF trade count crosses 500.

One-off diagnostic. Not part of the pytest suite.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.data.fetcher import fetch, detect_asset_class
from src.regimes import sbrs_v2
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


SYMBOL = "GBPUSD=X"
INTERVAL = "1h"
PERIOD = "10y"
CAPITAL = 10_000.0
RISK = 0.0025  # GBPUSD cap (R5)


def run_sweep(threshold: int, df, risk_config, asset_class: str):
    # `is_low_volatility` reads ATR_PCTILE_THRESHOLD as a default arg at import
    # time, so monkey-patching the module constant has no effect. Replace the
    # function itself with a wrapper that forces the threshold.
    orig = sbrs_v2.is_low_volatility

    def wrapper(atr_vals, current_idx, lookback=sbrs_v2.ATR_PCTILE_LOOKBACK, threshold=threshold):
        return orig(atr_vals, current_idx, lookback=lookback, threshold=threshold)

    sbrs_v2.is_low_volatility = wrapper
    try:
        setups = analyze_sbrs_v2(df, CAPITAL, RISK, asset_class=asset_class, symbol=SYMBOL)
        ind = get_sbrs_v2_indicators(df)
        result = run_backtest(
            df, setups, CAPITAL, risk_config,
            apply_slippage=True, sbrs_v2_indicators=ind,
        )
    finally:
        sbrs_v2.is_low_volatility = orig
    return len(setups), result


def main():
    print(f"[C4] Fetching {SYMBOL} {INTERVAL} {PERIOD}...")
    df = fetch(SYMBOL, INTERVAL, PERIOD)
    print(f"[C4] {len(df)} bars {df.index[0]} -> {df.index[-1]}")

    asset_class = detect_asset_class(SYMBOL)
    print(f"[C4] asset_class={asset_class}")

    risk_config = risk_config_for_interval(INTERVAL, RISK, asset_class, symbol=SYMBOL)

    print(f"\n[C4] Current production ATR_PCTILE_THRESHOLD = {sbrs_v2.ATR_PCTILE_THRESHOLD}")

    for t in (15, 20, 25):
        print(f"\n[C4] === ATR_PCTILE_THRESHOLD = {t} ===")
        n_setups, result = run_sweep(t, df, risk_config, asset_class)
        print(
            f"[C4] T={t}: setups={n_setups} trades={result.total_trades} "
            f"PF={result.profit_factor:.2f} Sharpe={result.sharpe_ratio:.2f} "
            f"PnL=${result.total_pnl:,.2f} DD={result.max_drawdown_pct:.2f}% "
            f"WR={result.win_rate*100:.1f}%"
        )

    print("\n[C4] Interpretation:")
    print("  Lower threshold = fewer ATR-filter blocks = more trades admitted.")
    print("  Elite gate: PF > 1.4 must hold. Trade count uplift is the lever.")


if __name__ == "__main__":
    main()
