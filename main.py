"""
Zeros Requiem — SBRS (Sovereign Breakout Retest Strategy)

Systematic algo trading for Gold and Forex Indices.

Usage:
    Single symbol (SBRS 1.1):
        py main.py --symbol GC=F --interval 1h --period 10y
        py main.py --symbol ^GSPC --interval 1h --period 10y

    Single symbol (SBRS 2.0):
        py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2

    Walk-forward validation (8 sequential windows):
        py main.py --walk-forward GC=F --interval 1h --windows 8
        py main.py --walk-forward GC=F --interval 1h --windows 8 --strategy sbrs_v2

    Monte Carlo simulation:
        py main.py --symbol GC=F --interval 1h --period 10y --monte-carlo
"""

import argparse
import warnings
warnings.filterwarnings('ignore')

from src.data.fetcher import (
    fetch, detect_asset_class, get_symbol_name, get_symbols_for_class, SYMBOLS
)
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, BacktestResult
from src.core.risk_manager import RiskConfig, risk_config_for_interval
from src.core.walk_forward import run_walk_forward, print_walk_forward_report
from src.core.monte_carlo import run_monte_carlo, print_monte_carlo_report


def _analyze_symbol(symbol, df, capital, risk, strategy='sbrs_v1'):
    """Route a symbol to the SBRS analyzer with correct asset class."""
    asset_class = detect_asset_class(symbol)

    if strategy == 'sbrs_v2':
        from src.regimes.sbrs_v2 import analyze_sbrs_v2
        if asset_class in ('gold', 'commodity'):
            return analyze_sbrs_v2(df, capital, risk, asset_class='gold', symbol=symbol)
        elif asset_class == 'indices':
            return analyze_sbrs_v2(df, capital, risk, asset_class='indices', symbol=symbol)
        elif asset_class == 'forex':
            return analyze_sbrs_v2(df, capital, risk, asset_class='forex', symbol=symbol)
        elif asset_class == 'crypto':
            return analyze_sbrs_v2(df, capital, risk, asset_class='crypto', symbol=symbol)
        else:
            print(f"  WARNING: Unsupported asset class '{asset_class}' for SBRS 2.0, trying as forex")
            return analyze_sbrs_v2(df, capital, risk, asset_class='forex', symbol=symbol)
    else:
        if asset_class in ('gold', 'commodity'):
            return analyze_gold_sbrs(df, capital, risk, asset_class='gold')
        elif asset_class == 'indices':
            return analyze_gold_sbrs(df, capital, risk, asset_class='indices', symbol=symbol)
        elif asset_class == 'forex':
            return analyze_gold_sbrs(df, capital, risk, asset_class='forex', symbol=symbol)
        else:
            print(f"  WARNING: Unsupported asset class '{asset_class}' for SBRS")
            return []


def _print_result(result, symbol_name=""):
    """Print a single backtest result with elite metrics."""
    header = f"BACKTEST RESULTS - {symbol_name}" if symbol_name else "BACKTEST RESULTS"
    print(f"""
    ----------------------------------------------------------------
      {header}
    ----------------------------------------------------------------
      Total Trades:     {result.total_trades}
      Winning Trades:   {result.winning_trades}
      Losing Trades:    {result.losing_trades}
      Win Rate:         {result.win_rate:.1f}%
      Total PnL:        ${result.total_pnl:,.2f}
      Total Return:     {result.total_return_pct:.2f}%
      Profit Factor:    {result.profit_factor:.2f}
      Max Drawdown:     {result.max_drawdown_pct:.2f}%
      Final Capital:    ${result.final_capital:,.2f}
      --- Elite Metrics ---
      Sharpe Ratio:     {result.sharpe_ratio:.2f}
      Sortino Ratio:    {result.sortino_ratio:.2f}
      Expectancy:       ${result.expectancy:,.2f} / trade
      Expectancy (R):   {result.expectancy_r:.3f}R / trade
      Avg Win:          ${result.avg_win:,.2f}
      Avg Loss:         ${result.avg_loss:,.2f}
      RoMaD:            {result.romad:.2f}
      Max Con. Wins:    {result.max_consecutive_wins}
      Max Con. Losses:  {result.max_consecutive_losses}
    ----------------------------------------------------------------""")

    if result.regime_breakdown:
        print("      Regime Breakdown:")
        for regime, stats in result.regime_breakdown.items():
            wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
            print(f"        {regime}: {stats['count']} trades, {wr:.0f}% WR, ${stats['pnl']:,.2f}")

    rs = result.risk_stats
    if rs.get('total_blocked', 0) > 0:
        print(f"      Risk Management: {rs['total_blocked']} trades blocked")


