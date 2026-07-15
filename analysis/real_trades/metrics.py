"""ZTT v3 — honest metric stack (book-informed, plan Workstream A2 = V9 + EX-5).

Replaces closed-trade Profit Factor as the *headline* with leakage-resistant,
drawdown-aware, distribution-aware measures. PF is the metric that masked the SBRS
phantom-fill artifact; these are the ones the council unanimously elevated.

References (decoded from the two bibles):
  * Kaufman ch.21/23: information ratio, Calmar, Sortino, Ulcer as the deployment
    scorecard; report the full R-multiple percentile distribution, not summed/mean R.
  * Kaufman ch.23: a long-biased system must beat buy-&-hold on the SAME window.
  * Chan ch.1: expect live realization ~= half of backtest; report worst-sequence
    (asymmetric-return math: a 50% gain after a 50% loss is still -25%).
  * Kaufman: per-trade excess kurtosis > ~7 is an overfit / leakage flag.

Everything here is PURE measurement — no strategy logic, no look-ahead. Functions
take already-realized trades / an equity curve and return numbers.

A `Trade` is a light dict with at least:
    r          : realized R-multiple (pnl / initial_risk_$), signed
    pnl        : realized $ pnl
    exit_reason: 'tp' | 'sl' | 'cap' | 'timeout'
    entry_time, exit_time : tz-aware pd.Timestamp
    mfe_r      : max favourable excursion in R within the hold (post-fill), optional
    regime     : optional regime tag string (for per-regime cap-MFE / B&H splits)
"""
from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np
import pandas as pd

TRADING_DAYS = 252


# ════════════════════════════════════════════════════════════════════════
# Equity-curve → daily returns
# ════════════════════════════════════════════════════════════════════════
def daily_returns(times: Sequence[pd.Timestamp], equity: Sequence[float]) -> np.ndarray:
    """Resample a per-trade equity path to a daily equity series and return daily
    simple returns. `times` are exit timestamps, `equity` is post-trade equity
    (same length). A starting point is implied by the first equity value.
    """
    if len(equity) < 2:
        return np.array([])
    s = pd.Series(np.asarray(equity, dtype=float),
                  index=pd.DatetimeIndex(pd.to_datetime(list(times))))
    s = s[~s.index.duplicated(keep='last')].sort_index()
    daily = s.resample('1D').last().ffill().dropna()
    if len(daily) < 2:
        return np.array([])
    return daily.pct_change().dropna().values


def information_ratio(daily_ret: np.ndarray, ppy: int = TRADING_DAYS) -> float:
    """Annualized mean / annualized SD of daily equity changes (Sharpe with rf=0)."""
    daily_ret = np.asarray(daily_ret, dtype=float)
    if daily_ret.size < 2 or daily_ret.std() < 1e-12:
        return 0.0
    return float(daily_ret.mean() / daily_ret.std() * np.sqrt(ppy))


def sortino(daily_ret: np.ndarray, ppy: int = TRADING_DAYS) -> float:
    """Annualized mean / annualized downside deviation."""
    daily_ret = np.asarray(daily_ret, dtype=float)
    if daily_ret.size < 2:
        return 0.0
    downside = daily_ret[daily_ret < 0]
    dd = downside.std() if downside.size else 0.0
    if dd == 0:
        return 0.0
    return float(daily_ret.mean() / dd * np.sqrt(ppy))


def max_drawdown(equity: Sequence[float]) -> float:
    """Max peak-to-trough drawdown as a positive fraction (0.15 = 15%)."""
    eq = np.asarray(equity, dtype=float)
    if eq.size < 2:
        return 0.0
    peak = np.maximum.accumulate(eq)
    return float(np.max((peak - eq) / peak))


def calmar(times: Sequence[pd.Timestamp], equity: Sequence[float]) -> float:
    """CAGR / max drawdown. Uses the elapsed wall-clock span for annualization."""
    eq = np.asarray(equity, dtype=float)
    if eq.size < 2 or eq[0] <= 0:
        return 0.0
    t = pd.DatetimeIndex(pd.to_datetime(list(times)))
    years = max((t[-1] - t[0]).days / 365.25, 1e-6)
    cagr = (eq[-1] / eq[0]) ** (1 / years) - 1
    mdd = max_drawdown(eq)
    return float(cagr / mdd) if mdd > 0 else 0.0


def ulcer_index(equity: Sequence[float]) -> float:
    """Ulcer index: RMS of percentage drawdowns (depth AND duration of pain)."""
    eq = np.asarray(equity, dtype=float)
    if eq.size < 2:
        return 0.0
    peak = np.maximum.accumulate(eq)
    dd_pct = (eq - peak) / peak * 100.0
    return float(np.sqrt(np.mean(dd_pct ** 2)))


