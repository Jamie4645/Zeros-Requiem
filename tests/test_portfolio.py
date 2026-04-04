"""
SBRS 1.1 — Combined Portfolio Test
Single $10K account, 1% risk per trade, all 4 markets simultaneously.
Risk manager handles concurrent exposure limits.
Run: py -m tests.test_portfolio
"""
import warnings
warnings.filterwarnings('ignore')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from src.data.fetcher import fetch, get_symbol_name, detect_asset_class
from src.regimes.sbrs_gold import analyze_gold_sbrs, get_sbrs_indicators
from src.core.engine import run_backtest, BacktestTrade, TradeStatus
from src.core.risk_manager import RiskConfig, risk_config_for_interval
from src.execution.entries import TradeSetup

CAPITAL = 10000.0
RISK_PCT = 0.01

MARKETS = [
    ('GC=F',      '1h', '1y', 'gold'),
    ('^GSPC',     '1h', '1y', 'indices'),
    ('^IXIC',     '1h', '1y', 'indices'),
    ('^GDAXI',    '1h', '1y', 'indices'),
    # Forex REMOVED from SBRS — no consistent edge with breakout-retest logic
]

print("=" * 80)
print("  SBRS 1.1 — COMBINED PORTFOLIO")
print("  Single $10K Account | 1% Risk Per Trade | 4 Markets Simultaneously")
print("=" * 80)

# Step 1: Fetch all data and generate setups
all_setups = []
all_dfs = {}
all_indicators = {}

for symbol, interval, period, asset_class in MARKETS:
    name = get_symbol_name(symbol)
    print(f"\n  [{name}] Fetching {interval} data ({period})...")
    
    try:
        df = fetch(symbol, interval, period)
        print(f"  [{name}] Loaded {len(df)} candles: {df.index[0]} to {df.index[-1]}")
    except Exception as e:
        print(f"  [{name}] FAILED: {e}")
        continue
    
    if len(df) < 50:
        print(f"  [{name}] Not enough data, skipping")
        continue
    
    # Generate setups
    setups = analyze_gold_sbrs(df, CAPITAL, RISK_PCT, asset_class=asset_class, symbol=symbol)
    indicators = get_sbrs_indicators(df)
    
    print(f"  [{name}] {len(setups)} setups generated")
    
    all_dfs[symbol] = df
    all_indicators[symbol] = indicators
    
    for s in setups:
        # Tag the setup with symbol for tracking
        s._portfolio_symbol = symbol
        all_setups.append((symbol, s, df))

if not all_setups:
    print("  No setups generated. Exiting.")
    sys.exit(1)

# Step 2: Merge all setups into a single timeline
# We need to create a unified bar-by-bar simulation
# The simplest approach: collect all setups with their actual timestamps,
# sort by timestamp, then process through a single engine-like loop

print(f"\n  Total setups across all markets: {len(all_setups)}")

# Build a list of (timestamp, symbol, setup) sorted by time
timed_setups = []
for symbol, setup, df in all_setups:
    try:
        ts = df.index[setup.index]
        timed_setups.append((ts, symbol, setup))
    except (IndexError, KeyError):
        pass

timed_setups.sort(key=lambda x: x[0])
print(f"  Setups sorted by timestamp: {len(timed_setups)}")

# Step 3: Simulate portfolio
# Track equity, open trades, risk management
risk_config = RiskConfig(
    risk_per_trade=RISK_PCT,
    max_daily_loss_pct=0.03,
    max_drawdown_pct=0.10,
    max_concurrent_risk_pct=0.08,  # 8% max concurrent risk across all markets
    max_same_direction=4,          # up to 4 same-direction trades (across markets)
    slippage_pips=1.5,
)

from src.core.risk_manager import RiskManager

risk_mgr = RiskManager(risk_config, CAPITAL)
current_capital = CAPITAL
equity_curve = [CAPITAL]
all_trades = []
open_trades = []
trade_counter = 0
blocked_count = 0

