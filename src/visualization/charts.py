"""
SBRS 1.1 — Visualization Module

Consolidated charting functions for equity curves, trade maps,
session heatmaps, and R-distribution histograms.

All functions save to PNG and return the file path.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from pathlib import Path
from typing import List, Optional, Dict, Any

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / 'charts'


def _ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def plot_equity_curve(
    equity_values: List[float],
    trade_dates: Optional[List] = None,
    title: str = 'SBRS Equity Curve',
    save_path: Optional[str] = None,
    initial_capital: float = 10000.0,
) -> str:
    """
    Plot equity curve with drawdown overlay.

    Args:
        equity_values: List of equity values (one per trade close)
        trade_dates: Optional list of datetime objects for x-axis
        title: Chart title
        save_path: Override save location
        initial_capital: Starting capital for reference line

    Returns:
        Path to saved PNG
    """
    _ensure_output_dir()
    if save_path is None:
        save_path = str(OUTPUT_DIR / 'equity_curve.png')

    eq = np.array(equity_values)
    peak = np.maximum.accumulate(eq)
    drawdown_pct = (peak - eq) / peak * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8),
                                    gridspec_kw={'height_ratios': [3, 1]},
                                    sharex=True)

    x = trade_dates if trade_dates else range(len(eq))

    # Equity
    ax1.fill_between(x, initial_capital, eq,
                     where=eq >= initial_capital, color='#4CAF50', alpha=0.2)
    ax1.fill_between(x, initial_capital, eq,
                     where=eq < initial_capital, color='#F44336', alpha=0.2)
    ax1.plot(x, eq, color='#1565C0', linewidth=1.5)
    ax1.axhline(y=initial_capital, color='gray', linestyle=':', alpha=0.5)
    ax1.set_ylabel('Equity ($)')
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.2)

    final_return = (eq[-1] - initial_capital) / initial_capital * 100
    max_dd = np.max(drawdown_pct)
    ax1.text(0.02, 0.95, f'Final: ${eq[-1]:,.0f} ({final_return:+.1f}%)\nMax DD: {max_dd:.1f}%',
             transform=ax1.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Drawdown
    ax2.fill_between(x, 0, -drawdown_pct, color='#F44336', alpha=0.4)
    ax2.plot(x, -drawdown_pct, color='#C62828', linewidth=0.8)
    ax2.set_ylabel('Drawdown (%)')
    ax2.set_xlabel('Trade #' if trade_dates is None else '')
    ax2.grid(True, alpha=0.2)

    if trade_dates:
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    return save_path


def plot_trades_on_price(
    df: pd.DataFrame,
    trades: List[Any],
    title: str = 'SBRS Trade Map',
    save_path: Optional[str] = None,
) -> str:
    """
    Plot price action with trade entry/exit markers.

    Args:
        df: OHLC DataFrame
        trades: List of BacktestTrade objects (must have entry_index, exit_index,
                entry_price, exit_price, direction, pnl, setup.stop_loss, setup.take_profit)
        title: Chart title
        save_path: Override save location

    Returns:
        Path to saved PNG
    """
    _ensure_output_dir()
    if save_path is None:
        save_path = str(OUTPUT_DIR / 'trade_map.png')

    fig, ax = plt.subplots(1, 1, figsize=(24, 10))

    # Price line with high/low range
    dates = df.index
    ax.plot(dates, df['Close'], color='#555555', linewidth=0.5, alpha=0.7)
    ax.fill_between(dates, df['Low'], df['High'], color='#E0E0E0', alpha=0.3)

    win_count = 0
    loss_count = 0

    for t in trades:
        entry_time = df.index[t.entry_index]
        exit_idx = min(t.exit_index, len(df) - 1)
        exit_time = df.index[exit_idx]
        is_long = t.direction == 'long'
        is_win = t.pnl > 0

        if is_win:
            win_count += 1
        else:
            loss_count += 1

        # Entry marker
        color = '#2196F3' if is_long else '#FF5722'
        marker = '^' if is_long else 'v'
        ax.scatter(entry_time, t.entry_price, color=color, marker=marker,
                   s=60, zorder=5, edgecolors='black', linewidths=0.5)

        # SL/TP lines
        ax.plot([entry_time, exit_time], [t.setup.stop_loss, t.setup.stop_loss],
                color='#F44336', linewidth=0.6, linestyle='--', alpha=0.5)
        ax.plot([entry_time, exit_time], [t.setup.take_profit, t.setup.take_profit],
                color='#4CAF50', linewidth=0.6, linestyle='--', alpha=0.5)

        # Trade outcome line
        outcome_color = '#4CAF50' if is_win else '#F44336'
        ax.plot([entry_time, exit_time], [t.entry_price, t.exit_price],
                color=outcome_color, linewidth=1.2, alpha=0.7)

        # Exit marker
        exit_marker = 'D' if is_win else 'X'
        ax.scatter(exit_time, t.exit_price, color=outcome_color, marker=exit_marker,
                   s=40, zorder=5, edgecolors='black', linewidths=0.5)

    longs = [t for t in trades if t.direction == 'long']
    shorts = [t for t in trades if t.direction == 'short']
    legend_elements = [
        Line2D([0], [0], marker='^', color='w', markerfacecolor='#2196F3', markersize=10,
               label=f'Long ({len(longs)})'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='#FF5722', markersize=10,
               label=f'Short ({len(shorts)})'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#4CAF50', markersize=8,
               label=f'Win ({win_count})'),
        Line2D([0], [0], marker='X', color='w', markerfacecolor='#F44336', markersize=8,
               label=f'Loss ({loss_count})'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel('Price ($)')
    ax.grid(True, alpha=0.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    return save_path


def plot_session_heatmap(
    trades: List[Dict],
    title: str = 'SBRS Session P&L Heatmap',
    save_path: Optional[str] = None,
) -> str:
    """
    Plot P&L by hour-of-day heatmap.

    Args:
        trades: List of trade dicts with 'entry_time' and 'pnl' keys
        title: Chart title
        save_path: Override save location

    Returns:
        Path to saved PNG
    """
    _ensure_output_dir()
    if save_path is None:
        save_path = str(OUTPUT_DIR / 'session_heatmap.png')

    # Aggregate by hour
    hour_pnl = {}
    hour_count = {}
    for t in trades:
        entry_time = t.get('entry_time', '')
        pnl = t.get('pnl', 0)
        try:
            if isinstance(entry_time, str):
                dt = pd.to_datetime(entry_time)
            else:
                dt = entry_time
            hour = dt.hour
        except Exception:
            continue

        hour_pnl[hour] = hour_pnl.get(hour, 0) + pnl
        hour_count[hour] = hour_count.get(hour, 0) + 1

    hours = list(range(24))
    pnls = [hour_pnl.get(h, 0) for h in hours]
    counts = [hour_count.get(h, 0) for h in hours]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # P&L bars
    colors = ['#4CAF50' if p >= 0 else '#F44336' for p in pnls]
    ax1.bar(hours, pnls, color=colors, alpha=0.8, edgecolor='white')
    ax1.axhline(y=0, color='black', linewidth=0.5)
    ax1.set_ylabel('Total P&L ($)')
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.2, axis='y')

    # Highlight blocked session (16-20 GMT)
    ax1.axvspan(16, 20, alpha=0.1, color='red', label='Blocked session (16-20 GMT)')
    ax1.legend(fontsize=9)

    # Trade count bars
    ax2.bar(hours, counts, color='#1565C0', alpha=0.6, edgecolor='white')
    ax2.set_ylabel('Trade Count')
    ax2.set_xlabel('Hour (GMT)')
    ax2.set_xticks(hours)
    ax2.set_xticklabels([f'{h:02d}' for h in hours], fontsize=8)
    ax2.grid(True, alpha=0.2, axis='y')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    return save_path


def plot_r_distribution(
    trades: List[Dict],
    title: str = 'SBRS R-Multiple Distribution',
    save_path: Optional[str] = None,
) -> str:
    """
    Plot histogram of R-multiples.

    Args:
        trades: List of trade dicts with 'entry_price', 'exit_price',
                'original_sl', 'direction' keys
        title: Chart title
        save_path: Override save location

    Returns:
        Path to saved PNG
    """
    _ensure_output_dir()
    if save_path is None:
        save_path = str(OUTPUT_DIR / 'r_distribution.png')

    r_multiples = []
    for t in trades:
        entry = t.get('entry_price', 0)
        exit_p = t.get('exit_price', 0)
        original_sl = t.get('original_sl', 0)
        direction = t.get('direction', 'long')

        initial_risk = abs(entry - original_sl)
        if initial_risk <= 0:
            continue

        if direction == 'long':
            r = (exit_p - entry) / initial_risk
        else:
            r = (entry - exit_p) / initial_risk
        r_multiples.append(r)

    if not r_multiples:
        return save_path

    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    r_arr = np.array(r_multiples)
    colors = ['#4CAF50' if r > 0 else '#F44336' for r in r_arr]

    bins = np.arange(np.floor(min(r_arr)) - 0.5, np.ceil(max(r_arr)) + 1.5, 0.5)
    n, bins_out, patches = ax.hist(r_arr, bins=bins, edgecolor='white', alpha=0.8)

    # Color bars by positive/negative
    for patch, left_edge in zip(patches, bins_out[:-1]):
        if left_edge + 0.25 >= 0:
            patch.set_facecolor('#4CAF50')
        else:
            patch.set_facecolor('#F44336')

    ax.axvline(x=0, color='black', linewidth=1.5)
    ax.axvline(x=np.mean(r_arr), color='#1565C0', linewidth=2, linestyle='--',
               label=f'Mean: {np.mean(r_arr):.2f}R')
    ax.axvline(x=np.median(r_arr), color='#FF9800', linewidth=2, linestyle=':',
               label=f'Median: {np.median(r_arr):.2f}R')

    ax.set_xlabel('R-Multiple')
    ax.set_ylabel('Count')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2, axis='y')

    # Stats box
    wins = sum(1 for r in r_arr if r > 0)
    stats_text = (
        f'Trades: {len(r_arr)}\n'
        f'Wins: {wins} ({wins/len(r_arr)*100:.0f}%)\n'
        f'Mean R: {np.mean(r_arr):.2f}\n'
        f'Best: {np.max(r_arr):.2f}R\n'
        f'Worst: {np.min(r_arr):.2f}R\n'
        f'Expectancy: {np.mean(r_arr):.3f}R'
    )
    ax.text(0.98, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    return save_path
