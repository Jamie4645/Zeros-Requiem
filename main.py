"""
Zeros Requiem — CLI entry point

ACTIVE STRATEGY: ZTT (Zero's True Trade) — intraday Gold, 10m, break-&-retest.
Mechanized ZTT has NO demonstrated edge (PF ceiling ~1.10, realistic cost) — the
live path is the human-in-the-loop SCREENER, not an autonomous backtest. See
CLAUDE.md and knowledge-base/89-ZTT-Rebuild.md before acting on any number below.

RETIRED: SBRS 1.1 / SBRS 2.0. Realistic-fill backtests found no edge on any
instrument (PF 0.52-1.07) — the SBRS 2.0 "7/7 elite benchmarks" track record was
a phantom-fill artifact. Kept only for historical ablation/comparison; do not
treat SBRS output as informative about current edge.

Usage:
    Live screener scan (the actual day-to-day tool):
        py main.py --screener
        py main.py --screener --period 6mo --fresh 12 --backfill

    ZTT mechanized backtest (sanity-check / research only — known no-edge):
        py main.py --strategy ztt_v2 --period 3mo
        py main.py --strategy ztt --period 1y

    SBRS backtest (RETIRED — comparison/ablation only):
        py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2
        py main.py --walk-forward GC=F --interval 1h --windows 8 --strategy sbrs_v2

    Monte Carlo simulation (SBRS path only):
        py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2 --monte-carlo
"""

import argparse
import warnings
warnings.filterwarnings('ignore')

RETIRED_STRATEGIES = ('sbrs_v1', 'sbrs_v2')
ZTT_STRATEGIES = ('ztt', 'ztt_v2')


def run_screener(args):
    """Delegate to the live ZTT screener (the actual active tool — human takes/skips)."""
    from src.live.ztt_screener import scan, DECISIONS, STATE
    from datetime import datetime, timezone

    print(f"""
    ================================================================
      ZERO'S REQUIEM — ZTT LIVE SCREENER (Gold 10m)
    ================================================================
      This is the ACTIVE strategy path. Alerts are logged; YOU decide
      take/skip in {DECISIONS}. Autonomous selection is falsified —
      see CLAUDE.md ZTT v2 banner. F8 forward-test gate: 300 decisions
      or 2026-12-31, whichever comes first.
    ================================================================
    """)
    new = scan(period=args.period, fresh_bars=args.fresh, backfill=args.backfill,
               min_alert_rr=args.min_rr)
    if not new:
        print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC] no new ZTT setups "
              f"(last bar checked written to {STATE}).")
    else:
        print(f"\n{len(new)} new setup(s) logged to {DECISIONS}. Fill in take/skip + reason.")
    return new


