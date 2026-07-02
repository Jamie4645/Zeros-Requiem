"""A4 + A5 — plateau-not-peak robustness + vertical (standalone-first) filter gate.

A4 (V6): sweep each tunable GEOMETRICALLY and require a CONTIGUOUS plateau of
profitable configs around the chosen value; report the AVERAGE and AVERAGE-1SD across
configs (not the best config). Directly stress-tests whether the "1.5% cap" is a
robust plateau or a lucky hindsight point on 30 takes.

A5 (V3): score filters by the % of profitable parameter-configs. A filter is credited
ONLY if %-profitable RISES vs the unfiltered base AND (avg up, SD flat) or (SD down,
avg flat). Surfaces Kaufman's "integrated trap": a filter that looks good only because
the base loses on its own — precisely ZTT's situation (PF~0.90), so any 'pass' must be
scrutinised as a possible artifact.

Headline metric = information ratio (A2), measured on the ONE honest engine (ztt_sim).
Caveat (stated in canon): a plateau on a near-PF-1.0 base just means it ROBUSTLY has
no edge — this guards false precision, not absence of edge. Pair with A3.

Usage:  py -m analysis.real_trades.phase4.robustness [1y|10y]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ  # noqa: E402
from analysis.real_trades.metrics import summarize                  # noqa: E402

PERIOD = sys.argv[1] if len(sys.argv) > 1 else '1y'
TP_GRID = [0.010, 0.0125, 0.015, 0.0175, 0.020, 0.025]   # geometric-ish TP %-cap sweep
SL_GRID = [0.0035, 0.0045, 0.0055]                        # SL buffer % sweep


def _ir(df, atr_v, p):
    setups = generate_setups_v2(df, p, apply_gates=True)
    trades, _ = simulate(setups, df, atr_v, one_position=True)
    if not trades:
        return None
    m = summarize(trades, START_EQ)
    return dict(ir=m['information_ratio'], net_r=m['net_r'], n=m['n'], pf=m['profit_factor'])


def _config(**kw):
    return ZTTV2Params(**kw)


def main():
    df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv',
                     index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    atr_v = atr_array(df, ZTTV2Params())

    print(f"=== A4 plateau robustness — {PERIOD} M10 Gold (info-ratio headline) ===")
    print("TP %-cap sweep (shipped config, false-bo on):")
    irs = []
    for tp in TP_GRID:
        r = _ir(df, atr_v, _config(MAX_MOVE_PCT=tp))
        if r:
            irs.append(r['ir'])
            mark = ' <-- shipped 1.5%' if abs(tp - 0.015) < 1e-9 else ''
            print(f"  TP={tp*100:5.2f}%  IR {r['ir']:+.2f}  net_R {r['net_r']:7.1f}  "
                  f"n {r['n']:4d}  PF {r['pf']:.2f}{mark}")
    irs = np.array(irs)
    pct_prof = float((irs > 0).mean() * 100)
    print(f"  -> %-profitable configs {pct_prof:.0f}%  | avg IR {irs.mean():+.2f}  "
          f"| avg-1SD {irs.mean() - irs.std():+.2f}")
    print(f"  PLATEAU verdict: {'contiguous profitable band' if pct_prof >= 70 else 'NO profitable plateau — robustly no edge'}")

    print("\nSL buffer % sweep (TP fixed 1.5%):")
    for sb in SL_GRID:
        r = _ir(df, atr_v, _config(SL_BUFFER_PCT=sb))
        if r:
            print(f"  SL_buf={sb*100:4.2f}%  IR {r['ir']:+.2f}  net_R {r['net_r']:7.1f}  n {r['n']:4d}")

    print(f"\n=== A5 vertical (standalone-first) filter gate — {PERIOD} ===")
    print("%-profitable-configs over the TP grid, by filter stack:")
    stacks = {
        'base geometry        ': dict(enforce_false_bo=False, enforce_session=False),
        '+ false-bo           ': dict(enforce_false_bo=True, enforce_session=False),
        '+ false-bo + session ': dict(enforce_false_bo=True, enforce_session=True),
    }
    base_pct = None
    for name, kw in stacks.items():
        irs = []
        for tp in TP_GRID:
            r = _ir(df, atr_v, _config(MAX_MOVE_PCT=tp, **kw))
            if r:
                irs.append(r['ir'])
        irs = np.array(irs)
        pct = float((irs > 0).mean() * 100)
        if base_pct is None:
            base_pct = pct
        delta = pct - base_pct
        verdict = 'credit' if (pct > base_pct and irs.mean() >= 0) else 'no lift (integrated-trap risk / losing base)'
        print(f"  {name} %-prof {pct:5.0f}%  (Δ{delta:+.0f})  avg IR {irs.mean():+.2f}  SD {irs.std():.2f}  -> {verdict}")
    print("\nNOTE: base geometry loses (canon PF~0.90); a filter 'passing' on a losing base is "
          "presumed an integrated-trap artifact -> reinforces screener-with-human, not autonomy.")


if __name__ == '__main__':
    main()
