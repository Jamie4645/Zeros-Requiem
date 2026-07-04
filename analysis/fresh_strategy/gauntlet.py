"""Fresh-strategy honest validation gauntlet — pre-registered N1-N8
(knowledge-base/93-Fresh-Gold-Strategy-MPB-VTC.md, committed BEFORE this ran).

Runs each candidate (MPB, VTC) through the frozen gate sequence, halting the
candidate at its first KILL. Reuses the ONE honest engine (ztt_sim.simulate:
next-bar-open fills, gap-aware exits, phantom-fill assert = N1, session-gated
cost) and the honest scoreboard (metrics.summarize). NOTHING here may be tuned
after results are seen — the 9-cell grids and every threshold are frozen in KB-93.

Usage:  py -m analysis.fresh_strategy.gauntlet [mpb|vtc|all] [n_perm]
Output: logs/fresh_strategy/gauntlet_<name>.log + gauntlet_<name>.json
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from analysis.real_trades.ztt_sim import simulate, atr_array, START_EQ   # noqa: E402
from analysis.real_trades.metrics import summarize, profit_factor        # noqa: E402
from src.regimes.ztt import ZTTParams                                    # noqa: E402

MAX_HOLD = 72            # frozen in KB-93 (12h on 10m bars)
SEED = 20260704          # frozen
N_WF_WINDOWS = 8
MC_SIMS = 10_000
MC_BLOCK = 25            # circular moving-block length (matches portfolio MC convention)
RISK = 0.01

# ── pre-registered grids (KB-93; NO other configs may be run) ──
GRIDS = {
    'mpb': [dict(ER_MIN=e, RR_TARGET=r) for e in (0.25, 0.30, 0.35) for r in (1.7, 1.8, 2.0)],
    'vtc': [dict(THRUST_ATR=t, CLV_BAND=c) for t in (1.25, 1.5, 2.0) for c in (0.75, 0.80, 0.85)],
}
CENTER = {'mpb': dict(ER_MIN=0.30, RR_TARGET=1.8), 'vtc': dict(THRUST_ATR=1.5, CLV_BAND=0.80)}


class Log:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, 'w', encoding='utf-8')

    def __call__(self, msg: str = ''):
        print(msg)
        self.f.write(msg + '\n')
        self.f.flush()


def _load_df() -> pd.DataFrame:
    df = pd.read_csv(ROOT / 'data/cache/oanda_gold_10y_10m.csv', index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    return df


def _strategy(name: str):
    if name == 'mpb':
        from src.regimes.mpb import MPBParams, generate_setups
        return MPBParams, generate_setups
    if name == 'vtc':
        from src.regimes.vtc import VTCParams, generate_setups
        return VTCParams, generate_setups
    raise ValueError(name)


def _run_cell(gen, Params, cell: dict, df, atr_v):
    p = Params(**cell)
    setups = gen(df, p)
    # min_risk_frac + block_rollover added post-verdict per 2026-07-04 ultrareview
    # defects #1/#4 (gap-collapse guard, rollover hard-gate). The original
    # pre-registered artifacts (no suffix) are preserved; corrected runs use
    # the '_corrected' suffix and did not change any verdict.
    trades, unables = simulate(setups, df, atr_v, one_position=True,
                               max_hold=MAX_HOLD, target_rr=getattr(p, 'RR_TARGET', 1.8),
                               block_rollover=True, min_risk_frac=0.5)
    return setups, trades, unables


def _wf_windows(trades, df) -> list:
    """8 sequential calendar windows over the single continuous one_position run.

    Equity/peak carry is inherent: the run is continuous (post-R6-5 discipline);
    windows only PARTITION the realized trades by entry_time.
    """
    t0, t1 = df.index[0], df.index[-1]
    edges = pd.date_range(t0, t1, periods=N_WF_WINDOWS + 1)
    out = []
    for k in range(N_WF_WINDOWS):
        wt = [t for t in trades if edges[k] <= t['entry_time'] < edges[k + 1]]
        out.append(dict(window=k + 1, n=len(wt), pnl=float(sum(t['pnl'] for t in wt)),
                        net_r=float(sum(t['r'] for t in wt))))
    return out


def _mc_block_bootstrap(r: np.ndarray, rng) -> float:
    """Circular moving-block bootstrap of the R sequence at 1% fixed risk.
    Returns Prob(max drawdown >= 20%)."""
    n = len(r)
    if n == 0:
        return 1.0
    hits = 0
    n_blocks = int(np.ceil(n / MC_BLOCK))
    for _ in range(MC_SIMS):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + np.arange(MC_BLOCK)[None, :]).ravel()[:n] % n
        eq = START_EQ * np.cumprod(1.0 + RISK * r[idx])
        peak = np.maximum.accumulate(np.concatenate([[START_EQ], eq]))
        dd = 1.0 - np.concatenate([[START_EQ], eq]) / peak
        if dd.max() >= 0.20:
            hits += 1
    return hits / MC_SIMS


def _perm_null_shift(setups, trades, df, atr_v, n_perm: int, rng, log) -> dict:
    """Adjacency-preserving circular-shift null (phase4/permutation_null.py 'shift'
    convention): same schedule spacing, same direction/SL%%/RR structure, random
    placement in time. Actual net-R must beat the 95th percentile."""
    n = len(df)
    CLOSE = df['Close'].values
    actual_net_r = sum(t['r'] for t in trades)
    tmpl = [(s.entry_index, s.direction,
             abs(s.entry_price - s.stop_loss) / s.entry_price, s.rr) for s in setups]
    nulls = []
    for b in range(n_perm):
        off = int(rng.integers(1, n - 1))
        shifted = []
        for (ei, direction, sl_frac, rr) in tmpl:
            bar = (ei + off) % (n - 2)
            entry = CLOSE[bar]
            sign = 1.0 if direction == 'long' else -1.0
            sl_dist = sl_frac * entry
            s = _NullSetup(entry_index=bar, entry_time=df.index[bar], direction=direction,
                           entry_price=entry, stop_loss=entry - sign * sl_dist,
                           take_profit=entry + sign * rr * sl_dist, rr=rr)
            shifted.append(s)
        nt, _ = simulate(shifted, df, atr_v, one_position=True, max_hold=MAX_HOLD)
        nulls.append(sum(t['r'] for t in nt))
        if (b + 1) % 100 == 0:
            log(f"    perm {b + 1}/{n_perm}  null mean so far {np.mean(nulls):+.1f}R")
    nulls = np.array(nulls)
    p95 = float(np.percentile(nulls, 95))
    p_emp = float((nulls >= actual_net_r).mean())
    return dict(actual_net_r=float(actual_net_r), null_mean=float(nulls.mean()),
                null_p95=p95, empirical_p=p_emp, beats=bool(actual_net_r > p95))


@dataclasses.dataclass
class _NullSetup:
    entry_index: int
    entry_time: pd.Timestamp
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    rr: float
    mode: str = 'null'
    level_price: float = 0.0
    level_touches: int = 0
    break_index: int = 0


def run(name: str, n_perm: int, suffix: str = ''):
    log = Log(ROOT / f'logs/fresh_strategy/gauntlet_{name}{suffix}.log')
    res = {'strategy': name, 'gates': {}, 'verdict': None}
    rng = np.random.default_rng(SEED)
    log(f"==== GAUNTLET {name.upper()} — pre-registered KB-93 N1-N8 ====")

    df = _load_df()
    atr_v = atr_array(df, ZTTParams())
    Params, gen = _strategy(name)

    def kill(gate, why):
        res['gates'][gate]['verdict'] = 'KILL'
        res['verdict'] = f'KILL at {gate}: {why}'
        log(f"\n*** {gate} KILL — {why} ***")

    # N1 is structural: any phantom-fill assert inside simulate() raises and halts.

    # ── N2 + N3: grid backtest at realistic cost ──
    log(f"\n-- N2/N3: 9-cell frozen grid --")
    cells = []
    center_trades = center_setups = None
    for cell in GRIDS[name]:
        setups, trades, unables = _run_cell(gen, Params, cell, df, atr_v)
        pnl = np.array([t['pnl'] for t in trades])
        pf = profit_factor(pnl) if len(trades) else 0.0
        cells.append(dict(cell=cell, n_setups=len(setups), n_trades=len(trades),
                          unables=unables, pf=float(pf), net_pnl=float(pnl.sum()) if len(trades) else 0.0))
        log(f"  {cell}  setups={len(setups)} trades={len(trades)} unables={unables} "
            f"PF={pf:.3f} pnl=${pnl.sum() if len(trades) else 0:.0f}")
        if cell == CENTER[name]:
            center_trades, center_setups = trades, setups
    n_center = next(c['n_trades'] for c in cells if c['cell'] == CENTER[name])
    res['gates']['N2'] = dict(center_trades=n_center,
                              verdict='PASS' if 150 <= n_center <= 6000 else 'KILL')
    log(f"\nN2 sample sanity: center-cell trades={n_center} -> {res['gates']['N2']['verdict']}")
    if res['gates']['N2']['verdict'] == 'KILL':
        kill('N2', f'trade count {n_center} outside [150, 6000]')
        return _finish(res, cells, log, name, suffix)

    pfs = np.array([c['pf'] for c in cells])
    grid_avg_pf = float(pfs.mean())
    plateau = float((pfs > 1.0).mean())
    res['gates']['N3'] = dict(grid_avg_pf=grid_avg_pf, plateau_frac=plateau,
                              verdict='PASS' if (grid_avg_pf >= 1.10 and plateau >= 0.70) else 'KILL')
    log(f"N3 realistic-cost: grid-avg PF={grid_avg_pf:.3f} (kill<1.10), "
        f"plateau {plateau * 100:.0f}% cells PF>1.0 (kill<70%) -> {res['gates']['N3']['verdict']}")

    # honest scoreboard on the center cell (reported regardless of verdict)
    m = summarize(center_trades, START_EQ, benchmark_close=df['Close'])
    res['center_scoreboard'] = {k: v for k, v in m.items() if not isinstance(v, dict)}
    log(f"\ncenter cell scoreboard: IR={m['information_ratio']:.2f} Sortino={m['sortino']:.2f} "
        f"Calmar={m['calmar']:.2f} maxDD={m['max_dd_pct']:.1f}% WR={m['wr']:.1f}% "
        f"netR={m['net_r']:.1f} PF={m['profit_factor']:.3f} "
        f"B&H_IR={m.get('buy_hold_info_ratio', float('nan')):.2f} beats={m.get('beats_buy_hold')}")

    if res['gates']['N3']['verdict'] == 'KILL':
        kill('N3', f'grid-avg PF {grid_avg_pf:.3f} / plateau {plateau * 100:.0f}%')
        return _finish(res, cells, log, name, suffix)

    # ── N4 walk-forward partition ──
    wf = _wf_windows(center_trades, df)
    n_prof = sum(1 for w in wf if w['pnl'] > 0)
    for w in wf:
        log(f"  W{w['window']}: n={w['n']} pnl=${w['pnl']:.0f} netR={w['net_r']:+.1f}")
    res['gates']['N4'] = dict(windows=wf, profitable=n_prof,
                              verdict='PASS' if n_prof >= 6 else ('KILL' if n_prof < 5 else 'MARGINAL'))
    log(f"N4 walk-forward: {n_prof}/8 profitable (pass>=6, kill<5) -> {res['gates']['N4']['verdict']}")
    if res['gates']['N4']['verdict'] == 'KILL':
        kill('N4', f'{n_prof}/8 windows profitable')
        return _finish(res, cells, log, name, suffix)

    # ── N7 red-flag inversion (KB-93 order: after WF so the Sharpe leg exists) ──
    flags = []
    if m['wr'] > 70: flags.append(f"WR {m['wr']:.1f}%>70%")
    if m['profit_factor'] > 3.0: flags.append(f"PF {m['profit_factor']:.2f}>3.0")
    if m['information_ratio'] > 3.0: flags.append(f"WF Sharpe/IR {m['information_ratio']:.2f}>3.0")
    res['gates']['N7'] = dict(flags=flags, verdict='HALT-INVESTIGATE' if flags else 'PASS')
    log(f"N7 red-flags: {flags or 'none'} -> {res['gates']['N7']['verdict']}")
    if flags:
        kill('N7', '; '.join(flags))
        return _finish(res, cells, log, name, suffix)

    # ── N5 block-bootstrap MC ──
    r = np.array([t['r'] for t in center_trades])
    prob_dd = _mc_block_bootstrap(r, rng)
    res['gates']['N5'] = dict(prob_20dd=prob_dd, sims=MC_SIMS, block=MC_BLOCK,
                              verdict='PASS' if prob_dd < 0.05 else 'KILL')
    log(f"N5 MC (block bootstrap, {MC_SIMS} sims, block={MC_BLOCK}): "
        f"Prob(20%DD)={prob_dd * 100:.2f}% (kill>=5%) -> {res['gates']['N5']['verdict']}")
    if res['gates']['N5']['verdict'] == 'KILL':
        kill('N5', f'Prob(20%DD) {prob_dd * 100:.2f}%')
        return _finish(res, cells, log, name, suffix)

    # ── N6 permutation null (adjacency-preserving circular shift) ──
    log(f"\n-- N6: permutation null ({n_perm} shifts) --")
    pn = _perm_null_shift(center_setups, center_trades, df, atr_v, n_perm, rng, log)
    res['gates']['N6'] = dict(**pn, verdict='PASS' if pn['beats'] else 'KILL')
    log(f"N6: actual {pn['actual_net_r']:+.1f}R vs null p95 {pn['null_p95']:+.1f}R "
        f"(mean {pn['null_mean']:+.1f}R, p={pn['empirical_p']:.4f}) -> {res['gates']['N6']['verdict']}")
    if not pn['beats']:
        kill('N6', f"net R {pn['actual_net_r']:.1f} <= null p95 {pn['null_p95']:.1f}")
        return _finish(res, cells, log, name, suffix)

    # ── N8 buy-and-hold gate (long-bias beta check) ──
    long_pnl = sum(t['pnl'] for t in center_trades if t['direction'] == 'long')
    tot_pnl = sum(t['pnl'] for t in center_trades)
    long_share = long_pnl / tot_pnl if tot_pnl else 0.0
    applies = long_share > 0.70
    beats = bool(m.get('beats_buy_hold'))
    res['gates']['N8'] = dict(long_share=float(long_share), applies=applies, beats_bh=beats,
                              verdict='PASS' if (not applies or beats) else 'KILL')
    log(f"N8 B&H gate: long-share {long_share * 100:.0f}% (applies>{70}%), "
        f"beats B&H IR: {beats} -> {res['gates']['N8']['verdict']}")
    if res['gates']['N8']['verdict'] == 'KILL':
        kill('N8', f'long-share {long_share * 100:.0f}% and IR does not beat buy-and-hold')
        return _finish(res, cells, log, name, suffix)

    res['verdict'] = 'SURVIVES N1-N8 (candidate for council review — NOT live; 0.00% size)'
    log(f"\n==== {name.upper()} verdict: {res['verdict']} ====")
    return _finish(res, cells, log, name, suffix)


def _finish(res, cells, log, name, suffix=''):
    res['grid'] = cells
    out = ROOT / f'logs/fresh_strategy/gauntlet_{name}{suffix}.json'
    out.write_text(json.dumps(res, indent=1, default=str), encoding='utf-8')
    log(f"\nJSON -> {out}")
    return res


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    n_perm = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    sfx = sys.argv[3] if len(sys.argv) > 3 else ''
    for nm in (['mpb', 'vtc'] if which == 'all' else [which]):
        run(nm, n_perm, sfx)
