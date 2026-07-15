"""
Realized vs Modeled Slippage Logger (Round 8 Falsifier #1).

Records each live fill's expected-entry vs actual-fill gap so we can reconcile
against the canonical backtest assumption (0.75pt/side indices, 0.0001×
multiplier FX, 0.10×multiplier Gold).

Triggers:
  - Falsifier #1: if realized mean |slip| > modeled × 1.33 across any
    rolling 60d window, demote slip-SLOPE strategies one sizing tier and
    re-convene the council.

Storage: logs/paper/slip_reconciliation.jsonl (one line per fill).
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

LOG_DIR = Path(__file__).resolve().parent.parent.parent / 'logs' / 'paper'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / 'slip_reconciliation.jsonl'


def log_fill(
    symbol: str,
    instrument: str,
    direction: str,
    expected_entry: float,
    actual_fill: Optional[float],
    oanda_trade_id: Optional[str],
    units: float,
    asset_class: str = '',
    note: str = '',
) -> None:
    """Append one fill event to the slip reconciliation log."""
    try:
        rec = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'symbol': symbol,
            'instrument': instrument,
            'direction': direction,
            'expected_entry': float(expected_entry) if expected_entry is not None else None,
            'actual_fill': float(actual_fill) if actual_fill is not None else None,
            'slip_abs': (
                abs(float(actual_fill) - float(expected_entry))
                if (actual_fill is not None and expected_entry is not None)
                else None
            ),
            'slip_signed': (
                (float(actual_fill) - float(expected_entry)) * (1 if direction == 'long' else -1)
                if (actual_fill is not None and expected_entry is not None)
                else None
            ),
            'oanda_trade_id': oanda_trade_id,
            'units': float(units) if units is not None else None,
            'asset_class': asset_class,
            'note': note,
        }
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
    except Exception:
        # Never let the slip logger crash a live run.
        pass
