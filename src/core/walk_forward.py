"""
Walk-Forward Testing Framework for SCAF 2.0

Priority 5: Splits data into sequential non-overlapping windows and runs
the full backtest on each, measuring whether the edge persists across
different time periods.

Since SCAF 2.0 is rule-based (not optimised per-window), walk-forward
here means: "does the same strategy work in every period, or was it
only profitable due to a specific market condition?"

Key outputs:
- Per-window results (trades, WR, PnL, PF, Sharpe)
- Consistency score (% of windows profitable)
- Edge stability (is performance degrading over time?)
- Aggregate statistics across all windows
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field

from .engine import run_backtest, BacktestResult
from .risk_manager import RiskConfig
from ..execution.entries import TradeSetup


@dataclass
class WindowResult:
    """Result for a single walk-forward window."""
    window_id: int
    start_date: str
    end_date: str
    bars: int
    result: BacktestResult


@dataclass
class WalkForwardResult:
    """Complete walk-forward analysis result."""
    windows: List[WindowResult]
    total_windows: int = 0
    profitable_windows: int = 0
    consistency_score: float = 0.0      # % of windows that are profitable
    avg_pnl_per_window: float = 0.0
    avg_trades_per_window: float = 0.0
    avg_win_rate: float = 0.0
    avg_profit_factor: float = 0.0
    avg_sharpe: float = 0.0
    avg_expectancy: float = 0.0
    total_trades: int = 0
    total_pnl: float = 0.0
    edge_degradation: float = 0.0       # Slope of PnL across windows (negative = degrading)
    worst_window_pnl: float = 0.0
    best_window_pnl: float = 0.0


def split_into_windows(
    df: pd.DataFrame,
    n_windows: int = 4,
    min_bars: int = 100
) -> List[pd.DataFrame]:
    """
    Split a DataFrame into N sequential non-overlapping windows.
    
    Args:
        df: OHLCV DataFrame
        n_windows: Number of windows to create
        min_bars: Minimum bars per window (skip if too small)
    
    Returns:
        List of DataFrames, one per window
    """
    total_bars = len(df)
    bars_per_window = total_bars // n_windows
    
    if bars_per_window < min_bars:
        # Reduce window count to meet minimum
        n_windows = max(2, total_bars // min_bars)
        bars_per_window = total_bars // n_windows
    
    windows = []
    for i in range(n_windows):
        start = i * bars_per_window
        # Last window gets any remaining bars
        end = (i + 1) * bars_per_window if i < n_windows - 1 else total_bars
        window_df = df.iloc[start:end].copy()
        if len(window_df) >= min_bars:
            windows.append(window_df)
    
    return windows


def run_walk_forward(
    df: pd.DataFrame,
    analyze_fn: Callable,
    n_windows: int = 4,
    initial_capital: float = 10000.0,
    risk_pct: float = 0.01,
    apply_slippage: bool = True,
    min_bars: int = 100,
    sbrs_indicator_fn: Optional[Callable] = None
) -> WalkForwardResult:
    """
    Run walk-forward analysis on a single symbol.
    
    Splits the data into sequential windows and runs the full
    regime analysis + backtest on each independently.
    
    Args:
        df: Full OHLCV DataFrame (use longest available period)
        analyze_fn: The regime analysis function (e.g., analyze_gold)
        n_windows: Number of time windows
        initial_capital: Starting capital per window
        risk_pct: Risk per trade
        apply_slippage: Whether to model slippage
        min_bars: Minimum bars per window
        sbrs_indicator_fn: Optional function to compute SBRS indicators per window
                           (pass get_sbrs_indicators for SBRS strategy)
    
    Returns:
        WalkForwardResult with per-window and aggregate statistics
    """
    windows_data = split_into_windows(df, n_windows, min_bars)
    
    window_results: List[WindowResult] = []
    risk_config = RiskConfig(risk_per_trade=risk_pct)
    
    for idx, window_df in enumerate(windows_data):
        # Get date range for this window
        try:
            start_date = str(window_df.index[0].date())
            end_date = str(window_df.index[-1].date())
        except (AttributeError, IndexError):
            start_date = str(window_df.index[0])
            end_date = str(window_df.index[-1])
        
        # Run regime analysis on this window
        setups = analyze_fn(window_df, initial_capital, risk_pct)
        
        # Compute SBRS indicators for this window if needed
        sbrs_ind = sbrs_indicator_fn(window_df) if sbrs_indicator_fn else None
        
        # Run backtest on this window
        result = run_backtest(
            window_df, setups, initial_capital,
            risk_config, apply_slippage,
            sbrs_indicators=sbrs_ind
        )
        
        window_results.append(WindowResult(
            window_id=idx + 1,
            start_date=start_date,
            end_date=end_date,
            bars=len(window_df),
            result=result
        ))
    
    # ============================================================
    # Aggregate statistics
    # ============================================================
    total_windows = len(window_results)
    if total_windows == 0:
        return WalkForwardResult(windows=[], total_windows=0)
    
    profitable = sum(1 for w in window_results if w.result.total_pnl > 0)
    consistency = profitable / total_windows * 100
    
    pnls = [w.result.total_pnl for w in window_results]
    trades_counts = [w.result.total_trades for w in window_results]
    win_rates = [w.result.win_rate for w in window_results if w.result.total_trades > 0]
    pf_values = [w.result.profit_factor for w in window_results
                 if w.result.total_trades > 0 and w.result.profit_factor < float('inf')]
    sharpe_values = [w.result.sharpe_ratio for w in window_results
                     if w.result.total_trades > 0]
    expect_values = [w.result.expectancy for w in window_results
                     if w.result.total_trades > 0]
    
    # Edge degradation: linear regression slope of PnL across windows
    # Negative slope = edge is weakening over time
    edge_degradation = 0.0
    if len(pnls) >= 3:
        x = np.arange(len(pnls))
        try:
            slope, _ = np.polyfit(x, pnls, 1)
            edge_degradation = round(slope, 2)
        except (np.linalg.LinAlgError, ValueError):
            edge_degradation = 0.0
    
    return WalkForwardResult(
        windows=window_results,
        total_windows=total_windows,
        profitable_windows=profitable,
        consistency_score=round(consistency, 1),
        avg_pnl_per_window=round(np.mean(pnls), 2) if pnls else 0.0,
        avg_trades_per_window=round(np.mean(trades_counts), 1) if trades_counts else 0.0,
        avg_win_rate=round(np.mean(win_rates), 1) if win_rates else 0.0,
        avg_profit_factor=round(np.mean(pf_values), 2) if pf_values else 0.0,
        avg_sharpe=round(np.mean(sharpe_values), 2) if sharpe_values else 0.0,
        avg_expectancy=round(np.mean(expect_values), 2) if expect_values else 0.0,
        total_trades=sum(trades_counts),
        total_pnl=round(sum(pnls), 2),
        edge_degradation=edge_degradation,
        worst_window_pnl=round(min(pnls), 2) if pnls else 0.0,
        best_window_pnl=round(max(pnls), 2) if pnls else 0.0
    )


def print_walk_forward_report(wf: WalkForwardResult, symbol_name: str = "") -> None:
    """Print a formatted walk-forward analysis report."""
    title = f"WALK-FORWARD ANALYSIS - {symbol_name}" if symbol_name else "WALK-FORWARD ANALYSIS"
    print(f"""
    ================================================================
      {title}
      Windows: {wf.total_windows}  |  Total Trades: {wf.total_trades}
    ================================================================
    """)
    
    # Per-window table
    print("      Window  | Period                     | Trades | WR    | PnL        | PF   | Sharpe")
    print("      --------|----------------------------|--------|-------|------------|------|-------")
    for w in wf.windows:
        r = w.result
        pf_str = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
        print(f"      W{w.window_id:<5d} | {w.start_date} to {w.end_date} | {r.total_trades:6d} | {r.win_rate:4.1f}% | ${r.total_pnl:>9,.2f} | {pf_str:>4s} | {r.sharpe_ratio:>5.2f}")
    
    # Summary
    print(f"""
    ================================================================
      WALK-FORWARD SUMMARY
    ================================================================
      Consistency Score:    {wf.consistency_score:.0f}% ({wf.profitable_windows}/{wf.total_windows} windows profitable)
      Avg PnL / Window:    ${wf.avg_pnl_per_window:,.2f}
      Avg Trades / Window: {wf.avg_trades_per_window:.0f}
      Avg Win Rate:        {wf.avg_win_rate:.1f}%
      Avg Profit Factor:   {wf.avg_profit_factor:.2f}
      Avg Sharpe:          {wf.avg_sharpe:.2f}
      Avg Expectancy:      ${wf.avg_expectancy:,.2f} / trade
      Edge Degradation:    ${wf.edge_degradation:,.2f} / window ({"stable" if abs(wf.edge_degradation) < 50 else "degrading" if wf.edge_degradation < -50 else "improving"})
      Best Window:         ${wf.best_window_pnl:,.2f}
      Worst Window:        ${wf.worst_window_pnl:,.2f}
      Combined PnL:        ${wf.total_pnl:,.2f}
    ================================================================
    """)
