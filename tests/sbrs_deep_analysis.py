"""
SBRS 1.0 Deep Analysis — Priorities 1-6
Corrected direction handling. Comprehensive metrics for live deployment decision.
Run: py -m tests.sbrs_deep_analysis
"""
import warnings
warnings.filterwarnings('ignore')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from collections import defaultdict

from src.data.fetcher import fetch
from src.regimes.sbrs_gold import (
    analyze_gold_sbrs, get_sbrs_indicators,
    resample_to_4h, compute_4h_context, map_4h_to_1h,
    WMA_PERIOD, SMMA_PERIOD
)
from src.core.engine import run_backtest, TradeStatus
from src.core.risk_manager import risk_config_for_interval
from src.core.walk_forward import split_into_windows

CAPITAL = 10000.0
N_WINDOWS = 8
RISK_PCT = 0.01

# ================================================================
print("=" * 80)
print("  SBRS 1.0 DEEP ANALYSIS — CORRECTED DIRECTION")
print("  Gold 1H / 10 Years / 8 Windows")
print("=" * 80)

print("\n  Fetching Gold 1H data (10Y via OANDA)...")
df_full = fetch("GC=F", "1h", "10y")
print(f"  Loaded {len(df_full)} candles: {df_full.index[0]} to {df_full.index[-1]}")

risk_config = risk_config_for_interval("1h", RISK_PCT)
windows_data = split_into_windows(df_full, N_WINDOWS, min_bars=100)

# Run all windows, collect everything
all_window_data = []
print(f"\n  Running {len(windows_data)} windows...")

for idx, window_df in enumerate(windows_data):
    try:
        sd = str(window_df.index[0].date())
        ed = str(window_df.index[-1].date())
    except:
        sd = str(window_df.index[0])
        ed = str(window_df.index[-1])
    
    setups = analyze_gold_sbrs(window_df, CAPITAL, RISK_PCT)
    sbrs_ind = get_sbrs_indicators(window_df)
    result = run_backtest(window_df, setups, CAPITAL, risk_config,
                          apply_slippage=True, sbrs_indicators=sbrs_ind)
    
    # Pre-compute 4H trend for this window (ONCE, not per trade)
    trend_ctx = None
    try:
        df_4h = resample_to_4h(window_df)
        if len(df_4h) >= WMA_PERIOD + SMMA_PERIOD:
            df_4h = compute_4h_context(df_4h)
            trend_ctx = map_4h_to_1h(window_df, df_4h)
    except:
        pass
    
    all_window_data.append({
        'wid': idx + 1, 'start': sd, 'end': ed,
        'df': window_df, 'result': result,
        'trend_ctx': trend_ctx
    })
    print(f"    W{idx+1}: {sd} to {ed} — {result.total_trades}t, {result.win_rate:.1f}% WR, ${result.total_pnl:,.2f}")

# Flatten trades
flat_trades = []
for w in all_window_data:
    for t in w['result'].trades:
        if t.status != TradeStatus.PENDING:
            flat_trades.append((t, w))


# ================================================================
# PRIORITY 1: WALK-FORWARD TABLE
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 1: CORRECTED WALK-FORWARD RESULTS")
print("=" * 80)

print(f"\n  {'Window':<8} | {'Period':<28} | {'Trades':>6} | {'WR':>6} | {'PnL':>12} | {'PF':>5} | {'Sharpe':>6}")
print(f"  {'-'*8}-+-{'-'*28}-+-{'-'*6}-+-{'-'*6}-+-{'-'*12}-+-{'-'*5}-+-{'-'*6}")

pnls = []
for w in all_window_data:
    r = w['result']
    pf = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"
    print(f"  W{w['wid']:<6} | {w['start']} to {w['end']} | {r.total_trades:>6} | {r.win_rate:>5.1f}% | ${r.total_pnl:>10,.2f} | {pf:>5} | {r.sharpe_ratio:>6.2f}")
    pnls.append(r.total_pnl)

total_trades = sum(w['result'].total_trades for w in all_window_data)
profitable_w = sum(1 for p in pnls if p > 0)
wrs = [w['result'].win_rate for w in all_window_data if w['result'].total_trades > 0]
pfs = [w['result'].profit_factor for w in all_window_data if w['result'].total_trades > 0 and w['result'].profit_factor < 100]
sharpes = [w['result'].sharpe_ratio for w in all_window_data if w['result'].total_trades > 0]
expects = [w['result'].expectancy for w in all_window_data if w['result'].total_trades > 0]
tpw = [w['result'].total_trades for w in all_window_data]

