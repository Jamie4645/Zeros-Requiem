"""
SBRS 2.0 Ablation Study — Systematic Feature Isolation

Runs 17 test configurations by monkey-patching strategy constants,
then produces a comparison table showing each feature's contribution.

Usage:
    py -m tests.ablation_study
    py -m tests.ablation_study --period 2y       # Shorter for quick test
    py -m tests.ablation_study --period 10y       # Full validation
"""

import sys
import argparse
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

from src.data.fetcher import fetch, detect_asset_class
from src.regimes.sbrs_v2 import analyze_sbrs_v2, get_sbrs_v2_indicators
import src.regimes.sbrs_v2 as v2_module
from src.core.engine import run_backtest
from src.core.risk_manager import RiskConfig, risk_config_for_interval


@dataclass
class AblationResult:
    name: str
    trades: int
    wins: int
    win_rate: float
    pnl: float
    profit_factor: float
    sharpe: float
    max_dd: float
    expectancy: float
    avg_win: float
    avg_loss: float


# ═══════════════════════════════════════════════════════════════
# TEST CONFIGURATIONS
# Each config: (name, dict of constants to override)
# ═══════════════════════════════════════════════════════════════

ABLATION_TESTS: List[Tuple[str, Dict[str, Any]]] = [
    # ── Category A: Signal Isolation ──────────────────────────
    ("Baseline (full v2.0)", {}),

    ("1. No FVG",
     {"CONFLUENCE_SCORE_FVG": 0.0}),

    ("2. No Liquidity Sweep",
     {"CONFLUENCE_SCORE_LIQUIDITY": 0.0}),

    ("3. No FVG + No Liquidity",
     {"CONFLUENCE_SCORE_FVG": 0.0, "CONFLUENCE_SCORE_LIQUIDITY": 0.0}),

    ("4. No MA Cross Score",
     {"CONFLUENCE_SCORE_MA_CROSS": 0.0}),

    ("5. MA Cross ONLY",
     {"CONFLUENCE_SCORE_FVG": 0.0, "CONFLUENCE_SCORE_LIQUIDITY": 0.0,
      "CONFLUENCE_SCORE_LEVEL_QUALITY": 0.0}),

    # ── Category B: Filter Isolation ─────────────────────────
    ("6. No Level Gate (0 touches)",
     {"MIN_LEVEL_TOUCHES": 0}),

    ("7. No Counter-Trend",
     {"CONFLUENCE_MIN_COUNTER_TREND": 99.0}),

    ("8. No Session Filter",
     {"SESSION_BLOCK_START_HOUR": 99}),

    ("9. No Squeeze Filter",
     {"SQUEEZE_REJECT_FIRST_BREAK": False}),

    ("10. No Whipsaw Detection",
     {"_DISABLE_WHIPSAW": True}),

    # ── Category C: Convention & Threshold ────────────────────
    # Uses whole-system flag USE_OLD_MA_CONVENTION (Round 4 fix): patches
    # compute_4h_context, check_ma_cross, AND engine MA callsites. Round 3
    # was partial-patch artefact (1/3 callsites) — see 66-Ablation-Round-3.
    ("11. Old MA Convention (SMMA>WMA=bull)",
     {"_USE_OLD_MA_CONVENTION_FULL": True}),

    ("12. Higher Threshold (1.5)",
     {"CONFLUENCE_MIN_WITH_TREND": 1.5}),

    ("13. Kitchen Sink OFF",
     {"CONFLUENCE_SCORE_FVG": 0.0, "CONFLUENCE_SCORE_LIQUIDITY": 0.0,
      "CONFLUENCE_SCORE_LEVEL_QUALITY": 0.0, "MIN_LEVEL_TOUCHES": 0,
      "CONFLUENCE_MIN_COUNTER_TREND": 99.0, "SESSION_BLOCK_START_HOUR": 99,
      "SQUEEZE_REJECT_FIRST_BREAK": False, "_DISABLE_WHIPSAW": True}),

    # ── Bonus: Retest & Chop Tuning ──────────────────────────
    ("14. Tight Retest (0.3 ATR all)",
     {"RETEST_TOLERANCE_ATR": 0.3, "INDICES_RETEST_TOLERANCE_ATR_V2": 0.3}),

    ("15. Wide Retest (0.8 ATR all)",
     {"RETEST_TOLERANCE_ATR": 0.8, "RETEST_TOLERANCE_ATR_SHORT": 0.6,
      "INDICES_RETEST_TOLERANCE_ATR_V2": 0.8}),

    ("16. No False Breakout Filter",
     {"_DISABLE_FALSE_BO": True}),

    ("17. No Chop Filter",
     {"CHOP_ATR_THRESHOLD": 0.0}),
]