def run_ztt_backtest(args):
    """Mechanized ZTT backtest — research/sanity-check only, NOT a live-edge claim.

    Pre-registered result (KB-89/90/93): mechanical selection has no edge
    (PF ceiling ~1.10 at realistic cost). This exists to reproduce that number
    against current code, and for research on the primitives — not to find a
    tradeable autonomous system.
    """
    from src.data.oanda_fetcher import fetch_oanda, is_oanda_available
    from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ
    from analysis.real_trades.metrics import summarize, profit_factor

    if not is_oanda_available():
        print("  ERROR: OANDA credentials not configured — ZTT requires OANDA 10m Gold data.")
        return None

    strategy_label = 'ZTT v2 (session/regime-aware)' if args.strategy == 'ztt_v2' else 'ZTT v1 (frozen primitives)'
    print(f"""
    ================================================================
      ZERO'S REQUIEM — {strategy_label} MECHANIZED BACKTEST
    ================================================================
      Symbol:   GC=F (Gold-only — ZTT freeze)
      Interval: 10m
      Period:   {args.period}
      Capital:  ${args.capital:,.2f}
      Risk:     {args.risk*100:.1f}% per trade
    ----------------------------------------------------------------
      CAVEAT: mechanical ZTT selection has NO pre-registered edge
      (PF ceiling ~1.10, realistic cost, KB-89/93). This run reproduces
      that finding against current code — it is not a live-deployment
      candidate. The live path is `py main.py --screener`.
    ================================================================
    """)

    print("  Fetching Gold 10m from OANDA...")
    df = fetch_oanda('GC=F', '10m', period=args.period)
    print(f"  Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    if args.strategy == 'ztt_v2':
        from src.regimes.ztt_v2 import ZTTV2Params, generate_setups_v2
        params = ZTTV2Params()
        print("  Generating ZTT v2 setups...")
        setups = generate_setups_v2(df, params, apply_gates=True)
    else:
        from src.regimes.ztt import ZTTParams, generate_setups
        params = ZTTParams()
        print("  Generating ZTT v1 setups...")
        setups = generate_setups(df, params, apply_gates=True)

    print(f"  Found {len(setups)} setups")
    atr_v = atr_array(df, params)

    print("  Running honest fill/exit simulation (gap-aware, F7-asserted)...")
    trades, unables = simulate(setups, df, atr_v, one_position=True,
                                risk=args.risk, start_eq=args.capital)
    print(f"  {len(trades)} filled trades, {unables} unable (outlier/gap-collapsed)")

    if not trades:
        print("\n  No trades produced — nothing to summarize.")
        return None

    scorecard = summarize(trades, start_equity=args.capital, benchmark_close=df['Close'])
    pf = profit_factor([t['pnl'] for t in trades])

    print(f"""
    ----------------------------------------------------------------
      RESULTS — {strategy_label}
    ----------------------------------------------------------------
      Trades:            {scorecard['n']}
      Win Rate:          {scorecard['wr']:.1f}%
      Net PnL:           ${scorecard['net_pnl']:,.2f}
      Net R:             {scorecard['net_r']:.2f}R  (mean {scorecard['mean_r']:.3f}R/trade)
      Compounded Return: {scorecard['compounded_return_pct']:.2f}%
      Max Drawdown:      {scorecard['max_dd_pct']:.2f}%
      Information Ratio: {scorecard['information_ratio']:.2f}
      Sortino:           {scorecard['sortino']:.2f}
      Calmar:            {scorecard['calmar']:.2f}
      Profit Factor:     {pf:.2f}  (secondary diagnostic only — see metrics.py)
      Excess Kurtosis:   {scorecard['excess_kurtosis']:.2f} {'** LEAK FLAG **' if scorecard['kurtosis_leak_flag'] else ''}
      vs Buy&Hold IR:    {scorecard.get('buy_hold_info_ratio', float('nan')):.2f} ({'BEATS' if scorecard.get('beats_buy_hold') else 'does NOT beat'} buy&hold)
    ----------------------------------------------------------------
      Reminder: this is a mechanized-selection sanity check, not a
      live-edge claim. See CLAUDE.md ZTT banner for the pre-registered
      no-edge finding this is expected to reproduce.
    ----------------------------------------------------------------""")
    return scorecard


def _analyze_symbol(symbol, df, capital, risk, strategy='sbrs_v1'):
    """Route a symbol to the RETIRED SBRS analyzer with correct asset class."""
    from src.data.fetcher import detect_asset_class
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
        from src.regimes.sbrs_gold import analyze_gold_sbrs
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
    """Run a RETIRED-SBRS backtest on a single symbol. Comparison/ablation only."""
    from src.data.fetcher import fetch, detect_asset_class, get_symbol_name
    from src.core.engine import run_backtest
    from src.core.risk_manager import risk_config_for_interval
    from src.core.monte_carlo import run_monte_carlo, print_monte_carlo_report
    from src.regimes.sbrs_gold import get_sbrs_indicators

    asset_class = detect_asset_class(args.symbol)
    name = get_symbol_name(args.symbol)
    strategy = args.strategy
    strategy_label = 'SBRS 2.0' if strategy == 'sbrs_v2' else 'SBRS 1.1'

    risk_config = risk_config_for_interval(args.interval, args.risk, asset_class, symbol=args.symbol)
    slip_display = 'OFF' if args.no_slippage else f'ON ({risk_config.slippage_pips} pips)'

    print(f"""
    ================================================================
      ZERO'S REQUIEM — {strategy_label} [RETIRED — comparison/ablation only]
    ================================================================
      Symbol:   {args.symbol} ({name})
      Class:    {asset_class}
      Strategy: {strategy_label}
      Interval: {args.interval}
      Period:   {args.period}
      Capital:  ${args.capital:,.2f}
      Risk:     {args.risk*100:.1f}% per trade
      Slippage: {slip_display}
    ----------------------------------------------------------------
      CAVEAT: SBRS is fully retired. Realistic-fill re-validation found
      NO edge on any instrument (PF 0.52-1.07). This is NOT a live
      candidate. Active strategy: py main.py --screener  (ZTT)
    ================================================================
    """)

    print("  Fetching market data...")
    df = fetch(args.symbol, args.interval, args.period)
    print(f"  Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")

    print("  Analyzing...")
    setups = _analyze_symbol(args.symbol, df, args.capital, args.risk, strategy=strategy)
    print(f"  Found {len(setups)} trade setups")

    print("  Running backtest...")

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
    """Run walk-forward analysis on a symbol with longest available data. RETIRED-SBRS only."""
    from src.data.fetcher import fetch, detect_asset_class, get_symbol_name
    from src.core.risk_manager import risk_config_for_interval
    from src.core.walk_forward import run_walk_forward, print_walk_forward_report
    from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators

    symbol = args.walk_forward
    name = get_symbol_name(symbol)
    strategy = args.strategy
    strategy_label = 'SBRS 2.0' if strategy == 'sbrs_v2' else 'SBRS 1.1'

    from src.data.oanda_fetcher import is_oanda_available, is_oanda_instrument
    from src.data.ibkr_fetcher import is_ibkr_available, is_ibkr_instrument
    has_oanda = is_oanda_available() and is_oanda_instrument(symbol)
    has_ibkr = is_ibkr_available() and is_ibkr_instrument(symbol)

    interval = args.interval
    if interval in ('1m', '5m', '10m', '15m', '30m'):
        max_period = '1mo'
    elif interval in ('1h', '4h'):
        max_period = '10y' if (has_oanda or has_ibkr) else '2y'
    else:
        max_period = '10y' if (has_oanda or has_ibkr) else '5y'

    n_windows = args.windows

    asset_class_preview = detect_asset_class(symbol)
    risk_config_preview = risk_config_for_interval(interval, args.risk, asset_class_preview, symbol=symbol)
    slip_display = 'OFF' if args.no_slippage else f'ON ({risk_config_preview.slippage_pips} pips)'

    print(f"""
    ================================================================
      ZERO'S REQUIEM — WALK-FORWARD ANALYSIS ({strategy_label}) [RETIRED — comparison only]
    ================================================================
      Symbol:     {symbol} ({name})
      Strategy:   {strategy_label}
      Interval:   {interval}
      Period:     {max_period} (maximum available)
      Windows:    {n_windows}
      Capital:    ${args.capital:,.2f} (per window)
      Slippage:   {slip_display}
    ----------------------------------------------------------------
      CAVEAT: SBRS is fully retired; pre-2026-07-02 WF scores are ALSO
      known-optimistic (peak-equity-reset bug, R6-5 retracted). Not a
      live candidate. Active strategy: py main.py --screener  (ZTT)
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
        description="Zeros Requiem — active strategy is ZTT (screener); SBRS is RETIRED",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  py main.py --screener
  py main.py --screener --period 6mo --fresh 12 --backfill
  py main.py --strategy ztt_v2 --period 3mo
  py main.py --symbol GC=F --interval 1h --period 10y --strategy sbrs_v2   [RETIRED]
  py main.py --walk-forward GC=F --interval 1h --windows 8 --strategy sbrs_v2   [RETIRED]
        """
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--screener', action='store_true',
                       help='Run the live ZTT screener scan (ACTIVE strategy — Gold 10m)')
    group.add_argument('--symbol', type=str, help='RETIRED SBRS symbol (GC=F, ^GSPC, ^IXIC, ^GDAXI)')
    group.add_argument('--walk-forward', type=str, metavar='SYMBOL',
                       help='RETIRED SBRS walk-forward analysis (uses max available data)')

    # Screener-only options
    parser.add_argument('--fresh', type=int, default=6,
                        help='[--screener] alert setups within the last N bars (default 6)')
    parser.add_argument('--backfill', action='store_true',
                        help='[--screener] alert ALL un-seen setups in the window')
    parser.add_argument('--min-rr', type=float, default=0.5,
                        help='[--screener] suppress alerts below this R:R (default 0.5)')

    parser.add_argument('--interval', type=str, default='1h',
                        choices=['1m', '5m', '10m', '15m', '30m', '1h', '4h', '1d', '1wk'])
    parser.add_argument('--period', type=str, default='1y',
                        choices=['1mo', '3mo', '6mo', '1y', '2y', '5y', '10y'])
    parser.add_argument('--windows', type=int, default=8,
                        help='Number of walk-forward windows (default: 8)')
    parser.add_argument('--capital', type=float, default=10000.0)
    parser.add_argument('--risk', type=float, default=0.01, help='Risk per trade (0.01 = 1%%)')
    parser.add_argument('--no-slippage', action='store_true', help='Disable slippage modelling (SBRS path only)')
    parser.add_argument('--strategy', type=str, default='ztt_v2',
                        choices=['ztt_v2', 'ztt', 'sbrs_v2', 'sbrs_v1'],
                        help="Strategy (default: ztt_v2 — active mechanization; sbrs_* is RETIRED)")
    parser.add_argument('--monte-carlo', action='store_true',
                        help='Run Monte Carlo simulation after backtest (SBRS path only)')
    parser.add_argument('--mc-sims', type=int, default=10000,
                        help='Number of Monte Carlo simulations (default: 10000)')

    args = parser.parse_args()

    if args.screener:
        return run_screener(args)

    if not args.symbol and not args.walk_forward:
        if args.strategy in ZTT_STRATEGIES:
            return run_ztt_backtest(args)
        args.symbol = 'GC=F'

    if args.walk_forward:
        return run_walk_forward_cmd(args)
    elif args.symbol:
        return run_single(args)
    else:
        return run_ztt_backtest(args)


if __name__ == "__main__":
    main()
