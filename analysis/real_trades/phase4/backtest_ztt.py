"""Phase 4 (v3) — HONEST backtest of the ZTT screener (plan A1 = V7).

Thin reporting layer over the ONE shared honest fill engine
(analysis/real_trades/ztt_sim.simulate) — next-bar-open fills, gap-aware exits,
phantom-fill assert, outlier/"unable" model, session-gated cost. Headline metrics
from analysis/real_trades/metrics.summarize (information ratio + Calmar/Sortino/
Ulcer + R-distribution + cap-MFE audit + beat-Gold-buy-&-hold), NOT Profit Factor.

Honest fills LOWER reported performance vs old signal-close fills — that is the
point (the SBRS phantom-fill artifact), not a regression.

Usage:  py -m analysis.real_trades.phase4.backtest_ztt [1y|10y]
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt import generate_setups, ZTTParams              # noqa: E402
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from src.regimes.ztt_regime import compute_regime                   # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ  # noqa: E402
from analysis.real_trades.metrics import summarize                  # noqa: E402

PERIOD = sys.argv[1] if len(sys.argv) > 1 else '1y'
df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv', index_col=0, parse_dates=True)
if df.index.tz is None:
    df.index = df.index.tz_localize('UTC')


def report(name, trades, unables):
    if not trades:
        print(f"{name:26s}  no trades  (unables={unables})"); return
    m = summarize(trades, START_EQ, benchmark_close=df['Close'])
    rd = m['r_dist']
    gate = 'PASS' if (m.get('beats_buy_hold') and m['information_ratio'] > 0.5
                      and rd.get('worst_decile', -1) > 0) else 'KILL/screener-only'
    print(f"\n-- {name}  (n={m['n']}, unables={unables}) --")
    print(f"   info_ratio {m['information_ratio']:.2f}  (live~{m['live_expectation_ir']:.2f}) "
          f"| buy&hold {m.get('buy_hold_info_ratio', float('nan')):.2f} "
          f"| beats_B&H {m.get('beats_buy_hold')}")
    print(f"   Sortino {m['sortino']:.2f} | Calmar {m['calmar']:.2f} | Ulcer {m['ulcer']:.2f} "
          f"| maxDD {m['max_dd_pct']:.1f}%")
    print(f"   net_pnl ${m['net_pnl']:.0f} | comp_ret {m['compounded_return_pct']:.1f}% "
          f"| worst_seq ${m['worst_sequence_pnl']:.0f} | WR {m['wr']:.1f}%")
    print(f"   net_R {m['net_r']:.1f} | mean_R {m['mean_r']:.3f} "
          f"| R p10 {rd.get('p10', float('nan')):.2f} / p50 {rd.get('p50', float('nan')):.2f} "
          f"/ p90 {rd.get('p90', float('nan')):.2f} / worst-decile {rd.get('worst_decile', float('nan')):.2f}")
    print(f"   kurtosis {m['excess_kurtosis']:.1f} (leak_flag={m['kurtosis_leak_flag']}) "
          f"| PF(diagnostic) {m['profit_factor']:.2f}")
    cm = m['cap_mfe']
    print(f"   cap-MFE: {cm['n_capped']} capped, median left-on-table "
          f"{cm['median_left_on_table_r']}R  by_regime={cm['by_regime']}")
    print(f"   VERDICT: {gate}")


def run():
    print(f"=== Phase 4 v3 HONEST backtest — {PERIOD} M10 Gold — next-bar fills, "
          f"phantom-fill assert, outlier-unable, info-ratio headline ===")
    p1 = ZTTParams()
    reg1 = compute_regime(df, p1)
    raw = generate_setups(df, p1, apply_gates=False)
    t, u = simulate(raw, df, atr_array(df, p1), reg1)
    report('raw geometry (v1, no gates)', t, u)

    p2 = ZTTV2Params()
    reg2 = compute_regime(df, p2)
    v2 = generate_setups_v2(df, p2, apply_gates=True)
    t, u = simulate(v2, df, atr_array(df, p2), reg2)
    report('v2 screener (shipped config)', t, u)


if __name__ == '__main__':
    run()
