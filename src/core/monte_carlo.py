"""
Monte Carlo Simulation

Evaluates the robustness of a trading edge by resampling from
historical trade results to generate thousands of synthetic equity curves.

Key question: "Given the statistical profile of my trades,
what is the probability of experiencing a catastrophic drawdown?"

Elite Benchmark: < 5% probability of 20% drawdown.

Usage:
    from src.core.monte_carlo import run_monte_carlo, print_monte_carlo_report
    mc = run_monte_carlo(backtest_result.trades, initial_capital=10000)
    print_monte_carlo_report(mc)
"""

import numpy as np
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    n_simulations: int
    n_trades: int
    # Drawdown analysis
    median_max_drawdown_pct: float      # 50th percentile max DD
    p95_max_drawdown_pct: float         # 95th percentile max DD (worst 5%)
    p99_max_drawdown_pct: float         # 99th percentile max DD (worst 1%)
    prob_15pct_drawdown: float          # Prob of hitting 15% DD (our limit)
    prob_20pct_drawdown: float          # Prob of hitting 20% DD (Elite Benchmark)
    prob_30pct_drawdown: float          # Prob of catastrophic 30% DD
    # PnL analysis
    median_final_pnl: float
    p5_final_pnl: float                # 5th percentile (worst case)
    p95_final_pnl: float               # 95th percentile (best case)
    mean_final_pnl: float
    prob_profitable: float             # % of sims that end profitable
    # Streak analysis
    median_max_consecutive_losses: int
    p95_max_consecutive_losses: int     # Worst-case losing streak
    # Risk of ruin
    prob_50pct_drawdown: float          # Probability of losing half the account
    # Bootstrap method (2026-07-02 audit: IID understates tail DD)
    method: str = 'block'
    block_size: int = 0


