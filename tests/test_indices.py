"""
SBRS 1.1 — Indices Test (S&P 500, NASDAQ, DAX)
Tests both constrained (open/close windows) and unconstrained (full market hours).
Run: py tests/test_indices.py
"""
import warnings
warnings.filterwarnings('ignore')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.data.fetcher import fetch, get_symbol_name
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval

CAPITAL = 10000.0
INDICES = ['^GSPC', '^IXIC', '^GDAXI']
TIMEFRAMES = ['4h', '1h']


def test_indices_integration_manual_only():
    """Heavy OANDA script — not run during pytest collect. Run: py tests/test_indices.py"""
    pytest.skip("Integration script — run manually: py tests/test_indices.py")


def main():
    results = []

    print("=" * 90)
    print("  SBRS 1.1 — INDICES TEST (Constrained vs Unconstrained)")
    print("=" * 90)

    for tf in TIMEFRAMES:
        period = '2y' if tf == '4h' else '1y'  # Yahoo 1H limit ~730 days
        risk_config = risk_config_for_interval(tf, 0.01)

        print(f"\n{'='*90}")
        print(f"  TIMEFRAME: {tf.upper()} / Period: {period}")
        print(f"{'='*90}")

        for symbol in INDICES:
            name = get_symbol_name(symbol)
            print(f"\n  --- {name} ({symbol}) ---")

            try:
                df = fetch(symbol, tf, period)
                print(f"  Loaded {len(df)} candles: {df.index[0]} to {df.index[-1]}")
            except Exception as e:
                print(f"  FAILED to fetch: {e}")
                continue

            if len(df) < 50:
                print(f"  Not enough data ({len(df)} bars), skipping")
                continue

            print(f"  Running CONSTRAINED (open 90min + close 60min)...")
            setups_c = analyze_gold_sbrs(df, CAPITAL, 0.01, asset_class='indices',
                                          symbol=symbol, indices_constrained=True)
            sbrs_ind = get_sbrs_indicators(df)
            result_c = run_backtest(df, setups_c, CAPITAL, risk_config,
                                    apply_slippage=True, sbrs_indicators=sbrs_ind)

            print(f"  Running UNCONSTRAINED (full market hours)...")
            setups_u = analyze_gold_sbrs(df, CAPITAL, 0.01, asset_class='indices',
                                          symbol=symbol, indices_constrained=False)
            result_u = run_backtest(df, setups_u, CAPITAL, risk_config,
                                    apply_slippage=True, sbrs_indicators=sbrs_ind)

            for label, r in [("CONSTRAINED", result_c), ("UNCONSTRAINED", result_u)]:
                pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
                print(f"    {label:14s}: {r.total_trades:>3}t, {r.win_rate:>5.1f}% WR, ${r.total_pnl:>9,.2f}, PF {pf:>5}, Sharpe {r.sharpe_ratio:>5.2f}, DD {r.max_drawdown_pct:.1f}%")

            results.append({
                'symbol': symbol, 'name': name, 'tf': tf,
                'c_trades': result_c.total_trades, 'c_wr': result_c.win_rate,
                'c_pnl': result_c.total_pnl, 'c_pf': result_c.profit_factor,
                'c_sharpe': result_c.sharpe_ratio, 'c_dd': result_c.max_drawdown_pct,
                'u_trades': result_u.total_trades, 'u_wr': result_u.win_rate,
                'u_pnl': result_u.total_pnl, 'u_pf': result_u.profit_factor,
                'u_sharpe': result_u.sharpe_ratio, 'u_dd': result_u.max_drawdown_pct,
            })

    print(f"\n{'='*90}")
    print(f"  SUMMARY: CONSTRAINED vs UNCONSTRAINED")
    print(f"{'='*90}")
    print(f"\n  {'Index':<12} {'TF':>3} | {'C-Trades':>8} {'C-WR':>6} {'C-PnL':>10} {'C-PF':>6} {'C-Shrp':>6} | {'U-Trades':>8} {'U-WR':>6} {'U-PnL':>10} {'U-PF':>6} {'U-Shrp':>6} | {'Winner':>12}")
    print(f"  {'-'*12} {'-'*3}-+-{'-'*8}-{'-'*6}-{'-'*10}-{'-'*6}-{'-'*6}-+-{'-'*8}-{'-'*6}-{'-'*10}-{'-'*6}-{'-'*6}-+-{'-'*12}")

    for r in results:
        cpf = f"{r['c_pf']:.2f}" if r['c_pf'] < 100 else "inf"
        upf = f"{r['u_pf']:.2f}" if r['u_pf'] < 100 else "inf"
        winner = "CONSTRAINED" if r['c_pnl'] > r['u_pnl'] else "UNCONSTRAINED" if r['u_pnl'] > r['c_pnl'] else "TIE"
        print(f"  {r['name']:<12} {r['tf']:>3} | {r['c_trades']:>8} {r['c_wr']:>5.1f}% ${r['c_pnl']:>9,.2f} {cpf:>6} {r['c_sharpe']:>6.2f} | {r['u_trades']:>8} {r['u_wr']:>5.1f}% ${r['u_pnl']:>9,.2f} {upf:>6} {r['u_sharpe']:>6.2f} | {winner:>12}")

    print(f"\n{'='*90}")
    print(f"  TEST COMPLETE")
    print(f"{'='*90}")


if __name__ == "__main__":
    main()
