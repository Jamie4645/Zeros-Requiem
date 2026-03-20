"""
SBRS 1.1 — Full Year Candlestick Trade Map
Splits into quarterly panels so candles are readable.
Run: py -m tests.chart_full_candles
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
from matplotlib.lines import Line2D

from src.data.fetcher import fetch
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, TradeStatus
from src.core.risk_manager import risk_config_for_interval

CAPITAL = 10000.0

print("Fetching Gold 4H data (1Y) for readable candles...")
df = fetch("GC=F", "4h", "1y")
print(f"Loaded {len(df)} 4H candles")

print("Fetching Gold 1H data (1Y) for trade signals...")
df_1h = fetch("GC=F", "1h", "1y")
print(f"Loaded {len(df_1h)} 1H candles")

print("Running SBRS on 1H...")
setups = analyze_gold_sbrs(df_1h, CAPITAL, 0.01, asset_class='gold')
sbrs_ind = get_sbrs_indicators(df_1h)
risk_config = risk_config_for_interval("1h", 0.01)
result = run_backtest(df_1h, setups, CAPITAL, risk_config, apply_slippage=True, sbrs_indicators=sbrs_ind)

trades = [t for t in result.trades if t.status != TradeStatus.PENDING]
print(f"Total trades: {len(trades)}")

# Map 1H trade timestamps to 4H chart
trade_data = []
for t in trades:
    entry_ts = df_1h.index[t.entry_index]
    exit_ts = df_1h.index[min(t.exit_index, len(df_1h)-1)]
    trade_data.append({
        'entry_ts': entry_ts, 'exit_ts': exit_ts,
        'entry_p': t.entry_price, 'exit_p': t.exit_price,
        'sl': t.setup.stop_loss, 'tp': t.setup.take_profit,
        'direction': t.direction, 'pnl': t.pnl,
        'reason': t.exit_reason if t.exit_reason else t.status.value,
        'bars': t.exit_index - t.entry_index,
    })


def draw_candles(ax, data):
    """Draw OHLC candlesticks."""
    width = pd.Timedelta(hours=3)  # 4H candle width
    for i in range(len(data)):
        ts = data.index[i]
        o, h, l, c = data['Open'].iloc[i], data['High'].iloc[i], data['Low'].iloc[i], data['Close'].iloc[i]
        color = '#26A69A' if c >= o else '#EF5350'
        
        # Wick
        ax.plot([ts, ts], [l, h], color=color, linewidth=0.6)
        # Body
        body_bot = min(o, c)
        body_h = max(abs(c - o), 0.5)
        rect = Rectangle((ts - width/2, body_bot), width, body_h,
                          facecolor=color, edgecolor=color, linewidth=0.3)
        ax.add_patch(rect)


# Split into 4 quarters
quarters = []
start = df.index[0]
for q in range(4):
    q_start = start + pd.DateOffset(months=q*3)
    q_end = start + pd.DateOffset(months=(q+1)*3)
    q_df = df[(df.index >= q_start) & (df.index < q_end)]
    q_trades = [t for t in trade_data if t['entry_ts'] >= q_start and t['entry_ts'] < q_end]
    if len(q_df) > 0:
        quarters.append((q_df, q_trades, f"{q_start.strftime('%b %Y')} — {q_end.strftime('%b %Y')}"))

n_quarters = len(quarters)
fig, axes = plt.subplots(n_quarters, 1, figsize=(28, n_quarters * 8))
if n_quarters == 1:
    axes = [axes]

fig.suptitle('SBRS 1.1 — Gold 1H Trades on 4H Candlestick Chart (Full Year)', 
             fontsize=18, fontweight='bold', y=1.005)

for idx, (q_df, q_trades, label) in enumerate(quarters):
    ax = axes[idx]
    
    # Draw 4H candles
    draw_candles(ax, q_df)
    
    # Overlay trades
    wins = 0
    losses = 0
    for t in q_trades:
        is_long = t['direction'] == 'long'
        is_win = t['pnl'] > 0
        entry_ts = t['entry_ts']
        exit_ts = t['exit_ts']
        
        if is_win:
            wins += 1
        else:
            losses += 1
        
        # SL line
        ax.plot([entry_ts, exit_ts], [t['sl'], t['sl']], 
                color='#EF5350', linewidth=0.8, linestyle='--', alpha=0.6)
        
        # TP line
        ax.plot([entry_ts, exit_ts], [t['tp'], t['tp']], 
                color='#26A69A', linewidth=0.8, linestyle='--', alpha=0.6)
        
        # SL/TP shaded zones
        if is_long:
            ax.axhspan(t['sl'], t['entry_p'], xmin=0, xmax=1, alpha=0.0)
            # Use fill_between for localized shading
            ax.fill_between([entry_ts, exit_ts], t['sl'], t['entry_p'], 
                           alpha=0.08, color='#EF5350')
            ax.fill_between([entry_ts, exit_ts], t['entry_p'], t['tp'], 
                           alpha=0.06, color='#26A69A')
        else:
            ax.fill_between([entry_ts, exit_ts], t['entry_p'], t['sl'], 
                           alpha=0.08, color='#EF5350')
            ax.fill_between([entry_ts, exit_ts], t['tp'], t['entry_p'], 
                           alpha=0.06, color='#26A69A')
        
        # Entry → Exit line
        outcome_color = '#26A69A' if is_win else '#EF5350'
        ax.plot([entry_ts, exit_ts], [t['entry_p'], t['exit_p']], 
                color=outcome_color, linewidth=2, alpha=0.8, zorder=6)
        
        # Entry marker
        marker = '^' if is_long else 'v'
        entry_color = '#1565C0' if is_long else '#E65100'
        ax.scatter(entry_ts, t['entry_p'], color=entry_color, marker=marker, 
                   s=140, zorder=10, edgecolors='black', linewidths=0.8)
        
        # Exit marker
        exit_marker = 'D' if is_win else 'X'
        ax.scatter(exit_ts, t['exit_p'], color=outcome_color, marker=exit_marker, 
                   s=100, zorder=10, edgecolors='black', linewidths=0.8)
        
        # R label at entry
        sl_dist = abs(t['entry_p'] - t['sl'])
        r_got = t['pnl'] / (sl_dist * 1) if sl_dist > 0 else 0  # Approximate
        d = "L" if is_long else "S"
        reason_short = {'tp': 'TP', 'sl': 'SL', 'sl_be': 'BE', 
                        'exit_ma_cross': 'MA', 'exit_structure': 'STR',
                        'exit_timeout': 'TO'}.get(t['reason'], t['reason'][:3])
        
        offset_y = 15 if is_long else -18
        ax.annotate(f'{d} ${t["pnl"]:+.0f} [{reason_short}]', 
                    xy=(entry_ts, t['entry_p']),
                    xytext=(5, offset_y), textcoords='offset points',
                    fontsize=6, fontweight='bold', color=outcome_color,
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', 
                             edgecolor=outcome_color, alpha=0.85))
    
    # Quarter stats
    q_pnl = sum(t['pnl'] for t in q_trades)
    ax.set_title(f'{label}  |  {len(q_trades)} trades ({wins}W / {losses}L)  |  PnL: ${q_pnl:+,.0f}', 
                 fontsize=13, fontweight='bold', 
                 color='#1B5E20' if q_pnl > 0 else '#B71C1C' if q_pnl < 0 else '#333',
                 pad=10)
    
    ax.set_ylabel('Gold Price ($)', fontsize=10)
    ax.grid(True, alpha=0.15)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.tick_params(axis='x', rotation=45, labelsize=8)

# Legend on first panel
legend_elements = [
    Line2D([0], [0], marker='^', color='w', markerfacecolor='#1565C0', markersize=10, label='Long Entry'),
    Line2D([0], [0], marker='v', color='w', markerfacecolor='#E65100', markersize=10, label='Short Entry'),
    Line2D([0], [0], marker='D', color='w', markerfacecolor='#26A69A', markersize=8, label='Win Exit'),
    Line2D([0], [0], marker='X', color='w', markerfacecolor='#EF5350', markersize=8, label='Loss Exit'),
    Line2D([0], [0], color='#26A69A', linestyle='--', linewidth=1, label='TP (3R)'),
    Line2D([0], [0], color='#EF5350', linestyle='--', linewidth=1, label='SL'),
]
axes[0].legend(handles=legend_elements, loc='upper left', fontsize=8, 
               framealpha=0.9, ncol=3)

plt.tight_layout()
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'sbrs_full_year_candles.png')
plt.savefig(path, dpi=170, bbox_inches='tight')
plt.close()
print(f"\nSaved: {path}")
print("Done!")
