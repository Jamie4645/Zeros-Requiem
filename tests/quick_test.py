"""
SCAF 2.0 Quick Test -- All Regimes

Tests Gold, Forex, and Crypto regimes on 1D, 4H, and 1H data.
Run: py -m tests.quick_test
"""

import warnings
warnings.filterwarnings('ignore')

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.fetcher import fetch
from src.regimes.gold import analyze_gold
from src.regimes.forex import analyze_forex
from src.regimes.crypto import analyze_crypto
from src.core.engine import run_backtest
from src.core.risk_manager import RiskConfig

CAPITAL = 10000.0

print("=" * 65)
print("  SCAF 2.0 - Gold Regime Quick Test")
print("=" * 65)

# Test 1: Gold 1D / 2 Years
print("\n--- Gold 1D / 2 Years ---")
print("Fetching data...")
df_1d = fetch("GC=F", "1d", "2y")
print(f"Loaded {len(df_1d)} candles")

print("Analyzing Gold regime...")
setups_1d = analyze_gold(df_1d, CAPITAL)
print(f"Found {len(setups_1d)} trade setups")

if setups_1d:
    for s in setups_1d[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:.2f} | RR={s.risk_reward:.2f} | Df={s.displacement_df:.1f}")

print("Running backtest...")
result_1d = run_backtest(df_1d, setups_1d, CAPITAL)

print(f"\nRESULTS (Gold 1D):")
print(f"  Trades:       {result_1d.total_trades}")
print(f"  Win Rate:     {result_1d.win_rate:.1f}%")
print(f"  Total PnL:    ${result_1d.total_pnl:,.2f}")
print(f"  Profit Factor:{result_1d.profit_factor:.2f}")
print(f"  Max Drawdown: {result_1d.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_1d.final_capital:,.2f}")

if result_1d.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_1d.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

if result_1d.risk_stats:
    rs = result_1d.risk_stats
    if rs.get('total_blocked', 0) > 0:
        print(f"  Risk blocked: {rs['total_blocked']} trades")

# Test 2: Gold 4H / 1 Year
print("\n--- Gold 4H / 1 Year ---")
print("Fetching data...")
df_4h = fetch("GC=F", "4h", "1y")
print(f"Loaded {len(df_4h)} candles")

print("Analyzing Gold regime...")
setups_4h = analyze_gold(df_4h, CAPITAL)
print(f"Found {len(setups_4h)} trade setups")

if setups_4h:
    for s in setups_4h[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:.2f} | RR={s.risk_reward:.2f}")

print("Running backtest...")
result_4h = run_backtest(df_4h, setups_4h, CAPITAL)

print(f"\nRESULTS (Gold 4H):")
print(f"  Trades:       {result_4h.total_trades}")
print(f"  Win Rate:     {result_4h.win_rate:.1f}%")
print(f"  Total PnL:    ${result_4h.total_pnl:,.2f}")
print(f"  Profit Factor:{result_4h.profit_factor:.2f}")
print(f"  Max Drawdown: {result_4h.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_4h.final_capital:,.2f}")

if result_4h.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_4h.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

# P7: Gold 1H REMOVED — edge doesn't exist on 1H (33% WR, PF 0.98, -$104).
# Sweep+FVG architecture is calibrated for 4H+ institutional flow.
# Gold trades on 4H + Daily only.

# ============================================================
# Test 3: EUR/USD 4H / 1 Year
# ============================================================
print("\n--- EUR/USD 4H / 1 Year ---")
print("Fetching data...")
df_fx = fetch("EURUSD=X", "4h", "1y")
print(f"Loaded {len(df_fx)} candles")

print("Analyzing Forex regime...")
setups_fx = analyze_forex(df_fx, CAPITAL)
print(f"Found {len(setups_fx)} trade setups")

if setups_fx:
    for s in setups_fx[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:.5f} | RR={s.risk_reward:.2f} | Df={s.displacement_df:.1f}")

print("Running backtest...")
result_fx = run_backtest(df_fx, setups_fx, CAPITAL)

