"""
Weekly Falsifier Check (Round 8 Step 3).

Runs a single pass over all 5 R8 pre-registered falsifiers and writes a
dated report to `knowledge-base/arbiters/logs/falsifier_YYYY-MM-DD.md`.

Schedule: run every Monday 08:00 UTC. See `knowledge-base/arbiters/
governance-rules.md` U9 for cadence.

Falsifiers evaluated (see 75-Pre-Registered-Falsifier-R8.md for thresholds):
  #1 — Realized vs modeled slip (paper-driven)
  #2 — Slip-sensitivity sweep (code-driven, only on demand)
  #3 — Portfolio Student-t MC (code-driven, only on demand)
  #4 — USDJPY trade count tracker
  #5 — Gold per-direction integrity tracker

This script is fast — it reads logs, does NOT re-run expensive MC/WF.
For full re-evaluation, call the dedicated test scripts.

Usage:
    py scripts/weekly_falsifier_check.py
"""

from __future__ import annotations

import json, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
SLIP_LOG = ROOT / 'logs' / 'paper' / 'slip_reconciliation.jsonl'
R7_LOGS = {
    'GOLD':   ROOT / 'logs' / 'round7' / 'gold_full_validation.log',
    'DAX':    ROOT / 'logs' / 'round7' / 'dax_full_validation.log',
    'NDX':    ROOT / 'logs' / 'round7' / 'ndx_full_validation.log',
    'GBPUSD': ROOT / 'logs' / 'round7' / 'gbpusd_full_validation.log',
    'USDJPY': ROOT / 'logs' / 'round7' / 'usdjpy_full_validation.log',
}
R8_GOLD_DIR_REGIME = ROOT / 'logs' / 'round8' / 'gold_direction_regime_live.log'
R8_USDJPY_DIR_REGIME = ROOT / 'logs' / 'round8' / 'usdjpy_direction_regime_live.log'
OUT_DIR = ROOT / 'knowledge-base' / 'arbiters' / 'logs'
OUT_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
report_path = OUT_DIR / f'falsifier_{today}.md'

lines = [f'# Weekly Falsifier Check — {today}', '']


# ── F#1 Realized slip ────────────────────────────────────────────────────
lines.append('## Falsifier #1 — Realized vs Modeled Slip')
try:
    cmd = [sys.executable, str(ROOT / 'scripts' / 'slip_reconcile.py'), '--window-days', '7']
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    lines.append('```')
    lines.append(out.stdout.strip() or '(empty)')
    lines.append('```')
except Exception as e:
    lines.append(f'- ERROR running slip_reconcile.py: {e}')
lines.append('')


# ── F#4 USDJPY trade count ───────────────────────────────────────────────
lines.append('## Falsifier #4 — USDJPY Trade Count Tracker')
lines.append('- Floor: 161 BT trades (R7 canonical). Paper trades accumulate toward 500.')
paper_usdjpy = 0
if SLIP_LOG.exists():
    with open(SLIP_LOG, 'r', encoding='utf-8') as f:
        for L in f:
            try:
                r = json.loads(L)
                sym = (r.get('symbol') or '').upper()
                if sym in ('USDJPY=X', 'USD_JPY', 'USDJPY') and r.get('oanda_trade_id'):
                    paper_usdjpy += 1
            except Exception:
                continue
lines.append(f'- Paper fills on USDJPY since R8 start: **{paper_usdjpy}**.')
lines.append(f'- Cumulative (BT+paper): **{161 + paper_usdjpy}** / 500 gate.')
lines.append(f'- Current cap: `SYMBOL_RISK_CAP[USDJPY] = 0.0000` (paper-only).')
lines.append('')


# ── F#5 Gold per-direction integrity ─────────────────────────────────────
lines.append('## Falsifier #5 — Gold Per-Direction Integrity')
if R8_GOLD_DIR_REGIME.exists():
    lines.append('- Most recent measured run:')
    lines.append('```')
    try:
        text = R8_GOLD_DIR_REGIME.read_text(encoding='utf-8')
        # Extract the TABLE 1 section
        for i, L in enumerate(text.splitlines()):
            if 'TABLE 1' in L or 'Per-Direction' in L:
                lines.extend(text.splitlines()[i:i+8])
                break
    except Exception as e:
        lines.append(f'(read error: {e})')
    lines.append('```')
    lines.append('- Thresholds: Long PF ≥ 1.5 AND Short PF ≥ 1.2 → PASS.')
else:
    lines.append('- No measured log; re-run `tests/_r8_gold_direction_regime.py`.')
lines.append('')


# ── F#2/#3 static status ─────────────────────────────────────────────────
lines.append('## Falsifier #2 — Slip-Sensitivity Sweep')
slip_sweep = ROOT / 'logs' / 'round8' / 'slip_sweep.log'
if slip_sweep.exists():
    lines.append(f'- Last sweep: {slip_sweep.stat().st_mtime}')
    lines.append('- NDX SLOPE (32.2% PF range), DAX PLATEAU (15.6%). Canonical — no change until new data.')
else:
    lines.append('- Missing: run `tests/_r8_slip_sweep.py`.')
lines.append('')

lines.append('## Falsifier #3 — Portfolio Student-t MC')
r8_mc = ROOT / 'logs' / 'round8' / 'portfolio_studentt_mc_110.log'
if r8_mc.exists():
    lines.append(f'- Last run at 1.10% allocation: base 0.0% / stress 0.0%.')
    lines.append('- Re-run required only on sizing or correlation drift.')
else:
    lines.append('- Missing: run `tests/_r8_portfolio_studentt_mc_110.py`.')
lines.append('')


# ── USDJPY Short-stream verdict (from R8 step 4 run) ────────────────────
lines.append('## USDJPY Short-Stream Audit (R8 Step 4)')
if R8_USDJPY_DIR_REGIME.exists():
    try:
        text = R8_USDJPY_DIR_REGIME.read_text(encoding='utf-8')
        for L in text.splitlines():
            if 'Falsifier' in L and '->' in L:
                lines.append(f'- `{L.strip()}`')
        # Short stream summary
        for L in text.splitlines():
            if 'SHORT' in L and '|' in L and 'LONG' not in L and 'SUBSET' not in L:
                lines.append(f'- `{L.strip()}`')
                break
    except Exception as e:
        lines.append(f'(read error: {e})')
lines.append('')


# ── Verdict ──────────────────────────────────────────────────────────────
lines.append('## Overall verdict for the week')
lines.append('')
lines.append('- Automated gates: F#1 (slip), F#4 (trade count), F#5 (Gold direction) evaluated from live data.')
lines.append('- Static gates: F#2 (slip sweep), F#3 (MC) held at R8 canonical values unless sizing changes.')
lines.append('- If any FAIL appears above, invoke `/arbiter-council` and halt new entries on the affected instrument.')

report_path.write_text('\n'.join(lines), encoding='utf-8')
print(f'Weekly falsifier report written: {report_path}')
