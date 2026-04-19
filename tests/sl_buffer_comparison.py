"""
SL Buffer ATR Comparison Test — Gold 10Y

Tests SL_BUFFER_ATR at 0.3, 0.4, 0.5, 0.6 with:
- Full 10Y backtest
- 8-window walk-forward
- Comparison table

Run: py -m tests.sl_buffer_comparison
"""
import warnings
warnings.filterwarnings('ignore')

from src.data.fetcher import fetch
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval
from src.core.walk_forward import run_walk_forward
import src.regimes.sbrs_v2 as v2


def main():
    print("Fetching Gold 10Y data...")
    df = fetch('GC=F', '1h', '10y')
    print(f"Loaded {len(df)} candles\n")

    results = []
    original = v2.SL_BUFFER_ATR

    for sl_val in [0.3, 0.4, 0.5, 0.6]:
        sep = "=" * 60
        print(f"\n{sep}")
        print(f"  TESTING SL_BUFFER_ATR = {sl_val}")
        print(sep)

        v2.SL_BUFFER_ATR = sl_val

        setups = analyze_sbrs_v2(df, 10000.0, 0.01, asset_class='gold', symbol='GC=F')
        ind = get_sbrs_v2_indicators(df)
        rc = risk_config_for_interval('1h', 0.01, 'gold')
        bt = run_backtest(df, setups, 10000.0, rc, apply_slippage=True, sbrs_v2_indicators=ind)

        print(f"  Backtest: {bt.total_trades} trades | PF {bt.profit_factor} | "
              f"Sharpe {bt.sharpe_ratio} | DD {bt.max_drawdown_pct}% | PnL ${bt.total_pnl:,.0f}")
        print(f"  WR {bt.win_rate}% | AvgWin ${bt.avg_win:,.0f} | AvgLoss ${bt.avg_loss:,.0f} | "
              f"MaxStreak {bt.max_consecutive_losses}")

        analyze_fn = lambda d, eq, rp: analyze_sbrs_v2(d, eq, rp, asset_class='gold', symbol='GC=F')
        wf = run_walk_forward(
            df=df, analyze_fn=analyze_fn, n_windows=8,
            initial_capital=10000.0, risk_pct=0.01,
            apply_slippage=True, min_bars=100,
            sbrs_indicator_fn=get_sbrs_v2_indicators,
            interval='1h', asset_class='gold'
        )

        print(f"  Walk-Forward: {wf.consistency_score}% ({wf.profitable_windows}/{wf.total_windows}) | "
              f"Combined PnL ${wf.total_pnl:,.0f}")
        print(f"  Avg PF {wf.avg_profit_factor} | Avg Sharpe {wf.avg_sharpe} | "
              f"Edge slope ${wf.edge_degradation:,.0f}")

        results.append({
            'sl': sl_val,
            'trades': bt.total_trades, 'pf': bt.profit_factor,
            'sharpe': bt.sharpe_ratio, 'dd': bt.max_drawdown_pct,
            'pnl': bt.total_pnl, 'wr': bt.win_rate,
            'avg_win': bt.avg_win, 'avg_loss': bt.avg_loss,
            'max_streak': bt.max_consecutive_losses,
            'wf_pct': wf.consistency_score, 'wf_wins': wf.profitable_windows,
            'wf_pnl': wf.total_pnl, 'wf_avg_pf': wf.avg_profit_factor,
            'wf_avg_sharpe': wf.avg_sharpe, 'wf_slope': wf.edge_degradation,
        })

    v2.SL_BUFFER_ATR = original

    sep = "=" * 110
    print(f"\n{sep}")
    print("  FINAL COMPARISON: SL_BUFFER_ATR (Gold 10Y, SBRS 2.0 + ATR Filter + Adaptive R:R)")
    print(sep)
    header = (f"{'SL':>5} {'Trades':>7} {'PF':>6} {'Sharpe':>7} {'DD%':>6} "
              f"{'PnL':>10} {'WR%':>5} {'AvgW':>7} {'AvgL':>7} {'Strk':>5} "
              f"{'WF%':>5} {'WF_PnL':>9} {'WF_PF':>6} {'Slope':>7}")
    print(header)
    print("-" * 110)
    for r in results:
        print(f"{r['sl']:>5.1f} {r['trades']:>7d} {r['pf']:>6.2f} {r['sharpe']:>7.2f} "
              f"{r['dd']:>6.2f} {r['pnl']:>10,.0f} {r['wr']:>5.1f} {r['avg_win']:>7,.0f} "
              f"{r['avg_loss']:>7,.0f} {r['max_streak']:>5d} {r['wf_pct']:>5.0f} "
              f"{r['wf_pnl']:>9,.0f} {r['wf_avg_pf']:>6.2f} {r['wf_slope']:>7,.0f}")
    print(sep)


if __name__ == '__main__':
    main()