edge_deg = 0.0
if len(pnls) >= 3:
    try:
        slope, _ = np.polyfit(np.arange(len(pnls)), pnls, 1)
        edge_deg = round(slope, 2)
    except:
        pass

print(f"""
  {'='*80}
    WALK-FORWARD SUMMARY
  {'='*80}
    Consistency Score:    {profitable_w}/{len(pnls)} windows profitable ({profitable_w/len(pnls)*100:.0f}%)
    Avg PnL / Window:    ${np.mean(pnls):,.2f}
    Avg Trades / Window: {np.mean(tpw):.0f}
    Avg Win Rate:        {np.mean(wrs):.1f}%
    Avg Profit Factor:   {np.mean(pfs):.2f}
    Avg Sharpe:          {np.mean(sharpes):.2f}
    Avg Expectancy:      ${np.mean(expects):,.2f} / trade
    Edge Degradation:    ${edge_deg:,.2f} / window ({"stable" if abs(edge_deg) < 50 else "degrading" if edge_deg < -50 else "improving"})
    Best Window:         ${max(pnls):,.2f}
    Worst Window:        ${min(pnls):,.2f}
    Combined PnL:        ${sum(pnls):,.2f}
    Total Trades:        {total_trades}
  {'='*80}""")


# ================================================================
# PRIORITY 2: LONG vs SHORT
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 2: LONG vs SHORT BREAKDOWN (10Y)")
print("=" * 80)

all_t = [t for t, _ in flat_trades]
longs = [t for t in all_t if t.direction == 'long']
shorts = [t for t in all_t if t.direction == 'short']

def dir_stats(trades, label):
    if not trades:
        print(f"\n  {label}: 0 trades")
        return
    winners = [t for t in trades if t.pnl > 0]
    losers = [t for t in trades if t.pnl <= 0]
    wr = len(winners)/len(trades)*100
    gw = sum(t.pnl for t in winners) if winners else 0
    gl = abs(sum(t.pnl for t in losers)) if losers else 0
    pf = gw/gl if gl > 0 else float('inf')
    tp = sum(t.pnl for t in trades)
    r_vals = []
    for t in trades:
        ir = abs(t.setup.entry_price - t.setup.stop_loss)
        if ir > 0 and t.position_size > 0:
            r_vals.append(t.pnl / (ir * t.position_size))
    holds = [t.exit_index - t.entry_index for t in trades]
    print(f"\n  {label}:")
    print(f"    Total trades:      {len(trades)}")
    print(f"    Win rate:          {wr:.1f}%")
    print(f"    Avg R/trade:       {np.mean(r_vals):.3f}R" if r_vals else "    Avg R/trade:       N/A")
    print(f"    Profit Factor:     {pf:.2f}")
    print(f"    Total PnL:         ${tp:,.2f}")
    print(f"    Best trade:        ${max(t.pnl for t in trades):,.2f}")
    print(f"    Worst trade:       ${min(t.pnl for t in trades):,.2f}")
    print(f"    Avg hold time:     {np.mean(holds):.1f} bars" if holds else "")

dir_stats(longs, "LONG TRADES")
dir_stats(shorts, "SHORT TRADES")

lp = sum(t.pnl for t in longs) if longs else 0
sp = sum(t.pnl for t in shorts) if shorts else 0
lwr = len([t for t in longs if t.pnl > 0])/len(longs)*100 if longs else 0
swr = len([t for t in shorts if t.pnl > 0])/len(shorts)*100 if shorts else 0
print(f"\n  Comparison:")
print(f"    More profitable: {'LONG' if lp > sp else 'SHORT'} (${max(lp,sp):,.2f} vs ${min(lp,sp):,.2f})")
print(f"    Higher WR:       {'LONG' if lwr > swr else 'SHORT'} ({max(lwr,swr):.1f}% vs {min(lwr,swr):.1f}%)")

