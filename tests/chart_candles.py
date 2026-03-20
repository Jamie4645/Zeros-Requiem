"""
SBRS 1.1 — Candlestick Trade Charts
Zoomed views with proper OHLC candles showing entries, SL, TP, exits.
Run: py -m tests.chart_candles
"""
import warnings
warnings.filterwarnings('ignore')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates

from src.data.fetcher import fetch
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, TradeStatus
from src.core.risk_manager import risk_config_for_interval

CAPITAL = 10000.0

print("Fetching Gold 1H data (1Y)...")
df = fetch("GC=F", "1h", "1y")
print(f"Loaded {len(df)} candles")

print("Running SBRS analysis...")
setups = analyze_gold_sbrs(df, CAPITAL, 0.01, asset_class='gold')
sbrs_ind = get_sbrs_indicators(df)
risk_config = risk_config_for_interval("1h", 0.01)
result = run_backtest(df, setups, CAPITAL, risk_config, apply_slippage=True, sbrs_indicators=sbrs_ind)

trades = [t for t in result.trades if t.status != TradeStatus.PENDING]
print(f"Total trades: {len(trades)}")


def draw_candlestick_chart(ax, window_df):
    """Draw OHLC candlesticks on an axis."""
    for idx in range(len(window_df)):
        ts = window_df.index[idx]
        o = window_df['Open'].iloc[idx]
        h = window_df['High'].iloc[idx]
        l = window_df['Low'].iloc[idx]
        c = window_df['Close'].iloc[idx]
        
        color = '#26A69A' if c >= o else '#EF5350'
        
        # Wick
        ax.plot([ts, ts], [l, h], color=color, linewidth=0.8)
        # Body
        body_bottom = min(o, c)
        body_height = abs(c - o)
        if body_height < 0.01:
            body_height = 0.5
        rect = Rectangle((mdates.date2num(ts) - 0.015, body_bottom), 
                          0.03, body_height, 
                          facecolor=color, edgecolor=color, linewidth=0.5)
        ax.add_patch(rect)


def annotate_trade(ax, t, df):
    """Draw entry, SL, TP, exit on chart."""
    entry_time = df.index[t.entry_index]
    exit_time = df.index[min(t.exit_index, len(df) - 1)]
    entry_p = t.entry_price
    sl_p = t.setup.stop_loss
    tp_p = t.setup.take_profit
    exit_p = t.exit_price
    is_long = t.direction == 'long'
    is_win = t.pnl > 0
    
    sl_dist = abs(entry_p - sl_p)
    rr = abs(tp_p - entry_p) / sl_dist if sl_dist > 0 else 0
    r_got = t.pnl / (sl_dist * t.position_size) if sl_dist > 0 and t.position_size > 0 else 0
    bars = t.exit_index - t.entry_index
    reason = t.exit_reason if t.exit_reason else t.status.value
    
    # Entry → Exit line
    outcome_color = '#26A69A' if is_win else '#EF5350'
    ax.plot([entry_time, exit_time], [entry_p, exit_p], 
            color=outcome_color, linewidth=2, alpha=0.8, zorder=6)
    
    # Entry horizontal line (blue)
    ax.axhline(y=entry_p, color='#2196F3', linewidth=1, linestyle='-', alpha=0.4, zorder=3)
    
    # SL zone (red shaded)
    if is_long:
        ax.axhspan(sl_p, entry_p, alpha=0.08, color='#EF5350', zorder=1)
    else:
        ax.axhspan(entry_p, sl_p, alpha=0.08, color='#EF5350', zorder=1)
    ax.axhline(y=sl_p, color='#EF5350', linewidth=1.2, linestyle='--', alpha=0.7, zorder=3)
    
    # TP zone (green shaded)
    if is_long:
        ax.axhspan(entry_p, tp_p, alpha=0.06, color='#26A69A', zorder=1)
    else:
        ax.axhspan(tp_p, entry_p, alpha=0.06, color='#26A69A', zorder=1)
    ax.axhline(y=tp_p, color='#26A69A', linewidth=1.2, linestyle='--', alpha=0.7, zorder=3)
    
    # Entry marker
    marker = '^' if is_long else 'v'
    entry_color = '#2196F3' if is_long else '#FF9800'
    ax.scatter(entry_time, entry_p, color=entry_color, marker=marker, 
               s=200, zorder=10, edgecolors='black', linewidths=1)
    
    # Exit marker
    exit_marker = 'D' if is_win else 'X'
    ax.scatter(exit_time, exit_p, color=outcome_color, marker=exit_marker, 
               s=150, zorder=10, edgecolors='black', linewidths=1)
    
    # Labels
    dir_str = "LONG" if is_long else "SHORT"
    ax.annotate(f'ENTRY {dir_str}\n${entry_p:.2f}', 
                xy=(entry_time, entry_p), xytext=(10, 20 if is_long else -30),
                textcoords='offset points', fontsize=7, fontweight='bold',
                color=entry_color, 
                arrowprops=dict(arrowstyle='->', color=entry_color, lw=0.8),
                zorder=11)
    
    ax.annotate(f'SL ${sl_p:.2f}', xy=(entry_time, sl_p), xytext=(-40, -10),
                textcoords='offset points', fontsize=6, color='#EF5350', zorder=11)
    
    ax.annotate(f'TP ${tp_p:.2f} (3R)', xy=(entry_time, tp_p), xytext=(-40, 5),
                textcoords='offset points', fontsize=6, color='#26A69A', zorder=11)
    
    result_str = f"{'WIN' if is_win else 'LOSS'}: ${t.pnl:+.0f} ({r_got:+.2f}R)\n{reason} | {bars} bars"
    ax.annotate(result_str,
                xy=(exit_time, exit_p), xytext=(10, -20 if is_win else 20),
                textcoords='offset points', fontsize=7, fontweight='bold',
                color=outcome_color,
                arrowprops=dict(arrowstyle='->', color=outcome_color, lw=0.8),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=outcome_color, alpha=0.9),
                zorder=11)


