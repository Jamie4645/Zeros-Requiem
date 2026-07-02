"""
Hard deployment gate for live order-placing entrypoints.

Canon (CLAUDE.md — 2026-06-01 phantom-fill audit, ZTT rebuild): NOTHING is
live-ready and live size is 0.00% across the board. Until 2026-07-02 that was
only a documentation claim — runner.py and engine_live.py were both launchable
and would place real OANDA orders (Gold capped at 1.00% in risk_manager).

This module makes the freeze a code invariant: every entrypoint that can place
broker orders must call require_live_authorization() BEFORE its main loop.
Without the explicit token below, the process prints why it refused and exits
with code 3 — so a stale Task Scheduler job cannot silently trade.

To intentionally run an order-placing session (e.g. OANDA practice account
demo), set the environment variable:

    ZR_LIVE_TRADING_ENABLE=I-UNDERSTAND-NO-VALIDATED-EDGE

Lifting the gate permanently requires: a validated edge (realistic fills,
walk-forward on the fixed persistent-peak methodology, pre-registered
falsifiers un-tripped) and explicit user approval recorded in CLAUDE.md.
"""

from __future__ import annotations

import os
import sys

ENABLE_VAR = 'ZR_LIVE_TRADING_ENABLE'
ENABLE_TOKEN = 'I-UNDERSTAND-NO-VALIDATED-EDGE'


def live_trading_authorized() -> bool:
    """True only when the operator has explicitly opted in via environment."""
    return os.environ.get(ENABLE_VAR) == ENABLE_TOKEN


def require_live_authorization(entrypoint: str) -> None:
    """Exit(3) unless live order placement was explicitly enabled.

    Call this first in every entrypoint that can reach place_market_order().
    """
    if live_trading_authorized():
        print(
            f"[deploy_gate] {entrypoint}: live order placement EXPLICITLY ENABLED "
            f"via {ENABLE_VAR}.",
            file=sys.stderr,
        )
        return
    print(
        f"[deploy_gate] {entrypoint}: refusing to start.\n"
        f"  Canon: no strategy has a validated edge (2026-06-01 phantom-fill audit); "
        f"live size is 0.00% across the board.\n"
        f"  This gate exists so the freeze is enforced by code, not discipline.\n"
        f"  To run anyway (e.g. OANDA practice/demo), set "
        f"{ENABLE_VAR}={ENABLE_TOKEN}",
        file=sys.stderr,
    )
    sys.exit(3)