# ════════════════════════════════════════════════════════════════════════
# R-multiple distribution (report percentiles, not summed/mean R)
# ════════════════════════════════════════════════════════════════════════
def r_percentiles(r: Sequence[float]) -> dict:
    r = np.asarray(r, dtype=float)
    if r.size == 0:
        return {}
    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    out = {f'p{p}': float(np.percentile(r, p)) for p in pcts}
    out['mean'] = float(r.mean())
    out['worst_decile'] = float(np.mean(np.sort(r)[: max(1, r.size // 10)]))
    return out


def excess_kurtosis(r: Sequence[float]) -> float:
    """Fisher excess kurtosis. > ~7 is the council's leak/overfit flag."""
    r = np.asarray(r, dtype=float)
    if r.size < 4 or r.std() == 0:
        return 0.0
    z = (r - r.mean()) / r.std()
    return float(np.mean(z ** 4) - 3.0)


def worst_sequence(pnl: Sequence[float]) -> float:
    """Worst contiguous run of cumulative pnl (the deepest losing streak in $)."""
    pnl = np.asarray(pnl, dtype=float)
    if pnl.size == 0:
        return 0.0
    cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(cum)
    return float(np.min(cum - peak))


# ════════════════════════════════════════════════════════════════════════
# Cap-MFE audit (EX-5): does the %-cap amputate the fat right tail?
# ════════════════════════════════════════════════════════════════════════
def cap_mfe_audit(trades: List[dict]) -> dict:
    """For every trade that exited at the %-cap, R 'left on the table' = mfe_r - r.

    Returns median left-on-table overall and per regime. The plan's decision rule:
    median > ~0.5R concentrated in trending months => the cap clips the tail
    (escalate to a trailing-runner test); otherwise certify the fixed cap.
    """
    capped = [t for t in trades if t.get('exit_reason') == 'cap' and t.get('mfe_r') is not None]
    if not capped:
        return {'n_capped': 0, 'median_left_on_table_r': None, 'by_regime': {}}
    left = np.array([t['mfe_r'] - t['r'] for t in capped], dtype=float)
    by_regime: dict = {}
    if any('regime' in t for t in capped):
        df = pd.DataFrame([{'reg': t.get('regime', 'NA'),
                            'left': t['mfe_r'] - t['r']} for t in capped])
        by_regime = {k: float(np.median(v)) for k, v in df.groupby('reg')['left']}
    return {
        'n_capped': len(capped),
        'median_left_on_table_r': float(np.median(left)),
        'p90_left_on_table_r': float(np.percentile(left, 90)),
        'by_regime': by_regime,
    }


# ════════════════════════════════════════════════════════════════════════
# Buy-&-hold benchmark (the long-biased-Gold gate)
# ════════════════════════════════════════════════════════════════════════
def buy_and_hold_info_ratio(close: pd.Series, ppy: int = TRADING_DAYS) -> float:
    """Information ratio of simply holding the instrument over the same window.
    A long-biased strategy that cannot beat this is just long-Gold beta.
    """
    px = pd.Series(np.asarray(close, dtype=float),
                   index=pd.DatetimeIndex(close.index))
    daily = px.resample('1D').last().ffill().dropna()
    if len(daily) < 2:
        return 0.0
    return information_ratio(daily.pct_change().dropna().values, ppy=ppy)


# ════════════════════════════════════════════════════════════════════════
# Profit factor (kept as a SECONDARY diagnostic only)
# ════════════════════════════════════════════════════════════════════════
def profit_factor(pnl: Sequence[float]) -> float:
    pnl = np.asarray(pnl, dtype=float)
    gw = pnl[pnl > 0].sum()
    gl = -pnl[pnl < 0].sum()
    if gl == 0:
        return float('inf') if gw > 0 else 0.0
    return float(gw / gl)


# ════════════════════════════════════════════════════════════════════════
# Orchestrator
# ════════════════════════════════════════════════════════════════════════
def summarize(trades: List[dict], start_equity: float,
              benchmark_close: Optional[pd.Series] = None) -> dict:
    """Full honest scorecard from a list of realized trades (chronological).

    Each trade needs: pnl, r, exit_reason, exit_time (+ mfe_r/regime for the audit).
    """
    if not trades:
        return {'n': 0}
    trades = sorted(trades, key=lambda t: t['exit_time'])
    pnl = np.array([t['pnl'] for t in trades], dtype=float)
    r = np.array([t['r'] for t in trades], dtype=float)
    eq = start_equity + np.cumsum(pnl)
    eq_full = np.concatenate([[start_equity], eq])
    times = [trades[0]['entry_time']] + [t['exit_time'] for t in trades]
    dr = daily_returns(times, eq_full)

    ir = information_ratio(dr)
    out = {
        'n': len(trades),
        'wr': float(100 * (pnl >= 0).mean()),
        'information_ratio': ir,
        'sortino': sortino(dr),
        'calmar': calmar(times, eq_full),
        'ulcer': ulcer_index(eq_full),
        'max_dd_pct': max_drawdown(eq_full) * 100,
        'net_pnl': float(pnl.sum()),
        'final_equity': float(eq_full[-1]),
        'compounded_return_pct': float((eq_full[-1] / start_equity - 1) * 100),
        'worst_sequence_pnl': worst_sequence(pnl),
        'net_r': float(r.sum()),
        'mean_r': float(r.mean()),
        'excess_kurtosis': excess_kurtosis(r),
        'kurtosis_leak_flag': bool(excess_kurtosis(r) > 7),
        'r_dist': r_percentiles(r),
        'cap_mfe': cap_mfe_audit(trades),
        'profit_factor': profit_factor(pnl),   # secondary diagnostic only
        'live_expectation_ir': ir / 2.0,        # Chan: live ~= half of backtest
    }
    if benchmark_close is not None:
        bh = buy_and_hold_info_ratio(benchmark_close)
        out['buy_hold_info_ratio'] = bh
        out['beats_buy_hold'] = bool(ir > bh)
    return out
