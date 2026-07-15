"""Round 8 Portfolio MC at evidence-weighted 1.10% allocation.
Scales per-strategy PnL by (new_risk / old_risk). USDJPY removed from portfolio.
Run: py -m tests._r8_portfolio_studentt_mc_110
"""
import sys, os
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import scipy.stats as stats

np.random.seed(42)
N_SIMS = 10000
CAPITAL = 10000.0

# R7 baseline risk (source of avg_win/avg_loss in strategies dict)
R7_RISK = {'Gold': 0.005, 'DAX': 0.0025, 'NDX': 0.0025, 'GBPUSD': 0.0025, 'USDJPY': 0.0025}

# Round 8 evidence-weighted allocation
R8_RISK = {'Gold': 0.005, 'DAX': 0.0025, 'NDX': 0.0015, 'GBPUSD': 0.0020, 'USDJPY': 0.0}

# Per-strategy BT stats (from Round 7 WF logs)
STRATEGIES_R7 = {
    'Gold':   {'wr': 0.461, 'avg_win': 162.80, 'avg_loss': 52.46, 'trades_yr': 73},
    'DAX':    {'wr': 0.488, 'avg_win': 46.47,  'avg_loss': 26.21, 'trades_yr': 46},
    'NDX':    {'wr': 0.450, 'avg_win': 83.75,  'avg_loss': 26.09, 'trades_yr': 53},
    'GBPUSD': {'wr': 0.462, 'avg_win': 78.35,  'avg_loss': 33.53, 'trades_yr': 27},
    'USDJPY': {'wr': 0.547, 'avg_win': 73.94,  'avg_loss': 27.99, 'trades_yr': 16},
}

# Scale PnL by new/old risk; drop strategies at 0.0
STRATEGIES = {}
for name, stat in STRATEGIES_R7.items():
    ratio = R8_RISK[name] / R7_RISK[name] if R7_RISK[name] > 0 else 0
    if ratio == 0:
        continue
    STRATEGIES[name] = {
        'wr': stat['wr'],
        'avg_win':  stat['avg_win'] * ratio,
        'avg_loss': stat['avg_loss'] * ratio,
        'trades_yr': stat['trades_yr'],
    }

STRAT_NAMES = list(STRATEGIES.keys())
N = len(STRAT_NAMES)

WF_PNL_R7 = {
    'Gold':   [3456.23, 2605.96, 2737.49, 2305.83, 3087.55, 3753.46, 5381.39, 3842.44],
    'DAX':    [1443.70, -189.43, 2331.18, 1004.33, 1503.20, 1671.16,  380.92, 1122.46],
    'NDX':    [1349.82, -565.23, 1851.87, 1461.49, 4438.34, 2194.46,  271.27, 2598.49],
    'GBPUSD': [ 221.57,  172.75,  543.10,  600.46,  744.28,  364.11,  146.63,  410.54],
    'USDJPY': [1864.35, 2095.66, 1607.12, -142.66,  750.63, 2841.18,  831.19, 1764.81],
}

CORR_BASE = np.corrcoef(np.array([WF_PNL_R7[n] for n in STRAT_NAMES]))


def nearest_pd(C):
    C = (C + C.T) / 2
    w, V = np.linalg.eigh(C)
    w = np.clip(w, 1e-6, None)
    Cpd = V @ np.diag(w) @ V.T
    d = np.sqrt(np.clip(np.diag(Cpd), 1e-12, None))
    Cpd = Cpd / np.outer(d, d)
    np.fill_diagonal(Cpd, 1.0)
    return Cpd