# Process each setup in chronological order
for ts, symbol, setup in timed_setups:
    df = all_dfs[symbol]
    i = setup.index
    
    # First, check if any open trades should be closed at this timestamp
    # We need to check all open trades against their respective market's current bar
    for trade in open_trades[:]:
        t_df = all_dfs[trade['symbol']]
        t_idx = trade['current_bar']
        
        # Advance the trade's bar to current time or its data's end
        while t_idx < len(t_df) - 1 and t_df.index[t_idx + 1] <= ts:
            t_idx += 1
            trade['current_bar'] = t_idx
            
            hi = t_df['High'].iloc[t_idx]
            lo = t_df['Low'].iloc[t_idx]
            cl = t_df['Close'].iloc[t_idx]
            bt = trade['trade']
            
            exit_price = None
            
            # Check SL/TP
            if bt.direction == 'long':
                if lo <= bt.stop_loss:
                    exit_price = bt.stop_loss
                elif hi >= bt.take_profit:
                    exit_price = bt.take_profit
            else:
                if hi >= bt.stop_loss:
                    exit_price = bt.stop_loss
                elif lo <= bt.take_profit:
                    exit_price = bt.take_profit
            
            # Check SBRS management (BE, MA cross, structure, timeout)
            if exit_price is None:
                bars_held = t_idx - bt.entry_index
                initial_risk = abs(bt.entry_price - bt.setup.stop_loss)
                
                # Breakeven at 1.5R
                if not bt.stop_moved_to_be and initial_risk > 0:
                    if bt.direction == 'long':
                        bar_profit = hi - bt.entry_price
                    else:
                        bar_profit = bt.entry_price - lo
                    
                    if bar_profit >= 1.5 * initial_risk:
                        be_buffer = 0.1 * initial_risk
                        if bt.direction == 'long':
                            bt.stop_loss = bt.entry_price + be_buffer
                        else:
                            bt.stop_loss = bt.entry_price - be_buffer
                        bt.stop_moved_to_be = True
                
                # Timeout (40 bars)
                if bars_held >= 40:
                    exit_price = cl
                
                # MA cross reversal
                if exit_price is None and t_idx >= 1:
                    ind = all_indicators[trade['symbol']]
                    w_c = ind['wma_1h'].iloc[t_idx]
                    s_c = ind['smma_1h'].iloc[t_idx]
                    w_p = ind['wma_1h'].iloc[t_idx - 1]
                    s_p = ind['smma_1h'].iloc[t_idx - 1]
                    
                    if not (np.isnan(w_c) or np.isnan(s_c) or np.isnan(w_p) or np.isnan(s_p)):
                        if bt.direction == 'long' and w_c < s_c and w_p >= s_p:
                            exit_price = cl
                        elif bt.direction == 'short' and w_c > s_c and w_p <= s_p:
                            exit_price = cl
            
            if exit_price is not None:
                # Apply slippage
                exit_price = risk_mgr.apply_slippage(exit_price,
                    'short' if bt.direction == 'long' else 'long')
                
                bt.exit_price = exit_price
                bt.exit_index = t_idx
                bt.status = TradeStatus.CLOSED_TP if exit_price == bt.take_profit else TradeStatus.CLOSED_SL
                
                if bt.direction == 'long':
                    bt.pnl = (exit_price - bt.entry_price) * bt.position_size
                else:
                    bt.pnl = (bt.entry_price - exit_price) * bt.position_size
                
                current_capital += bt.pnl
                risk_mgr.update_capital(current_capital, bt.pnl)
                equity_curve.append(current_capital)
                open_trades.remove(trade)
                break
    
    # Now process the new setup
    raw_dir = setup.direction
    dir_str = raw_dir.value if hasattr(raw_dir, 'value') else str(raw_dir)
    
    risk_amount = abs(setup.entry_price - setup.stop_loss) * setup.position_size
    can_trade, reason = risk_mgr.can_trade(
        [t['trade'] for t in open_trades], dir_str, risk_amount, ts
    )
    
    if not can_trade:
        blocked_count += 1
        continue
    
    # Apply slippage to entry
    entry_price = risk_mgr.apply_slippage(setup.entry_price, dir_str)
    
    # Recalculate position size based on CURRENT capital (not fixed 10K)
    sl_dist = abs(setup.entry_price - setup.stop_loss)
    if sl_dist <= 0:
        continue
    pos_size = (current_capital * RISK_PCT) / sl_dist
    
    trade_counter += 1
    bt = BacktestTrade(
        trade_id=trade_counter,
        setup=setup,
        direction=dir_str,
        entry_price=entry_price,
        stop_loss=setup.stop_loss,
        take_profit=setup.take_profit,
        position_size=pos_size,
        risk_amount=abs(entry_price - setup.stop_loss) * pos_size,
        regime=setup.regime,
        entry_index=i
    )
    
    all_trades.append(bt)
    open_trades.append({'trade': bt, 'symbol': symbol, 'current_bar': i})