print(f"\nRESULTS (EUR/USD 4H):")
print(f"  Trades:       {result_fx.total_trades}")
print(f"  Win Rate:     {result_fx.win_rate:.1f}%")
print(f"  Total PnL:    ${result_fx.total_pnl:,.2f}")
print(f"  Profit Factor:{result_fx.profit_factor:.2f}")
print(f"  Max Drawdown: {result_fx.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_fx.final_capital:,.2f}")

if result_fx.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_fx.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

if result_fx.risk_stats.get('total_blocked', 0) > 0:
    print(f"  Risk blocked: {result_fx.risk_stats['total_blocked']} trades")

# ============================================================
# Test 3b: EUR/USD 1H / 6 Months (more signals, higher resolution)
# ============================================================
print("\n--- EUR/USD 1H / 6 Months ---")
print("Fetching data...")
df_fx_1h = fetch("EURUSD=X", "1h", "6mo")
print(f"Loaded {len(df_fx_1h)} candles")

print("Analyzing Forex regime...")
setups_fx_1h = analyze_forex(df_fx_1h, CAPITAL)
print(f"Found {len(setups_fx_1h)} trade setups")

if setups_fx_1h:
    for s in setups_fx_1h[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:.5f} | RR={s.risk_reward:.2f} | Df={s.displacement_df:.1f}")

print("Running backtest...")
result_fx_1h = run_backtest(df_fx_1h, setups_fx_1h, CAPITAL)

print(f"\nRESULTS (EUR/USD 1H):")
print(f"  Trades:       {result_fx_1h.total_trades}")
print(f"  Win Rate:     {result_fx_1h.win_rate:.1f}%")
print(f"  Total PnL:    ${result_fx_1h.total_pnl:,.2f}")
print(f"  Profit Factor:{result_fx_1h.profit_factor:.2f}")
print(f"  Max Drawdown: {result_fx_1h.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_fx_1h.final_capital:,.2f}")

if result_fx_1h.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_fx_1h.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

if result_fx_1h.risk_stats.get('total_blocked', 0) > 0:
    print(f"  Risk blocked: {result_fx_1h.risk_stats['total_blocked']} trades")

# ============================================================
# Test 4: EUR/USD 1D / 2 Years
# ============================================================
print("\n--- EUR/USD 1D / 2 Years ---")
print("Fetching data...")
df_fxd = fetch("EURUSD=X", "1d", "2y")
print(f"Loaded {len(df_fxd)} candles")

print("Analyzing Forex regime...")
setups_fxd = analyze_forex(df_fxd, CAPITAL)
print(f"Found {len(setups_fxd)} trade setups")

if setups_fxd:
    for s in setups_fxd[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:.5f} | RR={s.risk_reward:.2f}")

print("Running backtest...")
result_fxd = run_backtest(df_fxd, setups_fxd, CAPITAL)

print(f"\nRESULTS (EUR/USD 1D):")
print(f"  Trades:       {result_fxd.total_trades}")
print(f"  Win Rate:     {result_fxd.win_rate:.1f}%")
print(f"  Total PnL:    ${result_fxd.total_pnl:,.2f}")
print(f"  Profit Factor:{result_fxd.profit_factor:.2f}")
print(f"  Max Drawdown: {result_fxd.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_fxd.final_capital:,.2f}")

if result_fxd.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_fxd.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

# ============================================================
# Test 5: BTC-USD 4H / 1 Year
# ============================================================
print("\n--- BTC-USD 4H / 1 Year ---")
print("Fetching data...")
df_btc = fetch("BTC-USD", "4h", "1y")
print(f"Loaded {len(df_btc)} candles")

print("Analyzing Crypto regime...")
setups_btc = analyze_crypto(df_btc, CAPITAL)
print(f"Found {len(setups_btc)} trade setups")

if setups_btc:
    for s in setups_btc[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:,.2f} | RR={s.risk_reward:.2f} | Df={s.displacement_df:.1f}")

print("Running backtest...")
result_btc = run_backtest(df_btc, setups_btc, CAPITAL)

