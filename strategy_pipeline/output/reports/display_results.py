import pandas as pd

df = pd.read_csv('strategy_pipeline/output/reports/backtest_correct_markets.csv')
df = df.sort_values('sharpe', ascending=False)

print("=" * 160)
print(f"{'Strategy':45s} {'Market':30s} {'Trades':>6} {'WR':>7} {'PnL':>14} {'Return':>8} {'MaxDD':>8} {'Sharpe':>7} {'PF':>8}")
print("=" * 160)

for _, r in df.iterrows():
    wr = f"{r['win_rate']*100:.1f}%"
    pnl = f"${r['total_pnl']:>12,.2f}"
    ret = f"{r['return_pct']*100:.1f}%"
    dd = f"{r['max_drawdown']*100:.1f}%"
    sh = f"{r['sharpe']:.2f}"
    pf = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 1000 else "huge"
    print(f"{str(r['strategy']):45s} {str(r['market']):30s} {int(r['trades']):>6} {wr:>7} {pnl:>14} {ret:>8} {dd:>8} {sh:>7} {pf:>8}")

print("=" * 160)