# Close any remaining open trades
for trade in open_trades:
    bt = trade['trade']
    t_df = all_dfs[trade['symbol']]
    last_close = t_df['Close'].iloc[-1]
    bt.exit_price = last_close
    bt.exit_index = len(t_df) - 1
    bt.status = TradeStatus.CLOSED_TIME
    if bt.direction == 'long':
        bt.pnl = (last_close - bt.entry_price) * bt.position_size
    else:
        bt.pnl = (bt.entry_price - last_close) * bt.position_size
    current_capital += bt.pnl
    equity_curve.append(current_capital)

# ================================================================
# RESULTS
# ================================================================
closed = [t for t in all_trades if t.status != TradeStatus.PENDING and t.status != TradeStatus.OPEN]
winners = [t for t in closed if t.pnl > 0]
losers = [t for t in closed if t.pnl <= 0]

total_pnl = sum(t.pnl for t in closed)
wr = len(winners) / len(closed) * 100 if closed else 0
gw = sum(t.pnl for t in winners) if winners else 0
gl = abs(sum(t.pnl for t in losers)) if losers else 0
pf = gw / gl if gl > 0 else float('inf')

eq_arr = np.array(equity_curve)
peak = np.maximum.accumulate(eq_arr)
dd_pct = (peak - eq_arr) / peak * 100
max_dd = np.max(dd_pct)

avg_win = np.mean([t.pnl for t in winners]) if winners else 0
avg_loss = abs(np.mean([t.pnl for t in losers])) if losers else 0

# Per-market breakdown
by_market = {}
for t in closed:
    regime = t.regime
    if regime not in by_market:
        by_market[regime] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
    by_market[regime]['trades'] += 1
    if t.pnl > 0:
        by_market[regime]['wins'] += 1
    by_market[regime]['pnl'] += t.pnl

# Streaks
mws = mls = cw = cl = 0
for t in closed:
    if t.pnl > 0:
        cw += 1; cl = 0; mws = max(mws, cw)
    else:
        cl += 1; cw = 0; mls = max(mls, cl)

print(f"""
{'='*80}
  COMBINED PORTFOLIO RESULTS
  $10,000 Start | 1% Risk/Trade | 4 Markets | 1H Timeframe
{'='*80}

  Total Trades:       {len(closed)}
  Winning Trades:     {len(winners)}
  Losing Trades:      {len(losers)}
  Win Rate:           {wr:.1f}%
  Total PnL:          ${total_pnl:,.2f}
  Total Return:       {total_pnl/CAPITAL*100:.2f}%
  Profit Factor:      {pf:.2f}
  Max Drawdown:       {max_dd:.2f}%
  Final Capital:      ${current_capital:,.2f}
  Avg Win:            ${avg_win:,.2f}
  Avg Loss:           ${avg_loss:,.2f}
  Win/Loss Ratio:     {avg_win/avg_loss:.2f}:1
  Expectancy:         ${total_pnl/len(closed) if closed else 0:,.2f} / trade
  Max Con. Wins:      {mws}
  Max Con. Losses:    {mls}
  Trades Blocked:     {blocked_count} (risk manager)

  --- Per Market ---""")

regime_labels = {
    'sbrs_gold': 'Gold', 'sbrs_indices': 'Indices (combined)',
    'sbrs_forex': 'Forex'
}
for regime, stats in sorted(by_market.items()):
    rwr = stats['wins'] / stats['trades'] * 100 if stats['trades'] > 0 else 0
    label = regime_labels.get(regime, regime)
    print(f"  {label:<20s}: {stats['trades']:>3}t, {rwr:.0f}% WR, ${stats['pnl']:>10,.2f}")

# Separate indices by symbol
print(f"\n  --- Per Symbol ---")
by_symbol = {}
for t in closed:
    sym = getattr(t.setup, '_portfolio_symbol', 'unknown')
    if sym not in by_symbol:
        by_symbol[sym] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
    by_symbol[sym]['trades'] += 1
    if t.pnl > 0:
        by_symbol[sym]['wins'] += 1
    by_symbol[sym]['pnl'] += t.pnl

for sym, stats in sorted(by_symbol.items()):
    name = get_symbol_name(sym)
    rwr = stats['wins'] / stats['trades'] * 100 if stats['trades'] > 0 else 0
    print(f"  {name:<20s}: {stats['trades']:>3}t, {rwr:.0f}% WR, ${stats['pnl']:>10,.2f}")

print(f"""
{'='*80}
  PORTFOLIO TEST COMPLETE
{'='*80}""")
