"""
Zeros Requiem - SCAF 2.0 (Sovereign Cross-Asset Framework)

A regime-aware trading algorithm for Gold, Forex, and Crypto.

The 5 Fundamental Truths (Mark Douglas):
1. Anything can happen.
2. You don't need to know what is going to happen next to make money.
3. There is a random distribution between wins and losses.
4. An edge is nothing more than a higher probability of one thing over another.
5. Every moment in the market is unique.

Usage:
    Single symbol:
        py main.py --symbol GC=F --interval 4h --period 1y
        py main.py --symbol GBPUSD=X --interval 1h --period 6mo
    
    All symbols in a regime:
        py main.py --multi forex --interval 4h --period 1y
        py main.py --multi crypto --interval 4h --period 1y
    
    All symbols across all regimes:
        py main.py --all --interval 4h --period 1y
    
    Walk-forward analysis (longest available data):
        py main.py --walk-forward GC=F --interval 4h --windows 6
        py main.py --walk-forward EURUSD=X --interval 1d --windows 8

Supported symbols:
    Gold:   GC=F
    Forex:  EURUSD=X, GBPUSD=X, USDJPY=X
    Crypto: BTC-USD, ETH-USD
"""

import argparse
import warnings
warnings.filterwarnings('ignore')

from src.data.fetcher import (
    fetch, fetch_all, detect_asset_class,
    get_symbol_name, get_symbols_for_class, SYMBOLS
)
from src.regimes.gold import analyze_gold
from src.regimes.forex import analyze_forex
from src.regimes.crypto import analyze_crypto
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, BacktestResult
from src.core.risk_manager import RiskConfig, risk_config_for_interval
from src.core.walk_forward import run_walk_forward, print_walk_forward_report
from src.core.monte_carlo import run_monte_carlo, print_monte_carlo_report


def _analyze_symbol(symbol, df, capital, risk, strategy='scaf'):
    """Route a symbol to its regime analyzer."""
    asset_class = detect_asset_class(symbol)
    
    # SBRS strategy (Gold + Forex + Indices)
    if strategy == 'sbrs':
        if asset_class in ('gold', 'commodity'):
            return analyze_gold_sbrs(df, capital, risk, asset_class='gold')
        elif asset_class == 'forex':
            return analyze_gold_sbrs(df, capital, risk, asset_class='forex')
        elif asset_class == 'indices':
            return analyze_gold_sbrs(df, capital, risk, asset_class='indices', symbol=symbol)
        else:
            print(f"  WARNING: SBRS not yet implemented for {asset_class}, falling back to SCAF")
    
    # Default SCAF strategy
    if asset_class in ('gold', 'commodity'):
        return analyze_gold(df, capital, risk)
    elif asset_class == 'forex':
        return analyze_forex(df, capital, risk, symbol=symbol)
    elif asset_class == 'crypto':
        return analyze_crypto(df, capital, risk)
    else:
        return []


