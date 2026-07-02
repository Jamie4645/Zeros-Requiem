"""
Audit 2026-06-01 — Reversal-trade isolation & phantom-fill diagnostic (blocker #2).

DIAGNOSTIC ONLY — does not modify the engine. Runs the current Gold backtest
(reversal logic ON, as in canon) and splits trades into:
  - PRIMARY      breakout-retest entries (setup.entry_price != broken_level)
  - REVERSAL     failed-breakout-reversal injected entries (entry_price == broken_level)

For every REVERSAL trade it asks the key fill-realism question the methodology
implies ("limit orders only — never market"): on the bar the reversal was
filled, did price ACTUALLY trade to broken_level?
  - SHORT reversal (sell-limit at level): needs fill-bar HIGH >= broken_level
  - LONG  reversal (buy-limit at level):  needs fill-bar LOW  <= broken_level
If not, the backtest booked a fill that a real limit order could NOT have got
on that bar ("phantom fill"). We report how much PnL rides on phantom fills.

Usage:  py -m tests._audit_reversal_stats --period 10y
Writes: logs/audit/reversal_stats.log
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

from src.data.fetcher import fetch
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
from src.core.engine import run_backtest
from src.core.risk_manager import risk_config_for_interval


def _pf(trades):
    gw = sum(t.pnl for t in trades if t.pnl > 0)
    gl = -sum(t.pnl for t in trades if t.pnl <= 0)
    return (gw / gl) if gl > 0 else float('inf')


def _stats(trades):
    n = len(trades)
    if n == 0:
        return dict(n=0, wr=0.0, pnl=0.0, pf=0.0)
    wins = sum(1 for t in trades if t.pnl > 0)
    return dict(n=n, wr=100.0 * wins / n, pnl=sum(t.pnl for t in trades), pf=_pf(trades))


# (symbol, asset_class) — risk passed WITHOUT symbol so SYMBOL_RISK_CAP does not
# zero USDJPY; raw 1% edge measured for every instrument.
INSTRUMENTS = [
    ('GC=F', 'gold'),
    ('^GDAXI', 'indices'),
    ('^IXIC', 'indices'),
    ('GBPUSD=X', 'forex'),
    ('USDJPY=X', 'forex'),
]


def analyze_symbol(symbol, asset_class, period, capital, p):
    p(f"\n  Fetching {symbol} ({asset_class}) 1H {period}...")
    df = fetch(symbol, '1h', period)
    p(f"  Loaded {len(df)} candles ({df.index[0]} -> {df.index[-1]})")

    risk_cfg = risk_config_for_interval('1h', 0.01)
    setups = analyze_sbrs_v2(df, capital, 0.01, asset_class=asset_class)  # no symbol -> no cap
    indicators = get_sbrs_v2_indicators(df)
    res = run_backtest(df, setups, capital, risk_cfg,
                       apply_slippage=True, sbrs_v2_indicators=indicators)

    highs, lows = df['High'].values, df['Low'].values
    closed = [t for t in res.trades if t.pnl != 0.0 or t.exit_index > 0]

    primary, rev_real, rev_phantom = [], [], []
    phantom_gaps = []
    for t in closed:
        lvl = t.setup.broken_level
        is_reversal = lvl != 0.0 and abs(t.setup.entry_price - lvl) < 1e-9
        if not is_reversal:
            primary.append(t); continue
        bi = t.entry_index
        if bi >= len(df):
            rev_phantom.append(t); continue
        hi, lo = highs[bi], lows[bi]
        if t.direction == 'short':
            filled = hi >= lvl - 1e-9
            gap = (lvl - hi) if not filled else 0.0
        else:
            filled = lo <= lvl + 1e-9
            gap = (lo - lvl) if not filled else 0.0
        (rev_real if filled else rev_phantom).append(t)
        if not filled:
            phantom_gaps.append(gap)

    return dict(
        symbol=symbol, closed=closed, primary=primary,
        rev_real=rev_real, rev_phantom=rev_phantom, phantom_gaps=phantom_gaps,
    )


def _print_breakdown(d, p):
    closed, primary = d['closed'], d['primary']
    rev_real, rev_phantom = d['rev_real'], d['rev_phantom']
    allrev = rev_real + rev_phantom
    p("\n" + "=" * 92)
    p(f"  REVERSAL TRADE ISOLATION — {d['symbol']} 1H — reversal ON, slippage ON")
    p("=" * 92)
    p(f"  {'Cohort':<36} | {'Trades':>6} | {'WR':>6} | {'PF':>6} | {'PnL':>13}")
    p("  " + "-" * 88)
    for label, grp in [
        ("ALL trades", closed),
        ("  PRIMARY (breakout-retest)", primary),
        ("  REVERSAL (all)", allrev),
        ("    REVERSAL real-fill (touched lvl)", rev_real),
        ("    REVERSAL PHANTOM-fill (no touch)", rev_phantom),
    ]:
        s = _stats(grp)
        pf = f"{s['pf']:.2f}" if s['pf'] < 100 else "inf"
        p(f"  {label:<36} | {s['n']:>6} | {s['wr']:>5.1f}% | {pf:>6} | ${s['pnl']:>12,.0f}")
    p("=" * 92)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', default='10y')
    ap.add_argument('--symbol', default=None)
    ap.add_argument('--asset-class', default='gold')
    ap.add_argument('--capital', type=float, default=10000.0)
    ap.add_argument('--all', action='store_true', help='Run all 5 canonical instruments')
    args = ap.parse_args()

    lines = []
    p = lambda s: (lines.append(s), print(s))

    targets = INSTRUMENTS if args.all else [(args.symbol or 'GC=F', args.asset_class)]
    summary = []
    for symbol, ac in targets:
        try:
            d = analyze_symbol(symbol, ac, args.period, args.capital, p)
        except Exception as e:
            p(f"  !! {symbol} failed: {e}")
            continue
        _print_breakdown(d, p)
        tot = _stats(d['closed'])['pnl']
        srp = _stats(d['rev_phantom'])
        srr = _stats(d['rev_real'])
        sp = _stats(d['primary'])
        legit = sp['pnl'] + srr['pnl']
        summary.append(dict(
            symbol=symbol, total=tot, n=len(d['closed']),
            phantom_n=srp['n'], phantom_pnl=srp['pnl'],
            phantom_share=(100 * srp['pnl'] / tot if tot else 0),
            legit_pnl=legit,
        ))

    if summary:
        p("\n" + "#" * 92)
        p("  PORTFOLIO-WIDE PHANTOM-FILL DEPENDENCE (raw 1% risk, no cap)")
        p("#" * 92)
        p(f"  {'Symbol':<10} | {'Trades':>6} | {'Total PnL':>12} | {'Phantom #':>9} | {'Phantom PnL':>12} | {'Phantom %':>9} | {'Legit PnL':>11}")
        p("  " + "-" * 88)
        for s in summary:
            p(f"  {s['symbol']:<10} | {s['n']:>6} | ${s['total']:>11,.0f} | {s['phantom_n']:>9} | ${s['phantom_pnl']:>11,.0f} | {s['phantom_share']:>8.1f}% | ${s['legit_pnl']:>10,.0f}")
        p("#" * 92)
        p("  'Legit PnL' = primary breakout-retest + reversals that actually touched the level.")
        p("  High Phantom % => that instrument's backtested edge is largely an impossible-fill artefact.")

    out = Path(__file__).resolve().parent.parent / 'logs' / 'audit' / ('reversal_stats_all.log' if args.all else 'reversal_stats.log')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
    p(f"\n  Written to {out}")


if __name__ == '__main__':
    main()
