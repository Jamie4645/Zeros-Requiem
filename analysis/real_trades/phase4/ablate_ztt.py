"""ZTT v2/v3 ABLATION — every method, active + legacy, one toggle at a time.

Measures each method's contribution to the SHIPPED screener on the HONEST engine
(ztt_sim) + the info-ratio metric stack (metrics.summarize). 1Y Gold M10 by default.

Layout:
  BASELINE   = shipped ZTTV2Params() (apply_gates=True).
  RAW floor  = all selection gates + false-bo off (pure geometry + v2 entry/exit).
  [ACTIVE]   = a method that is ON in the shipped config -> we turn it OFF; the Δ is
               what it currently contributes (negative Δ = it's helping, positive = hurting).
  [PAST]     = a method built earlier but OFF in the shipped config -> we turn it ON; the
               Δ is what re-enabling it would do.

Δ columns are vs BASELINE (net_R and info_ratio). Headline metric is information ratio
(PF kept as a secondary diagnostic). Honest fills, so absolute numbers are net-negative —
the ABLATION reads the RELATIVE contribution of each method, not an edge claim.

Usage:  py -m analysis.real_trades.phase4.ablate_ztt [1y|10y]
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from src.regimes.ztt_v2 import generate_setups_v2, ZTTV2Params      # noqa: E402
from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ  # noqa: E402
from analysis.real_trades.metrics import summarize                  # noqa: E402

PERIOD = sys.argv[1] if len(sys.argv) > 1 else '1y'

# (label, tag, kwargs-vs-baseline, apply_gates)
#   tag: base | floor | ACTIVE (remove) | PAST (add)
CONFIGS = [
    ('BASELINE (shipped full)',             'base',   {}, True),
    ('RAW geometry (all gates off)',        'floor',  dict(enforce_false_bo=False,
                                                           allow_reversal=True), False),
    # ── ACTIVE methods in the shipped screener -> turn OFF (Δ = current contribution) ──
    ('-- false-breakout filter (S3)',       'ACTIVE', dict(enforce_false_bo=False), True),
    ('-- G3 level-respect veto',            'ACTIVE', dict(enable_respect=False), True),
    ('-- G4 structure/efficiency',          'ACTIVE', dict(enable_structure=False), True),
    ('-- G5 HTF (1h/3h EMA) align',         'ACTIVE', dict(enable_htf=False), True),
    ('-- G6 volume >= avg',                 'ACTIVE', dict(enable_volume=False), True),
    ('-- %-cap TP (-> pure 3R)',            'ACTIVE', dict(MAX_MOVE_PCT=10.0), True),
    ('-- level-anchored SL (-> swing SL)',  'ACTIVE', dict(sl_anchor='swing'), True),
    ('-- reversal mode (continuation only)', 'ACTIVE', dict(allow_reversal=False), True),
    # ── level quality (MIN_TOUCHES) sensitivity ──
    ('~~ MIN_TOUCHES 2 -> 3 (stricter)',    'ACTIVE', dict(MIN_TOUCHES=3), True),
    ('~~ MIN_TOUCHES 2 -> 1 (looser)',      'ACTIVE', dict(MIN_TOUCHES=1), True),
    # ── PAST / legacy methods OFF in shipped -> turn ON (Δ = effect of re-enabling) ──
    ('++ significance gate (S1)',           'PAST',   dict(enforce_significance=True), True),
    ('++ momentum requirement (S2)',        'PAST',   dict(req_momentum=True), True),
    ('++ session gate (S4)',                'PAST',   dict(enforce_session=True), True),
    ('++ opposing-level TP cap (S1b)',      'PAST',   dict(enforce_opposing=True), True),
    ('++ FVG shift signal',                 'PAST',   dict(req_fvg=True), True),
    ('++ liquidity-sweep shift signal',     'PAST',   dict(req_sweep=True), True),
    ('++ momentum-continuation mode',       'PAST',   dict(momentum_mode='on'), True),
    ('++ REVERSAL_LOOKBACK 240 -> 30 (v1)', 'PAST',   dict(REVERSAL_LOOKBACK=30), True),
]


def main():
    df = pd.read_csv(ROOT / f'data/cache/oanda_gold_{PERIOD}_10m.csv',
                     index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    atr_v = atr_array(df, ZTTV2Params())

    def metrics_for(kwargs, apply_gates):
        p = ZTTV2Params(**kwargs)
        setups = generate_setups_v2(df, p, apply_gates=apply_gates)
        trades, _ = simulate(setups, df, atr_v, one_position=True)
        if not trades:
            return None
        m = summarize(trades, START_EQ)
        return m

    base = metrics_for({}, True)
    bnr, bir = base['net_r'], base['information_ratio']

    print(f"=== ZTT v2 ABLATION — {PERIOD} M10 Gold — honest engine, info-ratio headline ===")
    print(f"(Δ vs BASELINE; [ACTIVE]=method ON in shipped, removed here -> negative Δ means it helps)")
    print(f"\n{'method':38s} {'tag':6s} {'n':>4s} {'WR%':>5s} {'net_R':>7s} {'ΔnetR':>7s} "
          f"{'IR':>6s} {'ΔIR':>6s} {'PF':>5s} {'DD%':>5s}")
    print('-' * 104)
    for label, tag, kwargs, ag in CONFIGS:
        m = metrics_for(kwargs, ag)
        if m is None:
            print(f"{label:38s} {tag:6s}  no trades"); continue
        dnr = m['net_r'] - bnr
        dir_ = m['information_ratio'] - bir
        dmark = '' if tag in ('base', 'floor') else f"{dnr:+7.1f}"
        imark = '' if tag in ('base', 'floor') else f"{dir_:+6.2f}"
        print(f"{label:38s} {tag:6s} {m['n']:4d} {m['wr']:5.1f} {m['net_r']:7.1f} "
              f"{dmark:>7s} {m['information_ratio']:6.2f} {imark:>6s} "
              f"{m['profit_factor']:5.2f} {m['max_dd_pct']:5.1f}")

    print("\nReading guide:")
    print("  [ACTIVE] rows: a LARGE NEGATIVE ΔnetR means removing it hurt -> the method is pulling weight.")
    print("           a POSITIVE ΔnetR means the active method is HURTING (candidate to drop).")
    print("  [PAST]   rows: POSITIVE ΔnetR means re-enabling would help; NEGATIVE means it hurts (stays off).")
    print("  All absolute net_R are negative (honest fills, no blind edge) — read the RELATIVE deltas.")


if __name__ == '__main__':
    main()