# ================================================================
# Generate individual trade charts — 6 best trades
# ================================================================
print("\nGenerating candlestick trade charts...")

# Pick a mix: 3 best wins + 3 different trade types
winners = sorted([t for t in trades if t.pnl > 0], key=lambda x: x.pnl, reverse=True)
losers = sorted([t for t in trades if t.pnl <= 0], key=lambda x: x.pnl)
ma_exits = [t for t in trades if t.exit_reason == 'exit_ma_cross']
be_exits = [t for t in trades if t.exit_reason == 'sl_be' and t.pnl > 0]

# Select 8 interesting trades
selected = []
# Best 3 wins (mix of long/short)
long_wins = [t for t in winners if t.direction == 'long']
short_wins = [t for t in winners if t.direction == 'short']
if long_wins: selected.append(('LONG WIN (Best)', long_wins[0]))
if short_wins: selected.append(('SHORT WIN (Best)', short_wins[0]))
if len(long_wins) > 1: selected.append(('LONG WIN (Runner)', long_wins[1]))
# Best MA cross exit
if ma_exits:
    best_ma = max(ma_exits, key=lambda x: x.pnl)
    selected.append(('MA CROSS EXIT', best_ma))
# Worst loss
if losers: selected.append(('WORST LOSS', losers[0]))
# A typical SL loss
sl_losses = [t for t in trades if t.exit_reason == 'sl' and t.direction == 'long']
if sl_losses: selected.append(('TYPICAL SL (Long)', sl_losses[len(sl_losses)//2]))
# Short loss
short_losses = [t for t in trades if t.exit_reason == 'sl' and t.direction == 'short']
if short_losses: selected.append(('SHORT SL LOSS', short_losses[0]))
# BE save
if be_exits: selected.append(('BREAKEVEN SAVE', be_exits[0]))

n_charts = len(selected)
cols = 2
rows = (n_charts + 1) // 2

fig, axes = plt.subplots(rows, cols, figsize=(24, rows * 7))
fig.suptitle('SBRS 1.1 — Gold 1H Candlestick Trade Analysis', 
             fontsize=18, fontweight='bold', y=1.01)

for idx, (title, t) in enumerate(selected):
    row = idx // cols
    col = idx % cols
    ax = axes[row][col] if rows > 1 else axes[col]
    
    # Window: 10 bars before entry, trade duration + 10 bars after exit
    pad_before = 15
    pad_after = 10
    start = max(0, t.entry_index - pad_before)
    end = min(len(df), t.exit_index + pad_after)
    window = df.iloc[start:end].copy()
    
    if len(window) < 5:
        continue
    
    # Draw candlesticks
    draw_candlestick_chart(ax, window)
    
    # Annotate trade
    annotate_trade(ax, t, df)
    
    # Formatting
    is_win = t.pnl > 0
    sl_dist = abs(t.entry_price - t.setup.stop_loss)
    r_got = t.pnl / (sl_dist * t.position_size) if sl_dist > 0 and t.position_size > 0 else 0
    
    title_color = '#1B5E20' if is_win else '#B71C1C'
    ax.set_title(f'{title}  |  ${t.pnl:+,.0f}  |  {r_got:+.2f}R  |  {t.exit_index - t.entry_index} bars', 
                 fontsize=12, fontweight='bold', color=title_color, pad=10)
    
    ax.set_ylabel('Price ($)', fontsize=9)
    ax.grid(True, alpha=0.15)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b\n%H:%M'))
    ax.tick_params(axis='x', rotation=0, labelsize=7)
    ax.tick_params(axis='y', labelsize=8)
    
    # Set y-axis to show full SL-TP range with padding
    prices = [t.entry_price, t.setup.stop_loss, t.setup.take_profit, t.exit_price]
    ymin = min(prices) - sl_dist * 0.5
    ymax = max(prices) + sl_dist * 0.5
    ax.set_ylim(ymin, ymax)

# Hide empty subplots
total_slots = rows * cols
for idx in range(n_charts, total_slots):
    row = idx // cols
    col = idx % cols
    if rows > 1:
        axes[row][col].set_visible(False)
    else:
        axes[col].set_visible(False)

plt.tight_layout()
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'sbrs_candlestick_trades.png')
plt.savefig(path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {path}")

# ================================================================
# Chart 2: Recent trades cluster (last 30 trades with candles)
# ================================================================
print("Generating recent trades cluster chart...")

recent_trades = sorted(trades, key=lambda x: x.entry_index)[-15:]
if recent_trades:
    start_idx = max(0, recent_trades[0].entry_index - 20)
    end_idx = min(len(df), recent_trades[-1].exit_index + 20)
    window = df.iloc[start_idx:end_idx].copy()
    
    fig, ax = plt.subplots(1, 1, figsize=(28, 10))
    
    draw_candlestick_chart(ax, window)
    
    for t in recent_trades:
        entry_time = df.index[t.entry_index]
        exit_time = df.index[min(t.exit_index, len(df)-1)]
        is_long = t.direction == 'long'
        is_win = t.pnl > 0
        
        # SL/TP lines
        ax.plot([entry_time, exit_time], [t.setup.stop_loss, t.setup.stop_loss], 
                color='#EF5350', linewidth=0.8, linestyle='--', alpha=0.5)
        ax.plot([entry_time, exit_time], [t.setup.take_profit, t.setup.take_profit], 
                color='#26A69A', linewidth=0.8, linestyle='--', alpha=0.5)
        
        # Entry→Exit line
        outcome_color = '#26A69A' if is_win else '#EF5350'
        ax.plot([entry_time, exit_time], [t.entry_price, t.exit_price], 
                color=outcome_color, linewidth=1.5, alpha=0.7)
        
        # Entry marker
        marker = '^' if is_long else 'v'
        color = '#2196F3' if is_long else '#FF9800'
        ax.scatter(entry_time, t.entry_price, color=color, marker=marker, 
                   s=120, zorder=8, edgecolors='black', linewidths=0.8)
        
        # Exit marker
        ax.scatter(exit_time, t.exit_price, color=outcome_color, 
                   marker='D' if is_win else 'X', s=80, zorder=8, 
                   edgecolors='black', linewidths=0.8)
        
        # Small label
        sl_dist = abs(t.entry_price - t.setup.stop_loss)
        r_got = t.pnl / (sl_dist * t.position_size) if sl_dist > 0 and t.position_size > 0 else 0
        d = "L" if is_long else "S"
        ax.annotate(f'{d} {r_got:+.1f}R', xy=(entry_time, t.entry_price),
                    xytext=(5, 8 if is_long else -12), textcoords='offset points',
                    fontsize=6, color=outcome_color, fontweight='bold')
    
    ax.set_title(f'SBRS 1.1 — Last 15 Trades on Gold 1H (Candlestick View)', 
                 fontsize=14, fontweight='bold')
    ax.set_ylabel('Price ($)')
    ax.grid(True, alpha=0.15)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    path2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'sbrs_recent_trades_candles.png')
    plt.savefig(path2, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {path2}")

print("\nDone! Open the PNG files to view.")
