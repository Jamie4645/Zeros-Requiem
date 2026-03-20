"""
Entry Execution Logic for SCAF 2.0

The three-layer validation:
1. Liquidity Grab confirmed
2. Displacement Factor >= min_df (default 1.0, parameterised)
3. Entry at FVG midpoint (limit order)

Also handles stop loss and take profit placement.

Priority 1.4: Default min_df lowered from 1.5 to 1.0.
"""

import pandas as pd
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from .liquidity import LiquiditySweep, SweepDirection
from .displacement import FairValueGap, FVGDirection
from ..indicators.technical import atr


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeSetup:
    """A validated trade setup ready for execution."""
    direction: TradeDirection
    entry_price: float        # FVG midpoint
    stop_loss: float          # Beyond the sweep extreme
    take_profit: float        # 2x FVG size or next liquidity level
    position_size: float      # Calculated by risk manager
    risk_reward: float
    regime: str               # "gold_asia_mr", "gold_ny_momentum", "forex_killzone", "crypto_compression"
    sweep: LiquiditySweep     # The liquidity event
    fvg: FairValueGap         # The fair value gap
    displacement_df: float    # Df value
    index: int                # Bar where setup was identified
    
    # Execution tracking
    filled: bool = False
    fill_index: Optional[int] = None


def validate_entry(
    sweep: LiquiditySweep,
    fvg: FairValueGap,
    df: pd.DataFrame,
    index: int,
    regime: str,
    equity: float = 10000.0,
    risk_pct: float = 0.01,
    min_rr: float = 1.5,
    min_df: float = 1.0
) -> Optional[TradeSetup]:
    """
    Validate all three execution layers and create a TradeSetup.
    
    Layer 1: Liquidity Grab (sweep must exist)
    Layer 2: Displacement (FVG must have Df >= min_df)  
    Layer 3: Entry at FVG midpoint with defined SL/TP
    
    Returns TradeSetup if valid, None if any layer fails.
    """
    # Layer 1: Sweep direction must match FVG direction
    if sweep.direction == SweepDirection.BULLISH and fvg.direction != FVGDirection.BULLISH:
        return None
    if sweep.direction == SweepDirection.BEARISH and fvg.direction != FVGDirection.BEARISH:
        return None
    
    # Layer 2: Df check (already done in FVG detection, but verify)
    if fvg.displacement_df < min_df:
        return None
    
    # Layer 3: Calculate entry, SL, TP
    entry_price = fvg.midpoint
    
    # ATR for position sizing
    atr_series = atr(df, 14)
    atr_val = atr_series.iloc[index] if not pd.isna(atr_series.iloc[index]) else 0
    
    if fvg.direction == FVGDirection.BULLISH:
        direction = TradeDirection.LONG
        stop_loss = sweep.sweep_extreme - (atr_val * 0.5)  # Below sweep low + buffer
        take_profit = entry_price + (fvg.size * 3)  # 3x FVG size as target
    else:
        direction = TradeDirection.SHORT
        stop_loss = sweep.sweep_extreme + (atr_val * 0.5)  # Above sweep high + buffer
        take_profit = entry_price - (fvg.size * 3)
    
    # Calculate risk/reward
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    
    if risk <= 0:
        return None
    
    risk_reward = reward / risk
    
    if risk_reward < min_rr:
        return None
    
    # Position sizing: risk exactly 1% of equity
    # PositionSize = (Equity * 0.01) / (ATR(14) * 2)
    if atr_val > 0:
        position_size = (equity * risk_pct) / (atr_val * 2)
    else:
        position_size = (equity * risk_pct) / risk if risk > 0 else 0
    
    return TradeSetup(
        direction=direction,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size,
        risk_reward=risk_reward,
        regime=regime,
        sweep=sweep,
        fvg=fvg,
        displacement_df=fvg.displacement_df,
        index=index
    )