def run_monte_carlo(
    trades: list,
    initial_capital: float = 10000.0,
    n_simulations: int = 10000,
    n_trades_per_sim: Optional[int] = None,
    seed: Optional[int] = None,
    method: str = 'block',
    block_size: Optional[int] = None
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation on trade results.

    Resamples from actual trade PnLs with replacement to generate
    synthetic equity curves and measure tail risk.

    Args:
        trades: List of BacktestTrade objects (must have .pnl attribute)
        initial_capital: Starting capital for each simulation
        n_simulations: Number of synthetic paths to generate (10000 = standard)
        n_trades_per_sim: Trades per simulation (default: same as input)
        seed: Random seed for reproducibility
        method: 'block' (default) = circular moving-block bootstrap, which
            preserves the losing-streak autocorrelation of the real trade
            sequence; 'iid' = the pre-2026-07-02 per-trade shuffle. The audit
            found IID destroys loss clustering and UNDERSTATES Prob(20%DD) —
            the exact gate every promotion leaned on. Use 'iid' only for
            comparison against historical numbers.
        block_size: block length for method='block'. Default: ~2*n^(1/3),
            floored at 5 (a standard dependent-bootstrap block scale).

    Returns:
        MonteCarloResult with comprehensive risk statistics
    """
    # Extract PnLs from trades
    pnls = np.array([t.pnl for t in trades if hasattr(t, 'pnl')])
    
    if len(pnls) < 10:
        print(f"  WARNING: Only {len(pnls)} trades — Monte Carlo results unreliable (need 30+)")
    
    if len(pnls) < 3:
        print(f"  ERROR: Too few trades ({len(pnls)}) for Monte Carlo simulation")
        return MonteCarloResult(
            n_simulations=0, n_trades=len(pnls),
            median_max_drawdown_pct=0, p95_max_drawdown_pct=0,
            p99_max_drawdown_pct=0, prob_15pct_drawdown=0,
            prob_20pct_drawdown=0, prob_30pct_drawdown=0,
            median_final_pnl=0, p5_final_pnl=0, p95_final_pnl=0,
            mean_final_pnl=0, prob_profitable=0,
            median_max_consecutive_losses=0, p95_max_consecutive_losses=0,
            prob_50pct_drawdown=0
        )
    
    if seed is not None:
        np.random.seed(seed)
    
    n_trades = n_trades_per_sim if n_trades_per_sim else len(pnls)

    # ============================================================
    # Vectorised Monte Carlo: resample all simulations at once
    # Shape: (n_simulations, n_trades)
    # ============================================================
    if method == 'block':
        # Circular moving-block bootstrap: sample whole consecutive runs of
        # trades (wrapping at the end) so losing streaks survive resampling.
        if block_size is None:
            block_size = max(5, int(round(2 * len(pnls) ** (1.0 / 3.0))))
        block_size = max(1, min(block_size, len(pnls)))
        n_blocks = int(np.ceil(n_trades / block_size))
        starts = np.random.randint(0, len(pnls), size=(n_simulations, n_blocks))
        offsets = np.arange(block_size)
        indices = (starts[:, :, None] + offsets[None, None, :]) % len(pnls)
        indices = indices.reshape(n_simulations, n_blocks * block_size)[:, :n_trades]
    elif method == 'iid':
        block_size = 1
        indices = np.random.randint(0, len(pnls), size=(n_simulations, n_trades))
    else:
        raise ValueError(f"Unknown Monte Carlo method: {method!r} (use 'block' or 'iid')")
    sim_pnls = pnls[indices]  # (n_simulations, n_trades)
    
    # Cumulative equity curves
    cum_pnls = np.cumsum(sim_pnls, axis=1)  # (n_simulations, n_trades)
    equity_curves = initial_capital + cum_pnls
    
    # ============================================================
    # Max drawdown per simulation
    # ============================================================
    running_peak = np.maximum.accumulate(equity_curves, axis=1)
    drawdowns_pct = (running_peak - equity_curves) / running_peak * 100
    max_drawdowns = np.max(drawdowns_pct, axis=1)  # (n_simulations,)
    
    # ============================================================
    # Final PnL per simulation
    # ============================================================
    final_pnls = cum_pnls[:, -1]  # (n_simulations,)
    
    # ============================================================
    # Max consecutive losses per simulation (requires loop per sim)
    # Optimised: vectorise the win/loss detection, loop for streaks
    # ============================================================
    win_loss = (sim_pnls <= 0).astype(int)  # 1 = loss, 0 = win
    max_con_losses = np.zeros(n_simulations, dtype=int)
    
    # Efficient streak calculation using diff-based approach
    for sim_idx in range(n_simulations):
        losses = win_loss[sim_idx]
        if np.sum(losses) == 0:
            max_con_losses[sim_idx] = 0
            continue
        
        # Find streaks: diff detects transitions
        # Pad with 0 at start and end to catch edge streaks
        padded = np.concatenate(([0], losses, [0]))
        diffs = np.diff(padded)
        starts = np.where(diffs == 1)[0]
        ends = np.where(diffs == -1)[0]
        
        if len(starts) > 0 and len(ends) > 0:
            streaks = ends - starts
            max_con_losses[sim_idx] = np.max(streaks)
    
    # ============================================================
    # Compute statistics
    # ============================================================
    return MonteCarloResult(
        n_simulations=n_simulations,
        n_trades=n_trades,
        # Drawdown
        median_max_drawdown_pct=round(float(np.median(max_drawdowns)), 2),
        p95_max_drawdown_pct=round(float(np.percentile(max_drawdowns, 95)), 2),
        p99_max_drawdown_pct=round(float(np.percentile(max_drawdowns, 99)), 2),
        prob_15pct_drawdown=round(float(np.mean(max_drawdowns >= 15) * 100), 2),
        prob_20pct_drawdown=round(float(np.mean(max_drawdowns >= 20) * 100), 2),
        prob_30pct_drawdown=round(float(np.mean(max_drawdowns >= 30) * 100), 2),
        # PnL
        median_final_pnl=round(float(np.median(final_pnls)), 2),
        p5_final_pnl=round(float(np.percentile(final_pnls, 5)), 2),
        p95_final_pnl=round(float(np.percentile(final_pnls, 95)), 2),
        mean_final_pnl=round(float(np.mean(final_pnls)), 2),
        prob_profitable=round(float(np.mean(final_pnls > 0) * 100), 2),
        # Streaks
        median_max_consecutive_losses=int(np.median(max_con_losses)),
        p95_max_consecutive_losses=int(np.percentile(max_con_losses, 95)),
        # Risk of ruin
        prob_50pct_drawdown=round(float(np.mean(max_drawdowns >= 50) * 100), 2),
        method=method,
        block_size=int(block_size),
    )


def print_monte_carlo_report(mc: MonteCarloResult, symbol_name: str = "") -> None:
    """Print a formatted Monte Carlo analysis report."""
    title = f"MONTE CARLO ANALYSIS - {symbol_name}" if symbol_name else "MONTE CARLO ANALYSIS"
    
    # Determine Elite Benchmark status
    elite_status = "PASS" if mc.prob_20pct_drawdown < 5.0 else "FAIL"
    risk_status = "PASS" if mc.prob_15pct_drawdown < 10.0 else "CAUTION"
    
    method_str = (f"block bootstrap (L={mc.block_size})" if mc.method == 'block'
                  else "IID bootstrap (understates streak risk)")
    print(f"""
    ================================================================
      {title}
      Simulations: {mc.n_simulations:,}  |  Trades/Sim: {mc.n_trades}  |  {method_str}
    ================================================================
    
      --- Drawdown Risk ---
      Median Max DD:        {mc.median_max_drawdown_pct:.2f}%
      95th Percentile DD:   {mc.p95_max_drawdown_pct:.2f}%
      99th Percentile DD:   {mc.p99_max_drawdown_pct:.2f}%
      
      Prob of 15% DD:       {mc.prob_15pct_drawdown:.2f}%  [{risk_status}]
      Prob of 20% DD:       {mc.prob_20pct_drawdown:.2f}%  [Elite: {elite_status}]
      Prob of 30% DD:       {mc.prob_30pct_drawdown:.2f}%
      Prob of 50% DD:       {mc.prob_50pct_drawdown:.2f}%  (risk of ruin)
      
      --- Profit Distribution ---
      Median Final PnL:     ${mc.median_final_pnl:>10,.2f}
      Mean Final PnL:       ${mc.mean_final_pnl:>10,.2f}
      5th Percentile:       ${mc.p5_final_pnl:>10,.2f}  (worst 5%)
      95th Percentile:      ${mc.p95_final_pnl:>10,.2f}  (best 5%)
      Prob Profitable:      {mc.prob_profitable:.1f}%
      
      --- Losing Streaks ---
      Median Max Streak:    {mc.median_max_consecutive_losses} trades
      95th Percentile:      {mc.p95_max_consecutive_losses} trades  (prepare for this)
    
    ================================================================""")