print(f"\n  Per-Window Direction Split:")
print(f"  {'Win':<4} | {'L#':>4} {'L-WR':>6} {'L-PnL':>11} | {'S#':>4} {'S-WR':>6} {'S-PnL':>11}")
for w in all_window_data:
    wt = [t for t in w['result'].trades if t.status != TradeStatus.PENDING]
    wl = [t for t in wt if t.direction == 'long']
    ws = [t for t in wt if t.direction == 'short']
    wlw = len([t for t in wl if t.pnl>0])/len(wl)*100 if wl else 0
    wsw = len([t for t in ws if t.pnl>0])/len(ws)*100 if ws else 0
    print(f"  W{w['wid']:<3} | {len(wl):>4} {wlw:>5.1f}% ${sum(t.pnl for t in wl):>10,.2f} | {len(ws):>4} {wsw:>5.1f}% ${sum(t.pnl for t in ws):>10,.2f}")


# ================================================================
# PRIORITY 3: DRAWDOWN ANALYSIS
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 3: DRAWDOWN ANALYSIS")
print("=" * 80)

eq = [CAPITAL]
cap = CAPITAL
for t in sorted(all_t, key=lambda x: (getattr(x, '_window_id', 0) if hasattr(x, '_window_id') else 0, x.entry_index)):
    cap += t.pnl
    eq.append(cap)

eq_arr = np.array(eq)
pk = np.maximum.accumulate(eq_arr)
dd_pct = (pk - eq_arr) / pk * 100
max_dd = np.max(dd_pct)
max_dd_idx = np.argmax(dd_pct)
pk_idx = np.argmax(eq_arr[:max_dd_idx+1]) if max_dd_idx > 0 else 0

print(f"\n  Max Drawdown:      {max_dd:.2f}%")
print(f"  Peak Equity:       ${eq_arr[pk_idx]:,.2f} (trade #{pk_idx})")
print(f"  Trough Equity:     ${eq_arr[max_dd_idx]:,.2f} (trade #{max_dd_idx})")
print(f"  DD in dollars:     ${eq_arr[pk_idx] - eq_arr[max_dd_idx]:,.2f}")

# Per-window DD
print(f"\n  Per-Window Max Drawdown:")
for w in all_window_data:
    print(f"    W{w['wid']}: {w['result'].max_drawdown_pct:.2f}%")

# Count episodes
eps = 0
in_dd = False
for d in dd_pct:
    if d > 10 and not in_dd:
        eps += 1
        in_dd = True
    elif d < 1:
        in_dd = False
print(f"\n  Drawdown episodes > 10%: {eps}")

eps15 = 0
in_dd = False
for d in dd_pct:
    if d > 15 and not in_dd:
        eps15 += 1
        in_dd = True
    elif d < 1:
        in_dd = False
print(f"  Drawdown episodes > 15%: {eps15}")


# ================================================================
# PRIORITY 4: LOSING/WEAK WINDOWS
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 4: LOSING & WEAK WINDOW ANALYSIS")
print("=" * 80)

for w in all_window_data:
    r = w['result']
    if r.total_pnl > 1000:
        continue  # Skip strong windows
    
    wt = [t for t in r.trades if t.status != TradeStatus.PENDING]
    wl = [t for t in wt if t.direction == 'long']
    ws = [t for t in wt if t.direction == 'short']
    
    # Streaks
    max_ls = 0
    cur = 0
    for t in sorted(wt, key=lambda x: x.entry_index):
        if t.pnl <= 0:
            cur += 1
            max_ls = max(max_ls, cur)
        else:
            cur = 0
    
    # Exit breakdown
    exits = defaultdict(int)
    for t in wt:
        exits[t.exit_reason or t.status.value] += 1
    
    durations = [t.exit_index - t.entry_index for t in wt]
    
    status = "LOSING" if r.total_pnl <= 0 else "WEAK"
    print(f"\n  --- W{w['wid']} ({status}: ${r.total_pnl:,.2f}) ---")
    print(f"  Period:             {w['start']} to {w['end']}")
    print(f"  Trades:             {r.total_trades}")
    print(f"  Win Rate:           {r.win_rate:.1f}%")
    print(f"  Max Losing Streak:  {max_ls}")
    print(f"  Avg Hold Time:      {np.mean(durations):.1f} bars" if durations else "")
    print(f"  Max Drawdown:       {r.max_drawdown_pct:.2f}%")
    lp = sum(t.pnl for t in wl)
    sp = sum(t.pnl for t in ws)
    lww = len([t for t in wl if t.pnl>0])/len(wl)*100 if wl else 0
    sww = len([t for t in ws if t.pnl>0])/len(ws)*100 if ws else 0
    print(f"  Longs:  {len(wl)}t, {lww:.1f}% WR, ${lp:,.2f}")
    print(f"  Shorts: {len(ws)}t, {sww:.1f}% WR, ${sp:,.2f}")
    print(f"  Exit Reasons:")
    for reason, count in sorted(exits.items()):
        lbl = {'tp':'TP','sl':'SL','sl_be':'SL(BE)','exit_ma_cross':'MA Cross',
               'exit_structure':'Structure','exit_timeout':'Timeout'}.get(reason, reason)
        print(f"    {lbl}: {count}")