def _get_analyze_fn(symbol, strategy='scaf'):
    """Get the regime analyze function for a symbol."""
    asset_class = detect_asset_class(symbol)
    
    # SBRS strategy
    if strategy == 'sbrs':
        if asset_class in ('gold', 'commodity', 'forex', 'indices'):
            return analyze_gold_sbrs
        else:
            print(f"  WARNING: SBRS not yet implemented for {asset_class}, using SCAF")
    
    # Default SCAF
    if asset_class in ('gold', 'commodity'):
        return analyze_gold
    elif asset_class == 'forex':
        return analyze_forex
    elif asset_class == 'crypto':
        return analyze_crypto
    return None


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
    strategy = getattr(args, 'strategy', 'scaf')
    strategy_name = "SBRS 1.0 (Sovereign Breakout Retest Realm)" if strategy == 'sbrs' else "SCAF 2.0"
    
    print(f"""
    ================================================================
      ZERO'S REQUIEM - {strategy_name}
      {'Breakout + Retest Strategy' if strategy == 'sbrs' else 'Sovereign Cross-Asset Framework'}
    ================================================================
      Symbol:   {args.symbol} ({name})
      Class:    {asset_class}
      Strategy: {strategy.upper()}
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
    
    print("  Analyzing regime...")
    setups = _analyze_symbol(args.symbol, df, args.capital, args.risk, strategy)
    print(f"  Found {len(setups)} trade setups")
    
    print("  Running backtest...")
    risk_config = risk_config_for_interval(args.interval, args.risk)
    
    # SBRS trades need indicator series for trade management
    sbrs_ind = get_sbrs_indicators(df) if strategy == 'sbrs' else None
    result = run_backtest(df, setups, args.capital, risk_config,
                          apply_slippage=not args.no_slippage,
                          sbrs_indicators=sbrs_ind)
    
    _print_result(result, name)
    
    # P4: Monte Carlo simulation
    if args.monte_carlo and result.total_trades >= 3:
        print("\n  Running Monte Carlo simulation...")
        mc = run_monte_carlo(result.trades, initial_capital=args.capital,
                             n_simulations=args.mc_sims)
        print_monte_carlo_report(mc, name)
    elif args.monte_carlo:
        print("\n  Skipping Monte Carlo: too few trades (need at least 3)")
    
    print("\n  Analysis complete!")
    return result


def run_multi(args, asset_class):
    """Run backtest on all symbols in an asset class."""
    symbols = get_symbols_for_class(asset_class)
    if not symbols:
        print(f"  No symbols found for asset class '{asset_class}'")
        return {}
    
    print(f"""
    ================================================================
      ZERO'S REQUIEM - SCAF 2.0 (Multi-Symbol)
      Asset Class: {asset_class.upper()}
      Symbols:     {', '.join(symbols)}
      Interval:    {args.interval}
      Period:      {args.period}
      Capital:     ${args.capital:,.2f} (per symbol)
      Slippage:    {'OFF' if args.no_slippage else 'ON (1.5 pips)'}
    ================================================================
    """)
    
    results = {}
    total_trades = 0
    total_pnl = 0.0
    
    for symbol in symbols:
        name = get_symbol_name(symbol)
        print(f"  [{name}] Fetching data...")
        
        try:
            df = fetch(symbol, args.interval, args.period)
            print(f"  [{name}] Loaded {len(df)} candles")
        except Exception as e:
            print(f"  [{name}] Failed to fetch: {e}")
            continue
        
        if len(df) < 60:
            print(f"  [{name}] Not enough data ({len(df)} bars), skipping")
            continue
        
        print(f"  [{name}] Analyzing...")
        setups = _analyze_symbol(symbol, df, args.capital, args.risk)
        print(f"  [{name}] Found {len(setups)} setups")
        
        risk_config = risk_config_for_interval(args.interval, args.risk)
        result = run_backtest(df, setups, args.capital, risk_config, apply_slippage=not args.no_slippage)
        
        results[symbol] = result
        total_trades += result.total_trades
        total_pnl += result.total_pnl
        
        _print_result(result, name)
    
    # Summary
    print(f"""
    ================================================================
      COMBINED SUMMARY - {asset_class.upper()}
    ================================================================
      Symbols Tested:   {len(results)}
      Total Trades:     {total_trades}
      Combined PnL:     ${total_pnl:,.2f}
    ================================================================
    """)
    
    return results


def run_all(args):
    """Run backtest on ALL supported symbols across all regimes."""
    print(f"""
    ================================================================
      ZERO'S REQUIEM - SCAF 2.0 (Full Portfolio)
      Running ALL supported symbols
      Interval: {args.interval}  |  Period: {args.period}
    ================================================================
    """)
    
    all_results = {}
    grand_total_trades = 0
    grand_total_pnl = 0.0
    
    for asset_class in ['gold', 'forex', 'crypto']:
        print(f"\n  === {asset_class.upper()} REGIME ===")
        symbols = get_symbols_for_class(asset_class)
        
        for symbol in symbols:
            name = get_symbol_name(symbol)
            print(f"\n  [{name}] Fetching...")
            
            try:
                df = fetch(symbol, args.interval, args.period)
                print(f"  [{name}] {len(df)} candles loaded")
            except Exception as e:
                print(f"  [{name}] Failed: {e}")
                continue
            
            if len(df) < 60:
                print(f"  [{name}] Not enough data, skipping")
                continue
            
            setups = _analyze_symbol(symbol, df, args.capital, args.risk)
            print(f"  [{name}] {len(setups)} setups found")
            
            risk_config = risk_config_for_interval(args.interval, args.risk)
            result = run_backtest(df, setups, args.capital, risk_config, apply_slippage=not args.no_slippage)
            
            all_results[symbol] = result
            grand_total_trades += result.total_trades
            grand_total_pnl += result.total_pnl
            
            _print_result(result, name)
    
    # Grand summary
    print(f"""
    ================================================================
      GRAND PORTFOLIO SUMMARY
    ================================================================
      Symbols Tested:   {len(all_results)}
      Total Trades:     {grand_total_trades}
      Combined PnL:     ${grand_total_pnl:,.2f}
    ================================================================

      Breakdown by Symbol:""")
    
    for symbol, result in all_results.items():
        name = get_symbol_name(symbol)
        print(f"        {name:20s}  {result.total_trades:3d} trades  ${result.total_pnl:>10,.2f}  WR: {result.win_rate:.0f}%")
    
    print(f"""
    ================================================================
    """)
    
    return all_results


def run_walk_forward_cmd(args):
    """Run walk-forward analysis on a symbol with longest available data."""
    symbol = args.walk_forward
    name = get_symbol_name(symbol)
    strategy = getattr(args, 'strategy', 'scaf')
    analyze_fn = _get_analyze_fn(symbol, strategy)
    
    if analyze_fn is None:
        print(f"  No regime found for symbol '{symbol}'")
        return None
    
    # Determine max period for this interval
    # P5: OANDA unlocks 10+ years for Gold/Forex on any timeframe
    # Yahoo Finance limits: 1h = ~730 days, 4h = ~2y, 1d = ~5y
    interval = args.interval
    from src.data.oanda_fetcher import is_oanda_available, is_oanda_instrument
    has_oanda = is_oanda_available() and is_oanda_instrument(symbol)
    
    if interval in ('1m', '5m', '15m', '30m'):
        max_period = '1mo'  # Very short for sub-hourly
    elif interval == '1h':
        max_period = '10y' if has_oanda else '2y'
    elif interval == '4h':
        max_period = '10y' if has_oanda else '2y'
    else:
        max_period = '10y' if has_oanda else '5y'
    
    n_windows = args.windows
    strategy_label = "SBRS 1.0" if strategy == 'sbrs' else "SCAF 2.0"
    
    print(f"""
    ================================================================
      ZERO'S REQUIEM - WALK-FORWARD ANALYSIS ({strategy_label})
    ================================================================
      Symbol:     {symbol} ({name})
      Strategy:   {strategy.upper()}
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
        # Try with fewer windows
        n_windows = max(2, len(df) // 100)
        print(f"  Adjusting to {n_windows} windows")
    
    print(f"  Running walk-forward with {n_windows} windows...")
    
    # SBRS needs indicator function for per-window trade management
    sbrs_ind_fn = get_sbrs_indicators if strategy == 'sbrs' else None
    
    wf_result = run_walk_forward(
        df=df,
        analyze_fn=analyze_fn,
        n_windows=n_windows,
        initial_capital=args.capital,
        risk_pct=args.risk,
        apply_slippage=not args.no_slippage,
        min_bars=100,
        sbrs_indicator_fn=sbrs_ind_fn
    )
    
    print_walk_forward_report(wf_result, name)
    
    return wf_result


def main():
    parser = argparse.ArgumentParser(
        description="Zeros Requiem - SCAF 2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py main.py --symbol GC=F --interval 4h --period 1y
  py main.py --symbol GBPUSD=X --interval 1h --period 6mo
  py main.py --multi forex --interval 4h --period 1y
  py main.py --all --interval 4h --period 1y
  py main.py --walk-forward GC=F --interval 4h --windows 6
        """
    )
    
    # Symbol selection (mutually exclusive)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--symbol', type=str, help='Single trading symbol')
    group.add_argument('--multi', type=str, choices=['gold', 'forex', 'crypto'],
                       help='Run all symbols in an asset class')
    group.add_argument('--all', action='store_true', help='Run all supported symbols')
    group.add_argument('--walk-forward', type=str, metavar='SYMBOL',
                       help='Run walk-forward analysis on a symbol (uses max available data)')
    
    parser.add_argument('--strategy', type=str, default='scaf',
                        choices=['scaf', 'sbrs'],
                        help='Strategy: scaf (SCAF 2.0) or sbrs (SBRS 1.0 Breakout Retest)')
    parser.add_argument('--interval', type=str, default='4h',
                        choices=['1m','5m','15m','30m','1h','4h','1d','1wk'])
    parser.add_argument('--period', type=str, default='1y',
                        choices=['1mo','3mo','6mo','1y','2y','5y','10y'])
    parser.add_argument('--windows', type=int, default=4,
                        help='Number of walk-forward windows (default: 4)')
    parser.add_argument('--capital', type=float, default=10000.0)
    parser.add_argument('--risk', type=float, default=0.01, help='Risk per trade (0.01 = 1%%)')
    parser.add_argument('--no-slippage', action='store_true', help='Disable slippage tax')
    parser.add_argument('--monte-carlo', action='store_true',
                        help='Run Monte Carlo simulation after backtest (10,000 sims)')
    parser.add_argument('--mc-sims', type=int, default=10000,
                        help='Number of Monte Carlo simulations (default: 10000)')
    
    args = parser.parse_args()
    
    # Default to single symbol if nothing specified
    if not args.symbol and not args.multi and not args.all and not args.walk_forward:
        args.symbol = 'GC=F'
    
    if args.walk_forward:
        return run_walk_forward_cmd(args)
    elif args.all:
        return run_all(args)
    elif args.multi:
        return run_multi(args, args.multi)
    else:
        return run_single(args)


if __name__ == "__main__":
    main()
