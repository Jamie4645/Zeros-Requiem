"""ZTT cost model — session-gated OANDA XAU/USD spread + slippage.

Built in Phase 0 (pulled forward at the Arbiter cost-skeptic's mandate) so the
Phase 4 backtest models realistic intraday cost from day one, rather than a flat
slip scalar that masks the rollover window where ~25% of the user's real trades
sat. The prior SBRS disaster was about impossible FILL PRICES (phantom fills);
this model addresses the second cost axis: spread/slippage magnitude by session.

All figures are ONE-WAY spread in price points ($) for spot Gold. Round-trip
cost = 2 x one-way. A flat per-fill slip surcharge models execution imprecision
on the close-rejection entry.

Sources: arbiter-cost-skeptic + arbiter-execution plan-stage review, 2026-06-09.
These are ASSUMPTIONS to be falsified against measured demo slip (Falsifier F6),
not measured truths. Tunable via the dataclass for the Phase 4 slip A/B sweep.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class ZTTCostModel:
    """Session-gated spread/slip model for 10m XAU/USD.

    one_way_spread maps a UTC-hour bucket -> one-way spread in $ points.
    """
    # one-way spread ($) by session
    spread_london_ny: float = 0.40   # 06:00-20:00 UTC (London + NY liquid hours)
    spread_ny_close: float = 0.75    # 20:00-21:00 UTC
    spread_rollover: float = 1.50    # 21:00-23:00 UTC  (HARD GATE: no new entries)
    spread_asia: float = 0.80        # 23:00-06:00 UTC
    # per-fill execution slip surcharge ($), added one-way; A/B target in Phase 4
    slip_surcharge: float = 0.20
    # hard rules
    block_rollover_entries: bool = True
    rollover_hours: Tuple[int, int] = (21, 23)   # [start, end) UTC, no NEW entries
    min_sl_distance: float = 10.0    # $; reject setups with structural SL < this

    def one_way_spread(self, utc_hour: int) -> float:
        """One-way spread ($) for a given UTC hour (0-23)."""
        if 6 <= utc_hour < 20:
            return self.spread_london_ny
        if 20 <= utc_hour < 21:
            return self.spread_ny_close
        if 21 <= utc_hour < 23:
            return self.spread_rollover
        return self.spread_asia  # 23:00-06:00

    def fill_cost_one_way(self, utc_hour: int) -> float:
        """Total one-way cost ($) charged against a fill: spread + slip surcharge."""
        return self.one_way_spread(utc_hour) + self.slip_surcharge

    def entry_blocked(self, utc_hour: int) -> bool:
        """True if NO new entry may open in this UTC hour (rollover gate)."""
        if not self.block_rollover_entries:
            return False
        lo, hi = self.rollover_hours
        return lo <= utc_hour < hi

    def session_label(self, utc_hour: int) -> str:
        if 6 <= utc_hour < 20:
            return "london_ny"
        if 20 <= utc_hour < 21:
            return "ny_close"
        if 21 <= utc_hour < 23:
            return "rollover"
        return "asia"


# Default instance for the backtest; Phase 4 slip A/B overrides slip_surcharge
# and (separately) sweeps a flat-cost variant to satisfy cost-skeptic's
# "flat vs session-gated PF must not differ > 0.10" falsifier.
DEFAULT_COST = ZTTCostModel()