# ================================================================
# PRIORITY 5: DISTRIBUTION
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 5: TRADE DISTRIBUTION")
print("=" * 80)

# 5a: By session
print("\n  --- By Session (4h blocks, GMT) ---")
sess = defaultdict(lambda: {'n': 0, 'w': 0, 'pnl': 0.0})
for t, w in flat_trades:
    try:
        h = w['df'].index[t.entry_index].hour
        b = f"{(h//4)*4:02d}-{(h//4)*4+4:02d}"
    except:
        b = "??"
    sess[b]['n'] += 1
    if t.pnl > 0: sess[b]['w'] += 1
    sess[b]['pnl'] += t.pnl

print(f"  {'Session':>8} | {'Trades':>6} | {'WR':>6} | {'Avg PnL':>10} | {'Total PnL':>12}")
for b in sorted(sess.keys()):
    d = sess[b]
    wr = d['w']/d['n']*100 if d['n'] else 0
    print(f"  {b:>8} | {d['n']:>6} | {wr:>5.1f}% | ${d['pnl']/d['n']:>9,.2f} | ${d['pnl']:>11,.2f}")

# 5b: By 4H trend (using pre-computed trend_ctx)
print(f"\n  --- By 4H Trend Context ---")
trend_b = defaultdict(lambda: {'n': 0, 'w': 0, 'pnl': 0.0})
for t, w in flat_trades:
    tc = w.get('trend_ctx')
    if tc is not None and t.entry_index < len(tc):
        tr = tc.iloc[t.entry_index]
    else:
        tr = 'unknown'
    trend_b[tr]['n'] += 1
    if t.pnl > 0: trend_b[tr]['w'] += 1
    trend_b[tr]['pnl'] += t.pnl

print(f"  {'Trend':>10} | {'Trades':>6} | {'WR':>6} | {'Avg PnL':>10} | {'Total PnL':>12}")
for tr in ['bullish', 'bearish', 'neutral', 'unknown']:
    if tr in trend_b:
        d = trend_b[tr]
        wr = d['w']/d['n']*100 if d['n'] else 0
        print(f"  {tr:>10} | {d['n']:>6} | {wr:>5.1f}% | ${d['pnl']/d['n']:>9,.2f} | ${d['pnl']:>11,.2f}")


# ================================================================
# PRIORITY 6: EXIT REASONS
# ================================================================
print("\n" + "=" * 80)
print("  PRIORITY 6: EXIT REASON ANALYSIS")
print("=" * 80)

ex = defaultdict(lambda: {'n': 0, 'w': 0, 'pnl': 0.0, 'rs': []})
for t, _ in flat_trades:
    reason = t.exit_reason if t.exit_reason else t.status.value
    ex[reason]['n'] += 1
    if t.pnl > 0: ex[reason]['w'] += 1
    ex[reason]['pnl'] += t.pnl
    ir = abs(t.setup.entry_price - t.setup.stop_loss)
    if ir > 0 and t.position_size > 0:
        ex[reason]['rs'].append(t.pnl / (ir * t.position_size))

total_n = len(flat_trades)
labels = {'tp': 'Hit TP (3R)', 'sl': 'Hit SL (initial)', 'sl_be': 'Hit SL (breakeven)',
          'exit_ma_cross': 'MA Cross Exit', 'exit_structure': 'Structure Break',
          'exit_timeout': 'Max Hold Timeout', 'closed_time': 'End of Window'}