def run_single(args):
    """Run backtest on a single symbol."""
    asset_class = detect_asset_class(args.symbol)
    name = get_symbol_name(args.symbol)
    strategy = args.strategy
    strategy_label = 'SBRS 2.0' if strategy == 'sbrs_v2' else 'SBRS 1.1'

    print(f"""
    ================================================================
      ZERO'S REQUIEM — {strategy_label}
      Sovereign Breakout Retest Strategy
    ================================================================
      Symbol:   {args.symbol} ({name})
      Class:    {asset_class}
      Strategy: {strategy_label}
      Interval: {args.interval}
      Period:   {args.period}
      Capital:  ${args.capital:,.2f}
      Risk:     {args.risk*100:.1f}% per trade
      Slippage: {'OFF' if args.no_slippage else 'ON (1.5 pips)'}
    ================================================================
    """)

    print("  Fetching market data...")
    df = fetch(args.symbol, args.interval, args.period)
    print(f"  Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    print("  Analyzing...")
    setups = _analyze_symbol(args.symbol, df, args.capital, args.risk, strategy=strategy)
    print(f"  Found {len(setups)} trade setups")

    print("  Running backtest...")
    risk_config = risk_config_for_interval(args.interval, args.risk, asset_class, symbol=args.symbol)

    if strategy == 'sbrs_v2':
        from src.regimes.sbrs_v2 import get_sbrs_v2_indicators
        sbrs_v2_ind = get_sbrs_v2_indicators(df)
        result = run_backtest(df, setups, args.capital, risk_config,
                              apply_slippage=not args.no_slippage,
                              sbrs_v2_indicators=sbrs_v2_ind)
    else:
        sbrs_ind = get_sbrs_indicators(df)
        result = run_backtest(df, setups, args.capital, risk_config,
                              apply_slippage=not args.no_slippage,
                              sbrs_indicators=sbrs_ind)

    _print_result(result, name)

    if args.monte_carlo and result.total_trades >= 3:
        print("\n  Running Monte Carlo simulation...")
        mc = run_monte_carlo(result.trades, initial_capital=args.capital,
                             n_simulations=args.mc_sims)
        print_monte_carlo_report(mc, name)
    elif args.monte_carlo:
        print("\n  Skipping Monte Carlo: too few trades (need at least 3)")

    print("\n  Analysis complete!")
    return result


def run_walk_forward_cmd(args):
    """Run walk-forward analysis on a symbol with longest available data."""
    symbol = args.walk_forward
    name = get_symbol_name(symbol)
    strategy = args.strategy
    strategy_label = 'SBRS 2.0' if strategy == 'sbrs_v2' else 'SBRS 1.1'

    from src.data.oanda_fetcher import is_oanda_available, is_oanda_instrument
    from src.data.ibkr_fetcher import is_ibkr_available, is_ibkr_instrument
    has_oanda = is_oanda_available() and is_oanda_instrument(symbol)
    has_ibkr = is_ibkr_available() and is_ibkr_instrument(symbol)

    interval = args.interval
    if interval in ('1m', '5m', '15m', '30m'):
        max_period = '1mo'
    elif interval in ('1h', '4h'):
        max_period = '10y' if (has_oanda or has_ibkr) else '2y'
    else:
        max_period = '10y' if (has_oanda or has_ibkr) else '5y'

    n_windows = args.windows

    print(f"""
    ================================================================
      ZERO'S REQUIEM — WALK-FORWARD ANALYSIS ({strategy_label})
    ================================================================
      Symbol:     {symbol} ({name})
      Strategy:   {strategy_label}
      Interval:   {interval}
      Period:     {max_period} (maximum available)
      Windows:    {n_windows}
      Capital:    ${args.capital:,.2f} (per window)
      Slippage:   {'OFF' if args.no_slippage else 'ON (1.5 pips)'}
    ================================================================
    """)

    print("  Fetching maximum available data...")
    try:
        df = fetch(symbol, interval, max_period)
        print(f"  Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")
    except Exception as e:
        print(f"  Failed to fetch data: {e}")
        return None

    if len(df) < n_windows * 100:
        print(f"  Not enough data for {n_windows} windows (need {n_windows * 100}+ bars, have {len(df)})")
        n_windows = max(2, len(df) // 100)
        print(f"  Adjusting to {n_windows} windows")

    print(f"  Running walk-forward with {n_windows} windows...")

    asset_class = detect_asset_class(symbol)

    if strategy == 'sbrs_v2':
        from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
        analyze_fn = lambda df, eq, rp: analyze_sbrs_v2(
            df, eq, rp, asset_class=asset_class, symbol=symbol
        )
        wf_result = run_walk_forward(
            df=df,
            analyze_fn=analyze_fn,
            n_windows=n_windows,
            initial_capital=args.capital,
            risk_pct=args.risk,
            apply_slippage=not args.no_slippage,
            min_bars=100,
            sbrs_indicator_fn=get_sbrs_v2_indicators,
            interval=interval,
            asset_class=asset_class,
            symbol=symbol,
        )
    else:
        analyze_fn = lambda df, eq, rp: analyze_gold_sbrs(
            df, eq, rp, asset_class=asset_class, symbol=symbol
        )
        wf_result = run_walk_forward(
            df=df,
            analyze_fn=analyze_fn,
            n_windows=n_windows,
            initial_capital=args.capital,
            risk_pct=args.risk,
            apply_slippage=not args.no_slippage,
            min_bars=100,
            sbrs_indicator_fn=get_sbrs_indicators,
            interval=interval,
            asset_class=asset_class,
            symbol=symbol,
        )

    print_walk_forward_report(wf_result, name)
    return wf_result


def main():
    parser = argparse.ArgumentParser(
        description="Zeros Requiem — SBRS (Sovereign Breakout Retest Strategy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py main.py --symbol GC=F --interval 1h --period 10y
  py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2
  py main.py --symbol ^GSPC --interval 1h --period 10y
  py main.py --walk-forward GC=F --interval 1h --windows 8
  py main.py --walk-forward GC=F --interval 1h --windows 8 --strategy sbrs_v2
  py main.py --symbol GC=F --interval 1h --period 10y --monte-carlo
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--symbol', type=str, help='Trading symbol (GC=F, ^GSPC, ^IXIC, ^GDAXI)')
    group.add_argument('--walk-forward', type=str, metavar='SYMBOL',
                       help='Run walk-forward analysis (uses max available data)')

    parser.add_argument('--interval', type=str, default='1h',
                        choices=['1m','5m','15m','30m','1h','4h','1d','1wk'])
    parser.add_argument('--period', type=str, default='1y',
                        choices=['1mo','3mo','6mo','1y','2y','5y','10y'])
    parser.add_argument('--windows', type=int, default=8,
                        help='Number of walk-forward windows (default: 8)')
    parser.add_argument('--capital', type=float, default=10000.0)
    parser.add_argument('--risk', type=float, default=0.01, help='Risk per trade (0.01 = 1%%)')
    parser.add_argument('--no-slippage', action='store_true', help='Disable slippage modelling')
    parser.add_argument('--strategy', type=str, default='sbrs_v2',
                        choices=['sbrs_v1', 'sbrs_v2'],
                        help='Strategy version (default: sbrs_v2 — v1 is retained only for ablation/comparison)')
    parser.add_argument('--monte-carlo', action='store_true',
                        help='Run Monte Carlo simulation after backtest')
    parser.add_argument('--mc-sims', type=int, default=10000,
                        help='Number of Monte Carlo simulations (default: 10000)')

    args = parser.parse_args()

    if not args.symbol and not args.walk_forward:
        args.symbol = 'GC=F'

    if args.walk_forward:
        return run_walk_forward_cmd(args)
    else:
        return run_single(args)


if __name__ == "__main__":
    main()
