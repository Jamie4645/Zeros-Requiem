"""
SBRS 1.1 — Trade Visualization Chart
Shows Gold 1H price action with all trade entries, SL, TP, and outcomes.
Run: py -m tests.chart_trades
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
import matplotlib.dates as mdates
from matplotlib.patches import FancyArrowPatch

from src.data.fetcher import fetch
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, TradeStatus
from src.core.risk_manager import risk_config_for_interval
from src.execution.entries import TradeDirection

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
longs = [t for t in trades if t.direction == 'long']
shorts = [t for t in trades if t.direction == 'short']

print(f"Total trades: {len(trades)} ({len(longs)} longs, {len(shorts)} shorts)")

# ================================================================
# CHART 1: Full year overview with all trade markers
# ================================================================
print("Generating full year overview chart...")

fig, axes = plt.subplots(2, 1, figsize=(24, 14), gridspec_kw={'height_ratios': [4, 1]})

ax = axes[0]

# Plot price as a line (candles too dense for 1Y of 1H)
dates = df.index
ax.plot(dates, df['Close'], color='#555555', linewidth=0.5, alpha=0.7, label='Gold Close')
ax.fill_between(dates, df['Low'], df['High'], color='#E0E0E0', alpha=0.3)

# Plot each trade
for t in trades:
    entry_time = df.index[t.entry_index]
    exit_time = df.index[min(t.exit_index, len(df)-1)]
    entry_p = t.entry_price
    sl_p = t.setup.stop_loss
    tp_p = t.setup.take_profit
    exit_p = t.exit_price
    is_win = t.pnl > 0
    is_long = t.direction == 'long'
    
    # Entry marker
    color = '#2196F3' if is_long else '#FF5722'
    marker = '^' if is_long else 'v'
    ax.scatter(entry_time, entry_p, color=color, marker=marker, s=60, zorder=5, 
               edgecolors='black', linewidths=0.5)
    
    # SL line (red dashed)
    ax.plot([entry_time, exit_time], [sl_p, sl_p], color='#F44336', linewidth=0.6, 
            linestyle='--', alpha=0.5)
    
    # TP line (green dashed)
    ax.plot([entry_time, exit_time], [tp_p, tp_p], color='#4CAF50', linewidth=0.6, 
            linestyle='--', alpha=0.5)
    
    # Trade outcome line (entry to exit)
    outcome_color = '#4CAF50' if is_win else '#F44336'
    ax.plot([entry_time, exit_time], [entry_p, exit_p], color=outcome_color, 
            linewidth=1.2, alpha=0.7)
    
    # Exit marker
    exit_marker = 'D' if is_win else 'X'
    ax.scatter(exit_time, exit_p, color=outcome_color, marker=exit_marker, s=40, 
               zorder=5, edgecolors='black', linewidths=0.5)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='^', color='w', markerfacecolor='#2196F3', markersize=10, label=f'Long Entry ({len(longs)})'),
    Line2D([0], [0], marker='v', color='w', markerfacecolor='#FF5722', markersize=10, label=f'Short Entry ({len(shorts)})'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='#4CAF50', markersize=8, label=f'Win ({len([t for t in trades if t.pnl > 0])})'),
    Line2D([0], [0], marker='X', color='w', markerfacecolor='#F44336', markersize=8, label=f'Loss ({len([t for t in trades if t.pnl <= 0])})'),
    Line2D([0], [0], color='#4CAF50', linestyle='--', linewidth=1, label='TP Level'),
    Line2D([0], [0], color='#F44336', linestyle='--', linewidth=1, label='SL Level'),
]
ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
ax.set_title('SBRS 1.1 — Gold 1H Trade Map (1 Year)', fontsize=16, fontweight='bold')
ax.set_ylabel('Price ($)')
ax.grid(True, alpha=0.2)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

# Equity curve below
ax2 = axes[1]
eq = [CAPITAL]
cap = CAPITAL
trade_dates = [df.index[0]]
for t in sorted(trades, key=lambda x: x.exit_index):
    cap += t.pnl
    eq.append(cap)
    trade_dates.append(df.index[min(t.exit_index, len(df)-1)])

ax2.fill_between(trade_dates, CAPITAL, eq, where=[e >= CAPITAL for e in eq], 
                  color='#4CAF50', alpha=0.3)
ax2.fill_between(trade_dates, CAPITAL, eq, where=[e < CAPITAL for e in eq], 
                  color='#F44336', alpha=0.3)
ax2.plot(trade_dates, eq, color='#2196F3', linewidth=1.5)
ax2.axhline(y=CAPITAL, color='gray', linestyle=':', alpha=0.5)
ax2.set_ylabel('Equity ($)')
ax2.set_title('Equity Curve', fontsize=11)
ax2.grid(True, alpha=0.2)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

plt.tight_layout()
chart1_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'sbrs_trade_map_full.png')
plt.savefig(chart1_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {chart1_path}")

# ================================================================
# CHART 2: Zoomed views — 10 sample trades (5 wins, 5 losses)
# ================================================================
print("Generating sample trade detail charts...")

winners = sorted([t for t in trades if t.pnl > 0], key=lambda x: x.pnl, reverse=True)
losers = sorted([t for t in trades if t.pnl <= 0], key=lambda x: x.pnl)

# Pick best 5 wins and worst 5 losses for detail view
sample_trades = winners[:5] + losers[:5]
sample_trades.sort(key=lambda x: x.entry_index)

n_samples = len(sample_trades)
fig, axes = plt.subplots(2, 5, figsize=(30, 12))
fig.suptitle('SBRS 1.1 — Sample Trade Details (Top 5 Wins + Top 5 Losses)', 
             fontsize=16, fontweight='bold', y=1.02)

for idx, t in enumerate(sample_trades):
    row = 0 if t.pnl > 0 else 1
    col = idx if idx < 5 else idx - 5
    ax = axes[row][col]
    
    # Get 20 bars before entry and 20 after exit
    start = max(0, t.entry_index - 20)
    end = min(len(df), t.exit_index + 20)
    window = df.iloc[start:end]
    
    is_long = t.direction == 'long'
    is_win = t.pnl > 0
    entry_p = t.entry_price
    sl_p = t.setup.stop_loss
    tp_p = t.setup.take_profit
    exit_p = t.exit_price
    entry_time = df.index[t.entry_index]
    exit_time = df.index[min(t.exit_index, len(df)-1)]
    
    # R calculation
    initial_risk = abs(entry_p - sl_p)
    r_achieved = t.pnl / (initial_risk * t.position_size) if initial_risk > 0 and t.position_size > 0 else 0
    
    # Candlestick-style bars
    for i in range(len(window)):
        bar_time = window.index[i]
        o, h, l, c = window['Open'].iloc[i], window['High'].iloc[i], window['Low'].iloc[i], window['Close'].iloc[i]
        color = '#4CAF50' if c >= o else '#F44336'
        ax.plot([bar_time, bar_time], [l, h], color=color, linewidth=0.5)
        ax.plot([bar_time, bar_time], [min(o,c), max(o,c)], color=color, linewidth=2.5)
    
    # Entry line
    ax.axhline(y=entry_p, color='#2196F3', linewidth=1.5, linestyle='-', alpha=0.8, label='Entry')
    
    # SL zone
    ax.axhline(y=sl_p, color='#F44336', linewidth=1.2, linestyle='--', alpha=0.8, label='SL')
    ax.axhspan(min(entry_p, sl_p), max(entry_p, sl_p), alpha=0.08, color='#F44336')
    
    # TP zone
    ax.axhline(y=tp_p, color='#4CAF50', linewidth=1.2, linestyle='--', alpha=0.8, label='TP')
    ax.axhspan(min(entry_p, tp_p), max(entry_p, tp_p), alpha=0.08, color='#4CAF50')
    
    # Entry marker
    entry_color = '#2196F3' if is_long else '#FF5722'
    entry_marker = '^' if is_long else 'v'
    ax.scatter(entry_time, entry_p, color=entry_color, marker=entry_marker, s=120, zorder=10, edgecolors='black', linewidths=1)
    
    # Exit marker
    exit_color = '#4CAF50' if is_win else '#F44336'
    ax.scatter(exit_time, exit_p, color=exit_color, marker='D' if is_win else 'X', s=80, zorder=10, edgecolors='black', linewidths=1)
    
    # Title with details
    dir_str = "LONG" if is_long else "SHORT"
    outcome = "WIN" if is_win else "LOSS"
    reason = t.exit_reason if t.exit_reason else t.status.value
    sl_dist = abs(entry_p - sl_p)
    rr = abs(tp_p - entry_p) / sl_dist if sl_dist > 0 else 0
    bars = t.exit_index - t.entry_index
    
    title_color = '#2E7D32' if is_win else '#C62828'
    ax.set_title(
        f"{dir_str} → {outcome} (${t.pnl:+.0f})\n"
        f"R:R {rr:.1f} | Got {r_achieved:+.2f}R | {bars} bars\n"
        f"Exit: {reason}",
        fontsize=8, color=title_color, fontweight='bold'
    )
    
    ax.tick_params(axis='x', rotation=45, labelsize=6)
    ax.tick_params(axis='y', labelsize=7)
    ax.grid(True, alpha=0.15)

axes[0][0].set_ylabel('TOP 5 WINS', fontsize=11, fontweight='bold', color='#2E7D32')
axes[1][0].set_ylabel('TOP 5 LOSSES', fontsize=11, fontweight='bold', color='#C62828')

plt.tight_layout()
chart2_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'sbrs_trade_details.png')
plt.savefig(chart2_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {chart2_path}")

# ================================================================
# CHART 3: Long vs Short performance comparison
# ================================================================
print("Generating long vs short comparison chart...")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('SBRS 1.1 — Long vs Short Performance', fontsize=14, fontweight='bold')

# PnL distribution
ax = axes[0]
long_pnls = [t.pnl for t in longs]
short_pnls = [t.pnl for t in shorts]
ax.hist(long_pnls, bins=20, alpha=0.6, color='#2196F3', label=f'Longs ({len(longs)})', edgecolor='white')
ax.hist(short_pnls, bins=20, alpha=0.6, color='#FF5722', label=f'Shorts ({len(shorts)})', edgecolor='white')
ax.axvline(x=0, color='black', linewidth=1, linestyle='-')
ax.set_xlabel('PnL ($)')
ax.set_ylabel('Count')
ax.set_title('PnL Distribution')
ax.legend()

# Cumulative PnL
ax = axes[1]
long_cum = np.cumsum([t.pnl for t in sorted(longs, key=lambda x: x.entry_index)])
short_cum = np.cumsum([t.pnl for t in sorted(shorts, key=lambda x: x.entry_index)])
ax.plot(range(len(long_cum)), long_cum, color='#2196F3', linewidth=2, label=f'Longs: ${sum(long_pnls):,.0f}')
ax.plot(range(len(short_cum)), short_cum, color='#FF5722', linewidth=2, label=f'Shorts: ${sum(short_pnls):,.0f}')
ax.axhline(y=0, color='gray', linewidth=0.5, linestyle=':')
ax.set_xlabel('Trade #')
ax.set_ylabel('Cumulative PnL ($)')
ax.set_title('Cumulative PnL by Direction')
ax.legend()

# Win rate & R comparison
ax = axes[2]
long_wr = len([t for t in longs if t.pnl > 0]) / len(longs) * 100 if longs else 0
short_wr = len([t for t in shorts if t.pnl > 0]) / len(shorts) * 100 if shorts else 0

categories = ['Win Rate (%)', 'Avg Win ($)', 'Avg Loss ($)', 'Count']
long_vals = [
    long_wr,
    np.mean([t.pnl for t in longs if t.pnl > 0]) if [t for t in longs if t.pnl > 0] else 0,
    abs(np.mean([t.pnl for t in longs if t.pnl <= 0])) if [t for t in longs if t.pnl <= 0] else 0,
    len(longs)
]
short_vals = [
    short_wr,
    np.mean([t.pnl for t in shorts if t.pnl > 0]) if [t for t in shorts if t.pnl > 0] else 0,
    abs(np.mean([t.pnl for t in shorts if t.pnl <= 0])) if [t for t in shorts if t.pnl <= 0] else 0,
    len(shorts)
]

x = np.arange(len(categories))
width = 0.35
ax.bar(x - width/2, long_vals, width, color='#2196F3', alpha=0.8, label='Longs')
ax.bar(x + width/2, short_vals, width, color='#FF5722', alpha=0.8, label='Shorts')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=9)
ax.set_title('Key Metrics Comparison')
ax.legend()

for i, (lv, sv) in enumerate(zip(long_vals, short_vals)):
    ax.text(i - width/2, lv + 1, f'{lv:.0f}', ha='center', fontsize=8, fontweight='bold', color='#1565C0')
    ax.text(i + width/2, sv + 1, f'{sv:.0f}', ha='center', fontsize=8, fontweight='bold', color='#BF360C')

plt.tight_layout()
chart3_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'sbrs_long_vs_short.png')
plt.savefig(chart3_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {chart3_path}")

# ================================================================
# Print trade summary table
# ================================================================
print(f"\n{'='*90}")
print(f"  TRADE LOG — All {len(trades)} Trades")
print(f"{'='*90}")
print(f"  {'#':>3} | {'Dir':>5} | {'Entry':>10} | {'SL':>10} | {'TP':>10} | {'Exit':>10} | {'R:R':>4} | {'R Got':>6} | {'PnL':>10} | {'Bars':>4} | {'Exit Reason':<15}")
print(f"  {'-'*3}-+-{'-'*5}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*4}-+-{'-'*6}-+-{'-'*10}-+-{'-'*4}-+-{'-'*15}")

for i, t in enumerate(sorted(trades, key=lambda x: x.entry_index)):
    sl_dist = abs(t.entry_price - t.setup.stop_loss)
    rr = abs(t.setup.take_profit - t.entry_price) / sl_dist if sl_dist > 0 else 0
    r_got = t.pnl / (sl_dist * t.position_size) if sl_dist > 0 and t.position_size > 0 else 0
    bars = t.exit_index - t.entry_index
    reason = t.exit_reason if t.exit_reason else t.status.value
    d = "LONG" if t.direction == 'long' else "SHORT"
    
    print(f"  {i+1:>3} | {d:>5} | {t.entry_price:>10.2f} | {t.setup.stop_loss:>10.2f} | {t.setup.take_profit:>10.2f} | {t.exit_price:>10.2f} | {rr:>4.1f} | {r_got:>+5.2f}R | ${t.pnl:>9.2f} | {bars:>4} | {reason:<15}")

print(f"\n{'='*90}")
print(f"  CHARTS COMPLETE")
print(f"{'='*90}")