print(f"\n  {'Exit Reason':<20} | {'Trades':>6} | {'WR':>6} | {'Avg R':>7} | {'Avg PnL':>10} | {'Total PnL':>12} | {'%':>5}")
print(f"  {'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*7}-+-{'-'*10}-+-{'-'*12}-+-{'-'*5}")
for key in ['tp', 'sl', 'sl_be', 'exit_ma_cross', 'exit_structure', 'exit_timeout', 'closed_time']:
    if key in ex:
        d = ex[key]
        wr = d['w']/d['n']*100 if d['n'] else 0
        ar = np.mean(d['rs']) if d['rs'] else 0
        ap = d['pnl']/d['n'] if d['n'] else 0
        pct = d['n']/total_n*100 if total_n else 0
        print(f"  {labels.get(key,key):<20} | {d['n']:>6} | {wr:>5.1f}% | {ar:>6.2f}R | ${ap:>9,.2f} | ${d['pnl']:>11,.2f} | {pct:>4.1f}%")

# Other/unknown
for key, d in ex.items():
    if key not in labels:
        wr = d['w']/d['n']*100 if d['n'] else 0
        ar = np.mean(d['rs']) if d['rs'] else 0
        ap = d['pnl']/d['n'] if d['n'] else 0
        pct = d['n']/total_n*100 if total_n else 0
        print(f"  {key:<20} | {d['n']:>6} | {wr:>5.1f}% | {ar:>6.2f}R | ${ap:>9,.2f} | ${d['pnl']:>11,.2f} | {pct:>4.1f}%")


# ================================================================
# RISK METRICS
# ================================================================
print("\n" + "=" * 80)
print("  RISK-ADJUSTED METRICS (10Y COMBINED)")
print("=" * 80)

if all_t:
    winners = [t for t in all_t if t.pnl > 0]
    losers = [t for t in all_t if t.pnl <= 0]
    aw = np.mean([t.pnl for t in winners]) if winners else 0
    al = abs(np.mean([t.pnl for t in losers])) if losers else 0
    wr_all = len(winners)/len(all_t)*100
    e = (wr_all/100*aw) - ((100-wr_all)/100*al)
    
    mws = mls = cw = cl = 0
    for t in sorted(all_t, key=lambda x: x.entry_index):
        if t.pnl > 0:
            cw += 1; cl = 0; mws = max(mws, cw)
        else:
            cl += 1; cw = 0; mls = max(mls, cl)
    
    tp = sum(t.pnl for t in all_t)
    try:
        days = (df_full.index[-1] - df_full.index[0]).days
    except:
        days = 1
    
    print(f"""
    Trades:              {len(all_t)}
    Win Rate:            {wr_all:.1f}%
    Avg Win:             ${aw:,.2f}
    Avg Loss:            ${al:,.2f}
    Win/Loss Ratio:      {aw/al:.2f}:1 (need >1.0)
    Expectancy:          ${e:,.2f} / trade
    Max Consec. Wins:    {mws}
    Max Consec. Losses:  {mls}
    Max Drawdown:        {max_dd:.2f}%
    Combined PnL:        ${tp:,.2f}
    Profit/Day:          ${tp/days:,.2f}
    """)


# ================================================================
# EQUITY CURVE CHART
# ================================================================
print("  Generating equity curve chart...")
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [3, 1]})
    
    x = range(len(eq))
    axes[0].plot(x, eq, color='#2196F3', linewidth=1.2, label='Equity')
    axes[0].plot(x, pk[:len(eq)], color='#4CAF50', linewidth=0.8, alpha=0.5, linestyle='--', label='Peak')
    axes[0].fill_between(x, eq, pk[:len(eq)],
                          where=[e < p for e, p in zip(eq, pk[:len(eq)])],
                          color='#F44336', alpha=0.3, label='Drawdown')
    axes[0].axhline(y=CAPITAL, color='gray', linestyle=':', alpha=0.5)
    axes[0].set_title('SBRS 1.0 Gold 1H — Equity Curve (10Y, Corrected Direction)', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Equity ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    axes[1].fill_between(range(len(dd_pct)), 0, -dd_pct[:len(eq)], color='#F44336', alpha=0.5)
    axes[1].axhline(y=-10, color='orange', linestyle='--', alpha=0.7, label='-10%')
    axes[1].axhline(y=-15, color='red', linestyle='--', alpha=0.7, label='-15%')
    axes[1].set_ylabel('DD %')
    axes[1].set_xlabel('Trade #')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    cp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sbrs_equity_curve.png')
    plt.savefig(cp, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {cp}")
except Exception as e:
    print(f"  Chart error: {e}")

print("\n" + "=" * 80)
print("  ANALYSIS COMPLETE")
print("=" * 80)
