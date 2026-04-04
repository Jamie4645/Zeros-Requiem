"""
Run all pipeline strategies against all available markets.
Fetches data via Yahoo Finance and uses the pipeline's BacktestRunner.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import yfinance as yf
from strategy_pipeline.backtesting.bt_runner import BacktestRunner

# Markets to test
MARKETS = {
    'GC=F': 'Gold',
    '^GSPC': 'S&P 500',
    '^IXIC': 'NASDAQ',
    '^GDAXI': 'DAX',
}

# Strategy files
STRATEGY_DIR = os.path.join(os.path.dirname(__file__), 'output', 'strategies')
STRATEGIES = [
    'turtle_breakout.py',
    'ema_trend_following.py',
    'schwartz_ma_pullback.py',
    'sperandeo_age_reversal.py',
    'driehaus_momentum.py',
    'trout_risk_rules.py',
]


def fetch_data(symbol, interval='1h', period='2y'):
    """Fetch OHLCV data from Yahoo Finance."""
    print(f"  Fetching {MARKETS[symbol]} ({symbol})...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        # Try daily if hourly fails
        print(f"    1H empty, trying daily...")
        df = ticker.history(period='10y', interval='1d')
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    # Keep only OHLCV
    cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
    df = df[cols]
    print(f"    Got {len(df)} bars ({df.index[0].strftime('%Y-%m-%d') if len(df) > 0 else 'N/A'} to {df.index[-1].strftime('%Y-%m-%d') if len(df) > 0 else 'N/A'})")
    return df


def run_all():
    runner = BacktestRunner(initial_capital=100_000, commission_pct=0.001, slippage_pct=0.0005)

    # Fetch all market data
    print("=" * 70)
    print("FETCHING MARKET DATA")
    print("=" * 70)
    market_data = {}
    for symbol in MARKETS:
        try:
            df = fetch_data(symbol)
            if len(df) >= 100:
                market_data[symbol] = df
            else:
                print(f"    SKIPPED: Only {len(df)} bars")
        except Exception as e:
            print(f"    ERROR: {e}")

    # Run all strategies against all markets
    print("\n" + "=" * 70)
    print("RUNNING BACKTESTS")
    print("=" * 70)

    results = []
    for strat_file in STRATEGIES:
        strat_path = os.path.join(STRATEGY_DIR, strat_file)
        strat_name = strat_file.replace('.py', '')

        for symbol, df in market_data.items():
            market_name = MARKETS[symbol]
            try:
                result = runner.run(strat_path, df.copy(), risk_pct=0.01)
                results.append({
                    'strategy': strat_name,
                    'market': market_name,
                    'trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'total_pnl': result.total_pnl,
                    'return_pct': result.total_return_pct,
                    'max_dd': result.max_drawdown_pct,
                    'sharpe': result.sharpe_ratio,
                    'profit_factor': result.profit_factor,
                    'avg_win': result.avg_win,
                    'avg_loss': result.avg_loss,
                    'avg_hold': result.avg_hold_bars,
                    'max_consec_wins': result.max_consecutive_wins,
                    'max_consec_losses': result.max_consecutive_losses,
                })
                status = "OK" if result.total_trades > 0 else "NO TRADES"
                print(f"  {strat_name:30s} x {market_name:10s} -> {result.total_trades:4d} trades | "
                      f"WR: {result.win_rate:5.1%} | PnL: ${result.total_pnl:>10,.0f} | "
                      f"Sharpe: {result.sharpe_ratio:6.2f} | PF: {result.profit_factor:5.2f}")
            except Exception as e:
                print(f"  {strat_name:30s} x {market_name:10s} -> ERROR: {e}")
                results.append({
                    'strategy': strat_name,
                    'market': market_name,
                    'trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'return_pct': 0,
                    'max_dd': 0,
                    'sharpe': 0,
                    'profit_factor': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'avg_hold': 0,
                    'max_consec_wins': 0,
                    'max_consec_losses': 0,
                })

    # Build results DataFrame
    df_results = pd.DataFrame(results)

    # Print ranked results
    print("\n" + "=" * 70)
    print("RANKED RESULTS (by Sharpe Ratio)")
    print("=" * 70)

    # Filter to strategies with trades
    has_trades = df_results[df_results['trades'] > 0].copy()
    if has_trades.empty:
        print("No strategies produced trades!")
        return df_results

    ranked = has_trades.sort_values('sharpe', ascending=False)
    print(f"\n{'Rank':<5} {'Strategy':<28} {'Market':<10} {'Trades':<7} {'WR':<7} "
          f"{'PnL':>10} {'Return':>8} {'MaxDD':>8} {'Sharpe':>7} {'PF':>6}")
    print("-" * 106)

    for i, (_, row) in enumerate(ranked.iterrows(), 1):
        print(f"{i:<5} {row['strategy']:<28} {row['market']:<10} {row['trades']:<7.0f} "
              f"{row['win_rate']:<7.1%} {row['total_pnl']:>10,.0f} "
              f"{row['return_pct']:>7.1%} {row['max_dd']:>7.1%} "
              f"{row['sharpe']:>7.2f} {row['profit_factor']:>6.2f}")

    # Summary by strategy (average across markets)
    print("\n" + "=" * 70)
    print("STRATEGY AVERAGES (across all markets)")
    print("=" * 70)

    strat_avg = has_trades.groupby('strategy').agg({
        'trades': 'sum',
        'win_rate': 'mean',
        'total_pnl': 'sum',
        'return_pct': 'mean',
        'max_dd': 'mean',
        'sharpe': 'mean',
        'profit_factor': 'mean',
    }).sort_values('sharpe', ascending=False)

    print(f"\n{'Strategy':<28} {'Tot Trades':<11} {'Avg WR':<8} {'Tot PnL':>10} "
          f"{'Avg Ret':>8} {'Avg DD':>8} {'Avg Sharpe':>10} {'Avg PF':>8}")
    print("-" * 101)

    for name, row in strat_avg.iterrows():
        print(f"{name:<28} {row['trades']:<11.0f} {row['win_rate']:<8.1%} "
              f"{row['total_pnl']:>10,.0f} {row['return_pct']:>7.1%} "
              f"{row['max_dd']:>7.1%} {row['sharpe']:>10.2f} {row['profit_factor']:>8.2f}")

    # Summary by market
    print("\n" + "=" * 70)
    print("MARKET AVERAGES (across all strategies)")
    print("=" * 70)

    mkt_avg = has_trades.groupby('market').agg({
        'trades': 'sum',
        'win_rate': 'mean',
        'total_pnl': 'sum',
        'sharpe': 'mean',
        'profit_factor': 'mean',
    }).sort_values('sharpe', ascending=False)

    print(f"\n{'Market':<12} {'Tot Trades':<11} {'Avg WR':<8} {'Tot PnL':>10} "
          f"{'Avg Sharpe':>10} {'Avg PF':>8}")
    print("-" * 60)

    for name, row in mkt_avg.iterrows():
        print(f"{name:<12} {row['trades']:<11.0f} {row['win_rate']:<8.1%} "
              f"{row['total_pnl']:>10,.0f} {row['sharpe']:>10.2f} {row['profit_factor']:>8.2f}")

    # Elite benchmark check
    print("\n" + "=" * 70)
    print("ELITE BENCHMARK CHECK (Sharpe >= 1.5, PF >= 1.5, DD <= 15%)")
    print("=" * 70)

    elite = has_trades[
        (has_trades['sharpe'] >= 1.5) &
        (has_trades['profit_factor'] >= 1.5) &
        (has_trades['max_dd'] >= -0.15) &
        (has_trades['trades'] >= 10)
    ]

    if elite.empty:
        print("\nNo strategy-market combos meet ALL elite benchmarks.")
        print("Closest contenders:")
        # Show top 5 by sharpe that have >10 trades
        contenders = has_trades[has_trades['trades'] >= 10].nlargest(5, 'sharpe')
        for _, row in contenders.iterrows():
            flags = []
            if row['sharpe'] < 1.5: flags.append(f"Sharpe {row['sharpe']:.2f} < 1.5")
            if row['profit_factor'] < 1.5: flags.append(f"PF {row['profit_factor']:.2f} < 1.5")
            if row['max_dd'] < -0.15: flags.append(f"DD {row['max_dd']:.1%} > 15%")
            print(f"  {row['strategy']:28s} x {row['market']:10s} — Missing: {', '.join(flags) if flags else 'QUALIFIES'}")
    else:
        print(f"\n{len(elite)} combos meet elite benchmarks:")
        for _, row in elite.iterrows():
            print(f"  {row['strategy']:28s} x {row['market']:10s} — "
                  f"Sharpe: {row['sharpe']:.2f}, PF: {row['profit_factor']:.2f}, DD: {row['max_dd']:.1%}")

    # Save results
    output_path = os.path.join(os.path.dirname(__file__), 'output', 'reports', 'backtest_results.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_results.to_csv(output_path, index=False)
    print(f"\nResults saved to: {output_path}")

    return df_results


if __name__ == '__main__':
    run_all()
