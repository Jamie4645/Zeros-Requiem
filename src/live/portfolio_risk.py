"""
SBRS 2.0 — Portfolio-Level Risk Aggregation

Tracks total exposure across ALL symbols and enforces portfolio-wide limits.
Prevents over-concentration in correlated positions.

Elite risk management: the system knows total heat at all times.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

STATE_DIR = Path(__file__).resolve().parent.parent.parent / 'state'

MAX_PORTFOLIO_HEAT_PCT = 0.02       # 2% total open risk across all symbols
MAX_CORRELATED_HEAT_PCT = 0.015     # 1.5% max in correlated cluster
MAX_OPEN_POSITIONS_TOTAL = 6        # max across entire portfolio
MAX_PER_SYMBOL = 2                  # max open per single symbol

# Correlation clusters: positions in the same cluster count as correlated
# "weak_usd" = assets that rise when USD falls
# "risk_on" = assets that rise in risk-on environments
CORRELATION_CLUSTERS = {
    'XAU_USD': ['weak_usd'],
    'GBP_USD': ['weak_usd'],
    'EUR_USD': ['weak_usd'],
    'NAS100_USD': ['risk_on'],
    'DE30_EUR': ['risk_on'],
    'SPX500_USD': ['risk_on'],
}

# Direction matters: Gold LONG + GBP/USD LONG = both weak_usd LONG (correlated)
# Gold LONG + GBP/USD SHORT = offsetting (not correlated)


@dataclass
class PortfolioSnapshot:
    """Current portfolio state across all symbols."""
    total_open_positions: int = 0
    total_risk_dollars: float = 0.0
    total_risk_pct: float = 0.0
    cluster_exposure: Dict[str, float] = None  # cluster_name -> net risk $
    per_symbol_count: Dict[str, int] = None    # symbol -> open count
    capital: float = 0.0

    def __post_init__(self):
        if self.cluster_exposure is None:
            self.cluster_exposure = {}
        if self.per_symbol_count is None:
            self.per_symbol_count = {}


def load_portfolio_snapshot() -> PortfolioSnapshot:
    """
    Scan all per-symbol state files and build a portfolio-wide risk picture.
    """
    snap = PortfolioSnapshot()

    if not STATE_DIR.exists():
        return snap

    all_open_trades = []
    capitals = []

    for f in STATE_DIR.glob('sbrs_state_*.json'):
        try:
            with open(f) as fh:
                data = json.load(fh)

            capital = data.get('current_capital', 0)
            capitals.append(capital)
            symbol = data.get('symbol', '')
            instrument = data.get('instrument', '')

            open_trades = data.get('open_trades', [])
            snap.per_symbol_count[symbol] = len(open_trades)
            snap.total_open_positions += len(open_trades)

            for trade in open_trades:
                entry = trade.get('entry_price', 0)
                original_sl = trade.get('original_sl', 0)
                pos_size = trade.get('position_size', 0)
                direction = trade.get('direction', 'long')

                risk_dollars = abs(entry - original_sl) * pos_size
                snap.total_risk_dollars += risk_dollars

                # Track cluster exposure (direction-aware)
                clusters = CORRELATION_CLUSTERS.get(instrument, [])
                sign = 1.0 if direction == 'long' else -1.0
                for cluster in clusters:
                    snap.cluster_exposure[cluster] = snap.cluster_exposure.get(cluster, 0) + (sign * risk_dollars)

        except Exception:
            continue

    snap.capital = max(capitals) if capitals else 0
    if snap.capital > 0:
        snap.total_risk_pct = snap.total_risk_dollars / snap.capital

    return snap


def can_open_position(
    instrument: str,
    symbol: str,
    direction: str,
    risk_dollars: float,
    capital: float,
) -> Tuple[bool, str]:
    """
    Portfolio-level check: can we open a new position?

    Returns (allowed, reason_if_blocked).
    """
    snap = load_portfolio_snapshot()
    snap.capital = max(snap.capital, capital)

    # Check 1: Total open positions
    if snap.total_open_positions >= MAX_OPEN_POSITIONS_TOTAL:
        return False, f"max_portfolio_positions ({snap.total_open_positions}/{MAX_OPEN_POSITIONS_TOTAL})"

    # Check 2: Per-symbol limit
    sym_count = snap.per_symbol_count.get(symbol, 0)
    if sym_count >= MAX_PER_SYMBOL:
        return False, f"max_per_symbol ({sym_count}/{MAX_PER_SYMBOL})"

    # Check 3: Total portfolio heat
    new_total_risk = snap.total_risk_dollars + risk_dollars
    new_risk_pct = new_total_risk / snap.capital if snap.capital > 0 else 1.0
    if new_risk_pct > MAX_PORTFOLIO_HEAT_PCT:
        return False, f"portfolio_heat ({new_risk_pct:.2%} > {MAX_PORTFOLIO_HEAT_PCT:.0%})"

    # Check 4: Correlation cluster exposure
    clusters = CORRELATION_CLUSTERS.get(instrument, [])
    sign = 1.0 if direction == 'long' else -1.0
    for cluster in clusters:
        current_cluster = snap.cluster_exposure.get(cluster, 0)
        new_cluster = current_cluster + (sign * risk_dollars)
        cluster_pct = abs(new_cluster) / snap.capital if snap.capital > 0 else 1.0
        if cluster_pct > MAX_CORRELATED_HEAT_PCT:
            return False, f"correlated_cluster_{cluster} ({cluster_pct:.2%} > {MAX_CORRELATED_HEAT_PCT:.0%})"

    return True, ""


def get_portfolio_summary() -> str:
    """Human-readable portfolio risk summary."""
    snap = load_portfolio_snapshot()
    lines = [
        f"Portfolio: {snap.total_open_positions} positions | "
        f"${snap.total_risk_dollars:,.0f} at risk ({snap.total_risk_pct:.2%})"
    ]
    for sym, count in snap.per_symbol_count.items():
        if count > 0:
            lines.append(f"  {sym}: {count} open")
    for cluster, exposure in snap.cluster_exposure.items():
        if abs(exposure) > 0:
            direction = "LONG" if exposure > 0 else "SHORT"
            lines.append(f"  Cluster [{cluster}]: ${abs(exposure):,.0f} {direction}")
    return "\n".join(lines)