print(f"\nRESULTS (BTC-USD 4H):")
print(f"  Trades:       {result_btc.total_trades}")
print(f"  Win Rate:     {result_btc.win_rate:.1f}%")
print(f"  Total PnL:    ${result_btc.total_pnl:,.2f}")
print(f"  Profit Factor:{result_btc.profit_factor:.2f}")
print(f"  Max Drawdown: {result_btc.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_btc.final_capital:,.2f}")

if result_btc.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_btc.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

if result_btc.risk_stats.get('total_blocked', 0) > 0:
    print(f"  Risk blocked: {result_btc.risk_stats['total_blocked']} trades")

# ============================================================
# Test 5b: BTC-USD 1H / 6 Months (more signals, higher resolution)
# ============================================================
print("\n--- BTC-USD 1H / 6 Months ---")
print("Fetching data...")
df_btc_1h = fetch("BTC-USD", "1h", "6mo")
print(f"Loaded {len(df_btc_1h)} candles")

print("Analyzing Crypto regime...")
setups_btc_1h = analyze_crypto(df_btc_1h, CAPITAL)
print(f"Found {len(setups_btc_1h)} trade setups")

if setups_btc_1h:
    for s in setups_btc_1h[:5]:
        print(f"  {s.regime} | {s.direction} | entry=${s.entry_price:,.2f} | RR={s.risk_reward:.2f} | Df={s.displacement_df:.1f}")

print("Running backtest...")
result_btc_1h = run_backtest(df_btc_1h, setups_btc_1h, CAPITAL)

print(f"\nRESULTS (BTC-USD 1H):")
print(f"  Trades:       {result_btc_1h.total_trades}")
print(f"  Win Rate:     {result_btc_1h.win_rate:.1f}%")
print(f"  Total PnL:    ${result_btc_1h.total_pnl:,.2f}")
print(f"  Profit Factor:{result_btc_1h.profit_factor:.2f}")
print(f"  Max Drawdown: {result_btc_1h.max_drawdown_pct:.2f}%")
print(f"  Final Capital:${result_btc_1h.final_capital:,.2f}")

if result_btc_1h.regime_breakdown:
    print(f"  Regimes:")
    for regime, stats in result_btc_1h.regime_breakdown.items():
        wr = stats['wins'] / stats['count'] * 100 if stats['count'] > 0 else 0
        print(f"    {regime}: {stats['count']}t, {wr:.0f}%WR, ${stats['pnl']:,.2f}")

if result_btc_1h.risk_stats.get('total_blocked', 0) > 0:
    print(f"  Risk blocked: {result_btc_1h.risk_stats['total_blocked']} trades")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 65)
print("  ALL REGIMES SUMMARY")
print("=" * 65)
print(f"\n  {'Regime':<25} {'Trades':>7} {'WR':>6} {'PnL':>12} {'PF':>6} {'MaxDD':>7}")
print(f"  {'_'*25} {'_'*7} {'_'*6} {'_'*12} {'_'*6} {'_'*7}")

results = [
    ("Gold 1D", result_1d),
    ("Gold 4H", result_4h),
    # P7: Gold 1H removed (no edge)
    ("EUR/USD 4H (Killzone)", result_fx),
    ("EUR/USD 1H (Killzone)", result_fx_1h),
    ("EUR/USD 1D", result_fxd),
    ("BTC 4H (Compression)", result_btc),
    ("BTC 1H (Compression)", result_btc_1h),
]

total_pnl = 0
total_trades = 0
for name, r in results:
    print(f"  {name:<25} {r.total_trades:>7} {r.win_rate:>5.1f}% {f'${r.total_pnl:,.2f}':>12} {r.profit_factor:>5.2f} {r.max_drawdown_pct:>6.2f}%")
    total_pnl += r.total_pnl
    total_trades += r.total_trades

print(f"  {'_'*25} {'_'*7} {'_'*6} {'_'*12}")
print(f"  {'COMBINED':<25} {total_trades:>7} {'':>6} {f'${total_pnl:,.2f}':>12}")

print("\n" + "=" * 65)
print("  QUICK TEST COMPLETE")
print("=" * 65)
