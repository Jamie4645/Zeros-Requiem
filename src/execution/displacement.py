"""
Displacement & Fair Value Gap (FVG) Detection for SCAF 2.0

Displacement = institutional candle that moves aggressively in one direction.
Measured by the Displacement Factor (Df), a Z-score of candle body size.

Fair Value Gap (FVG) = price imbalance left by the displacement candle.
Created when candle N's range doesn't overlap with candle N-2's range.
The gap between them is the FVG -- price tends to return to fill it.

Priority 1.1 Enhancement: Near-FVG tolerance allows partial gaps where
candles overlap by less than a configurable ATR-relative amount. On higher
timeframes (4H, Daily) true gaps are extremely rare -- this catches the
"almost-gap" imbalances that still represent institutional displacement.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from ..indicators.technical import displacement_factor, atr as calc_atr


class FVGDirection(Enum):
    BULLISH = "bullish"   # Gap up -- expect price to drop back to fill
    BEARISH = "bearish"   # Gap down -- expect price to rise back to fill


@dataclass
class FairValueGap:
    """A detected Fair Value Gap."""
    direction: FVGDirection
    top: float              # Upper edge of the gap
    bottom: float           # Lower edge of the gap
    midpoint: float         # Entry point (FVG midpoint)
    size: float             # Gap size (can be negative for near-FVGs, stored as effective size)
    index: int              # Bar index where FVG was created
    displacement_df: float  # The Df value of the displacement candle
    is_near_fvg: bool = False   # True if this was a partial gap (near-FVG)
    filled: bool = False        # Has price returned to fill this gap?


def detect_fvg(
    df: pd.DataFrame,
    index: int,
    min_df: float = 2.0,
    precomputed_df: Optional[pd.Series] = None,
    overlap_tolerance_atr: float = 0.1,
    precomputed_atr: Optional[pd.Series] = None
) -> Optional[FairValueGap]:
    """
    Detect a Fair Value Gap at the given index.
    
    An FVG occurs when three consecutive candles create a gap:
    - Bullish FVG: candle[i]'s low > candle[i-2]'s high (gap up)
    - Bearish FVG: candle[i]'s high < candle[i-2]'s low (gap down)
    
    Near-FVG tolerance (Priority 1.1): If the candles overlap by less than
    overlap_tolerance_atr * ATR(14), it's treated as a "near-FVG". The gap
    edges are set to the midpoint between the overlapping wicks, giving a
    small but valid imbalance zone for entry.
    
    Only reported if the middle candle (i-1) has Df >= min_df (institutional displacement).
    
    Args:
        df: OHLCV DataFrame
        index: Current bar index (the third candle of the pattern)
        min_df: Minimum displacement factor for the middle candle
        precomputed_df: Optional pre-calculated displacement_factor series
        overlap_tolerance_atr: Max overlap (in ATR units) to still count as near-FVG.
                               0.0 = strict classic FVG only, 0.1 = allow 10% ATR overlap.
        precomputed_atr: Optional pre-calculated ATR(14) series for near-FVG calc
    """
    if index < 52:  # Need 50 bars for Df calculation + 2 lookback
        return None
    
    # Get the three candles
    candle_0_high = df['High'].iloc[index - 2]    # First candle
    candle_0_low = df['Low'].iloc[index - 2]
    candle_1_open = df['Open'].iloc[index - 1]    # Middle candle (displacement)
    candle_1_close = df['Close'].iloc[index - 1]
    candle_2_high = df['High'].iloc[index]         # Third candle
    candle_2_low = df['Low'].iloc[index]
    
    # Use pre-computed Df series if available, otherwise calculate (backward compat)
    df_series = precomputed_df if precomputed_df is not None else displacement_factor(df, 50)
    if pd.isna(df_series.iloc[index - 1]):
        return None
    
    df_value = df_series.iloc[index - 1]
    
    if df_value < min_df:
        return None  # Not enough displacement
    
    # Calculate ATR for near-FVG tolerance
    atr_val = 0.0
    if overlap_tolerance_atr > 0:
        if precomputed_atr is not None:
            atr_val = precomputed_atr.iloc[index] if not pd.isna(precomputed_atr.iloc[index]) else 0.0
        else:
            atr_series = calc_atr(df, 14)
            atr_val = atr_series.iloc[index] if not pd.isna(atr_series.iloc[index]) else 0.0
    
    max_overlap = atr_val * overlap_tolerance_atr
    
    # ------------------------------------------------------------------
    # Check for Bullish FVG: candle 2's low vs candle 0's high
    # Classic:  candle_2_low > candle_0_high  (true gap)
    # Near-FVG: candle_2_low > candle_0_high - max_overlap  (small overlap ok)
    # ------------------------------------------------------------------
    bullish_gap = candle_2_low - candle_0_high  # positive = true gap, negative = overlap
    
    if bullish_gap > 0:
        # Classic bullish FVG (true gap)
        return FairValueGap(
            direction=FVGDirection.BULLISH,
            top=candle_2_low,
            bottom=candle_0_high,
            midpoint=(candle_2_low + candle_0_high) / 2,
            size=bullish_gap,
            index=index,
            displacement_df=df_value,
            is_near_fvg=False
        )
    elif bullish_gap >= -max_overlap and max_overlap > 0:
        # Near-FVG: small overlap, still an imbalance zone
        # The "gap" edges converge -- use midpoint of the overlapping wicks
        mid = (candle_2_low + candle_0_high) / 2
        # Effective size: use the displacement candle's body as proxy for imbalance strength
        effective_size = abs(candle_1_close - candle_1_open) * 0.25  # 25% of displacement body
        if effective_size > 0 and candle_1_close > candle_1_open:  # Bullish displacement
            return FairValueGap(
                direction=FVGDirection.BULLISH,
                top=mid + effective_size / 2,
                bottom=mid - effective_size / 2,
                midpoint=mid,
                size=effective_size,
                index=index,
                displacement_df=df_value,
                is_near_fvg=True
            )
    
    # ------------------------------------------------------------------
    # Check for Bearish FVG: candle 2's high vs candle 0's low
    # Classic:  candle_2_high < candle_0_low  (true gap)
    # Near-FVG: candle_2_high < candle_0_low + max_overlap  (small overlap ok)
    # ------------------------------------------------------------------
    bearish_gap = candle_0_low - candle_2_high  # positive = true gap, negative = overlap
    
    if bearish_gap > 0:
        # Classic bearish FVG (true gap)
        return FairValueGap(
            direction=FVGDirection.BEARISH,
            top=candle_0_low,
            bottom=candle_2_high,
            midpoint=(candle_0_low + candle_2_high) / 2,
            size=bearish_gap,
            index=index,
            displacement_df=df_value,
            is_near_fvg=False
        )
    elif bearish_gap >= -max_overlap and max_overlap > 0:
        # Near-FVG: small overlap, still an imbalance zone
        mid = (candle_0_low + candle_2_high) / 2
        effective_size = abs(candle_1_close - candle_1_open) * 0.25
        if effective_size > 0 and candle_1_close < candle_1_open:  # Bearish displacement
            return FairValueGap(
                direction=FVGDirection.BEARISH,
                top=mid + effective_size / 2,
                bottom=mid - effective_size / 2,
                midpoint=mid,
                size=effective_size,
                index=index,
                displacement_df=df_value,
                is_near_fvg=True
            )
    
    return None


def check_fvg_fill(fvg: FairValueGap, df: pd.DataFrame, index: int) -> bool:
    """
    Check if price has returned to fill (touch) the FVG midpoint.
    
    For a bullish FVG: price must drop down to the midpoint (long entry)
    For a bearish FVG: price must rise up to the midpoint (short entry)
    """
    current_high = df['High'].iloc[index]
    current_low = df['Low'].iloc[index]
    
    if fvg.direction == FVGDirection.BULLISH:
        # Price needs to pull back DOWN to the FVG midpoint
        return current_low <= fvg.midpoint
    
    elif fvg.direction == FVGDirection.BEARISH:
        # Price needs to push back UP to the FVG midpoint
        return current_high >= fvg.midpoint
    
    return False


def scan_active_fvgs(
    df: pd.DataFrame,
    start_index: int,
    end_index: int,
    min_df: float = 2.0,
    max_age: int = 50,
    overlap_tolerance_atr: float = 0.1
) -> List[FairValueGap]:
    """
    Scan for all unfilled FVGs in a range.
    
    Returns list of FVGs that have been created but not yet filled.
    FVGs older than max_age bars are discarded.
    """
    active_fvgs = []
    
    # Pre-compute ATR once for the whole scan
    atr_series = calc_atr(df, 14)
    
    for i in range(start_index, end_index + 1):
        # Check if any existing FVG gets filled
        for fvg in active_fvgs[:]:
            if check_fvg_fill(fvg, df, i):
                fvg.filled = True
                active_fvgs.remove(fvg)
            elif i - fvg.index > max_age:
                active_fvgs.remove(fvg)  # Too old
        
        # Detect new FVG (with near-FVG tolerance)
        new_fvg = detect_fvg(df, i, min_df,
                             overlap_tolerance_atr=overlap_tolerance_atr,
                             precomputed_atr=atr_series)
        if new_fvg:
            active_fvgs.append(new_fvg)
    
    return active_fvgs