def _save_and_patch(overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Save current values and apply overrides. Returns the saved originals."""
    originals = {}
    for key, val in overrides.items():
        if key.startswith('_'):
            continue
        if hasattr(v2_module, key):
            originals[key] = getattr(v2_module, key)
            setattr(v2_module, key, val)
    return originals


def _restore(originals: Dict[str, Any]):
    """Restore saved original values."""
    for key, val in originals.items():
        setattr(v2_module, key, val)


def _patch_functions(overrides: Dict[str, Any]):
    """
    Handle special flags that require function-level patching.
    Returns a cleanup function.
    """
    cleanups = []

    if overrides.get('_DISABLE_WHIPSAW'):
        if hasattr(v2_module, 'detect_ma_whipsaw'):
            original_fn = v2_module.detect_ma_whipsaw
            v2_module.detect_ma_whipsaw = lambda *a, **kw: False
            cleanups.append(('detect_ma_whipsaw', original_fn))
        # else: whipsaw detection already removed from sbrs_v2 — variant is a no-op

    if overrides.get('_USE_OLD_MA_CONVENTION_FULL'):
        # Council Round 4 fix: set whole-system flag so ALL 4 MA callsites flip
        # coherently (compute_4h_context, check_ma_cross, engine inline checks).
        # Round 3 used partial patch (1 of 3 callsites) and produced PF 5.23
        # chimera result. See knowledge-base/66-Ablation-Round-3-Post-Change.md.
        original_flag = v2_module.USE_OLD_MA_CONVENTION
        v2_module.USE_OLD_MA_CONVENTION = True
        def _restore_flag():
            v2_module.USE_OLD_MA_CONVENTION = original_flag
        cleanups.append(('_flag_restore', _restore_flag))

    if overrides.get('_DISABLE_FALSE_BO'):
        if hasattr(v2_module, 'detect_false_breakout'):
            original_fn = v2_module.detect_false_breakout
            v2_module.detect_false_breakout = lambda *a, **kw: False
            cleanups.append(('detect_false_breakout', original_fn))

    return cleanups


def _restore_functions(cleanups):
    for name, fn in cleanups:
        if name == '_flag_restore':
            fn()  # callable, not an attribute to assign
        else:
            setattr(v2_module, name, fn)


def run_single_test(
    name: str, overrides: Dict[str, Any],
    df, risk_config, capital, slippage
) -> AblationResult:
    """Run one ablation test with the given overrides."""
    originals = _save_and_patch(overrides)
    fn_cleanups = _patch_functions(overrides)

    try:
        setups = analyze_sbrs_v2(df, capital, 0.01, asset_class='gold')
        indicators = get_sbrs_v2_indicators(df)
        result = run_backtest(
            df, setups, capital, risk_config,
            apply_slippage=slippage,
            sbrs_v2_indicators=indicators
        )
        return AblationResult(
            name=name,
            trades=result.total_trades,
            wins=result.winning_trades,
            win_rate=result.win_rate,
            pnl=result.total_pnl,
            profit_factor=result.profit_factor,
            sharpe=result.sharpe_ratio,
            max_dd=result.max_drawdown_pct,
            expectancy=result.expectancy,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
        )
    finally:
        _restore_functions(fn_cleanups)
        _restore(originals)


def print_results(results: List[AblationResult]):
    """Print the ablation comparison table."""
    baseline = results[0] if results else None

    print("\n" + "=" * 130)
    print("  SBRS 2.0 ABLATION STUDY — Feature Contribution Analysis")
    print("=" * 130)
    print(f"  {'Test':<38} | {'Trades':>6} | {'WR':>6} | {'PF':>5} | {'PnL':>11} | {'Sharpe':>6} | {'MaxDD':>6} | {'Exp/Trade':>10} | {'vs Base':>8}")
    print("  " + "-" * 126)

    for r in results:
        pnl_delta = ""
        if baseline and r.name != baseline.name and baseline.pnl != 0:
            delta_pct = ((r.pnl - baseline.pnl) / abs(baseline.pnl)) * 100
            pnl_delta = f"{delta_pct:+.1f}%"
        elif r.name == baseline.name:
            pnl_delta = "BASE"

        pf_str = f"{r.profit_factor:.2f}" if r.profit_factor < 100 else "inf"

        print(f"  {r.name:<38} | {r.trades:>6} | {r.win_rate:>5.1f}% | {pf_str:>5} | ${r.pnl:>10,.2f} | {r.sharpe:>6.2f} | {r.max_dd:>5.1f}% | ${r.expectancy:>9,.2f} | {pnl_delta:>8}")

    print("=" * 130)

    if baseline:
        print(f"\n  Baseline: {baseline.trades} trades, PF {baseline.profit_factor:.2f}, ${baseline.pnl:,.2f} PnL")

    # Find best and worst
    non_baseline = [r for r in results if r.name != baseline.name] if baseline else results
    if non_baseline:
        best = max(non_baseline, key=lambda r: r.pnl)
        worst = min(non_baseline, key=lambda r: r.pnl)
        print(f"  Best variant:  {best.name} — ${best.pnl:,.2f} PnL, PF {best.profit_factor:.2f}")
        print(f"  Worst variant: {worst.name} — ${worst.pnl:,.2f} PnL, PF {worst.profit_factor:.2f}")

        # Identify what's helping vs hurting
        print(f"\n  {'-' * 60}")
        print(f"  FEATURE IMPACT ANALYSIS (positive = removing it HURTS)")
        print(f"  {'-' * 60}")
        for r in non_baseline:
            if baseline:
                delta = r.pnl - baseline.pnl
                label = "HELPING" if delta < 0 else "HURTING" if delta > 50 else "NEUTRAL"
                arrow = "↓" if delta < 0 else "↑" if delta > 0 else "→"
                print(f"    {r.name:<38} {arrow} ${delta:>+10,.2f}  [{label}]")

    print()


def main():
    parser = argparse.ArgumentParser(description="SBRS 2.0 Ablation Study")
    parser.add_argument('--period', default='10y', help='Data period (default: 10y)')
    parser.add_argument('--symbol', default='GC=F', help='Symbol (default: GC=F)')
    parser.add_argument('--capital', type=float, default=10000.0)
    parser.add_argument('--no-slippage', action='store_true')
    args = parser.parse_args()

    asset_class = detect_asset_class(args.symbol)
    risk_config = risk_config_for_interval('1h', 0.01)

    print(f"\n  Fetching {args.symbol} 1H {args.period} data...")
    t0 = time.time()
    df = fetch(args.symbol, '1h', args.period)
    print(f"  Loaded {len(df)} candles in {time.time() - t0:.1f}s")
    print(f"  Range: {df.index[0]} to {df.index[-1]}")
    print(f"\n  Running {len(ABLATION_TESTS)} ablation tests...\n")

    results = []
    for i, (name, overrides) in enumerate(ABLATION_TESTS):
        t1 = time.time()
        print(f"  [{i+1:>2}/{len(ABLATION_TESTS)}] {name}...", end=" ", flush=True)
        r = run_single_test(name, overrides, df, risk_config, args.capital, not args.no_slippage)
        elapsed = time.time() - t1
        print(f"{r.trades} trades, PF {r.profit_factor:.2f}, ${r.pnl:,.2f} ({elapsed:.1f}s)")
        results.append(r)

    print_results(results)

    total_time = time.time() - t0
    print(f"  Total time: {total_time:.0f}s ({total_time/60:.1f} min)")


if __name__ == '__main__':
    main()