def run_mc(corr_mat, use_student_t=True, nu=4, label="Student-t nu=4"):
    try:
        L = np.linalg.cholesky(corr_mat)
    except np.linalg.LinAlgError:
        corr_mat = nearest_pd(corr_mat)
        L = np.linalg.cholesky(corr_mat)
    mds, fps = [], []
    for _ in range(N_SIMS):
        ts = []
        for i, (n, s) in enumerate(STRATEGIES.items()):
            ts.extend([(i, n)] * int(np.random.poisson(s['trades_yr'])))
        np.random.shuffle(ts)
        nt = len(ts)
        if nt == 0:
            mds.append(0.0); fps.append(0.0); continue
        if use_student_t:
            Z = np.random.multivariate_normal(np.zeros(N), corr_mat, size=nt)
            c2 = np.random.chisquare(nu, size=(nt, 1))
            U = stats.t.cdf(Z / np.sqrt(c2 / nu), df=nu)
        else:
            Z = np.random.multivariate_normal(np.zeros(N), corr_mat, size=nt)
            U = stats.norm.cdf(Z)
        eq, pk, md = CAPITAL, CAPITAL, 0.0
        for ti, (si, sn) in enumerate(ts):
            s = STRATEGIES[sn]
            sc = eq / CAPITAL
            win = U[ti, si] < s['wr']
            eq += s['avg_win'] * sc if win else -s['avg_loss'] * sc
            if eq > pk:
                pk = eq
            dd = (pk - eq) / pk
            if dd > md:
                md = dd
        mds.append(md)
        fps.append(eq - CAPITAL)
    mds = np.array(mds); fps = np.array(fps)
    return {
        'label': label,
        'p20': float(np.mean(mds >= 0.20) * 100),
        'p15': float(np.mean(mds >= 0.15) * 100),
        'p10': float(np.mean(mds >= 0.10) * 100),
        'avg': float(np.mean(mds) * 100),
        'p50': float(np.percentile(mds, 50) * 100),
        'p95': float(np.percentile(mds, 95) * 100),
        'p99': float(np.percentile(mds, 99) * 100),
        'ann_pnl_mean': float(np.mean(fps)),
        'ann_pnl_p5': float(np.percentile(fps, 5)),
        'ann_pnl_p95': float(np.percentile(fps, 95)),
        'worst1pct': float(np.percentile(fps, 1)),
    }


def fmt(r):
    s = r["label"] + "\n"
    s += "  Prob(20DD): " + str(round(r["p20"], 2)) + "%\n"
    s += "  Prob(15DD): " + str(round(r["p15"], 2)) + "%\n"
    s += "  Prob(10DD): " + str(round(r["p10"], 2)) + "%\n"
    s += "  AvgDD: " + str(round(r["avg"], 2)) + "% P95: " + str(round(r["p95"], 2)) + "% P99: " + str(round(r["p99"], 2)) + "%\n"
    s += "  Ann PnL mean: $" + str(round(r["ann_pnl_mean"])) + "  P5: $" + str(round(r["ann_pnl_p5"])) + "  P95: $" + str(round(r["ann_pnl_p95"])) + "  Worst1%: $" + str(round(r["worst1pct"]))
    return s


if __name__ == '__main__':
    print('Round 8 Portfolio MC @ 1.10% evidence-weighted sizing | seed=42 | 10k sims')
    print('Active strategies:', ', '.join([f"{n} {R8_RISK[n]*100:.2f}%" for n in STRAT_NAMES]))
    print('Total portfolio risk: ' + str(round(sum(R8_RISK[n] for n in STRAT_NAMES) * 100, 2)) + '%')
    print('Running Student-t nu=4 (base)...')
    rt = run_mc(CORR_BASE, use_student_t=True, nu=4, label='Student-t nu=4 @1.10%')
    print('Running Gaussian baseline...')
    rg = run_mc(CORR_BASE, use_student_t=False, label='Gaussian baseline @1.10%')
    # Subset corr matrix for stress (exclude USDJPY)
    cs = np.clip(CORR_BASE + 0.2 * (1 - np.eye(N)), -1, 1)
    np.fill_diagonal(cs, 1.0)
    print('Running Student-t nu=4 stress +0.2 corr...')
    rs = run_mc(cs, use_student_t=True, nu=4, label='Student-t nu=4 +0.2 stress @1.10%')
    for r in [rt, rg, rs]:
        print()
        print(fmt(r))
    p20 = rt['p20']; p20s = rs['p20']
    v = 'PASS' if p20 < 5.0 and p20s < 10.0 else 'WARN' if p20 < 10.0 else 'FAIL'
    pen = p20 - rg['p20']
    print()
    print("VERDICT: " + v + "  Base:" + str(round(p20, 2)) + "%  Stress:" + str(round(p20s, 2)) + "%  Penalty:+" + str(round(pen, 2)) + "pp")
    os.makedirs('logs/round8', exist_ok=True)
    with open('logs/round8/portfolio_studentt_mc_110.log', 'w') as f:
        f.write('PORTFOLIO STUDENT-T MC @ 1.10% | ROUND 8 | ' + str(datetime.now().date()) + '\n')
        f.write('Allocation: ' + ', '.join([f"{n} {R8_RISK[n]*100:.2f}%" for n in STRAT_NAMES]) + '\n')
        for r in [rt, rg, rs]:
            f.write('\n' + fmt(r) + '\n')
        f.write('\nVERDICT: ' + v + '  Base:' + str(round(p20, 2)) + '%  Stress:' + str(round(p20s, 2)) + '%\n')
    print('Written: logs/round8/portfolio_studentt_mc_110.log')
