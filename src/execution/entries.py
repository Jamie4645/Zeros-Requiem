"""
Trade Setup & Entry Logic for SBRS 1.1

Defines the TradeSetup dataclass used by all SBRS regimes and the backtest engine.
"""

import pandas as pd
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeSetup:
    """A validated trade setup ready for execution."""
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_reward: float
    regime: str               # "sbrs_gold", "sbrs_indices", etc.
    index: int                # Bar where setup was identified

    # SBRS context (optional, for analysis/debugging)
    broken_level: float = 0.0       # The swing level that was broken
    retest_bar: int = 0             # Bar index of the confirmed retest
    break_bar: int = 0              # Bar index of the structure break

    # Execution tracking
    filled: bool = False
    fill_index: Optional[int] = None
