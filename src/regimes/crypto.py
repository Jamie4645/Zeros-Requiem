"""
Crypto (BTC/ETH) Regime for SCAF 2.0

The Volatility Compression Strategy:
1. Monitor Volatility Ratio: VR = ATR(5) / ATR(50)
2. VR < 0.8 = "High Alert" (coiled spring, relaxed from 0.7 for more signals)
3. Scan for liquidity sweep of Weekly High/Low or PDH/PDL
4. Confirm with expansion candle (body > 65% of range)  [Priority 1.5: was 80%]
5. Confirm Displacement Factor (Df > 1.0)  [Priority 1.4: was 1.5]
6. Enter at FVG midpoint or on displacement candle close

Crypto is 24/7 -- no session restrictions, purely volatility-driven.

Priority 1.4: Df thresholds lowered (FVG: 1.5→1.0, fallback: 1.0→0.75)
Priority 1.5: Expansion candle threshold lowered (0.75→0.65)
Priority 1.6: EMA trend filter widened (2%→3%)
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from dataclasses import dataclass

from ..indicators.technical import (
    atr, ema, volatility_ratio, displacement_factor
)
from ..indicators.candlestick import is_expansion_candle
from ..execution.liquidity import (
    detect_liquidity_sweep, LiquiditySweep, SweepDirection,
    get_previous_day_levels
)
from ..execution.displacement import detect_fvg, FairValueGap, FVGDirection
from ..execution.entries import validate_entry, TradeSetup


def _get_weekly_levels(df: pd.DataFrame, current_index: int) -> tuple:
    """
    Get the Weekly High and Weekly Low looking back 5-7 trading days.
    
    Returns (weekly_high, weekly_low).
    """
    # Look back ~35 bars on 4H (7 days * 5 bars/day) or 7 bars on daily
    lookback = min(40, current_index)
    if lookback < 5:
        return (0.0, 0.0)
    
    window = df.iloc[current_index - lookback:current_index]
    return (window['High'].max(), window['Low'].min())


def analyze_crypto(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01
) -> List[TradeSetup]:
    """
    Run Crypto regime analysis across all bars.
    
    Two entry strategies:
    A. Volatility Compression (original):
       VR < 0.8 → sweep → expansion + Df → FVG or fallback
    
    B. Trend Momentum (N3 — new):
       EMA(20) > EMA(50) → sweep of weekly low → Df > 0.75 → enter with trend
       No VR compression required. Catches trend continuations.
    """
    setups = []
    
    # Pre-calculate indicators
    atr_14 = atr(df, 14)
    ema_20 = ema(df['Close'], 20)
    ema_50 = ema(df['Close'], 50)
    vr = volatility_ratio(df, fast=5, slow=50)
    df_series = displacement_factor(df, 50)
    
    # Track state
    high_alert = False
    alert_start_index = 0
    pending_fvg_setups: List[dict] = []
    pending_sweeps: List[dict] = []  # Sweeps waiting for FVG formation (up to 3 bars)
    
    for i in range(52, len(df)):
        
        # ============================================================
        # Check pending FVG fills
        # ============================================================
        for pending in pending_fvg_setups[:]:
            fvg = pending['fvg']
            sweep = pending['sweep']
            bars_since = i - fvg.index
            
            if bars_since > 25:
                pending_fvg_setups.remove(pending)
                continue
            
            if fvg.direction == FVGDirection.BULLISH and df['Low'].iloc[i] <= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "crypto_compression", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
            elif fvg.direction == FVGDirection.BEARISH and df['High'].iloc[i] >= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "crypto_compression", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
        
        # ============================================================
        # Check pending sweeps for FVG formation (adjacent-bar window)
        # Sweeps persist for up to 3 bars waiting for FVG to form
        # ============================================================
        for ps in pending_sweeps[:]:
            bars_since_sweep = i - ps['index']
            if bars_since_sweep > 3:
                pending_sweeps.remove(ps)
                continue
            
            fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                             overlap_tolerance_atr=0.1, precomputed_atr=atr_14)
            if fvg:
                sweep = ps['sweep']
                if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
                   (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                    pending_fvg_setups.append({
                        'fvg': fvg,
                        'sweep': sweep,
                    })
                    pending_sweeps.remove(ps)
                    break  # Only match one pending sweep per FVG
        
        # ============================================================
        # N3: TREND MOMENTUM ENTRY (independent of VR compression)
        # When trend is clear (EMA20 > EMA50) and a weekly level sweep
        # occurs with displacement, enter with the trend.
        # ============================================================
        if not pd.isna(ema_20.iloc[i]) and not pd.isna(ema_50.iloc[i]):
            ema20_val = ema_20.iloc[i]
            ema50_val = ema_50.iloc[i]
            current_close_trend = df['Close'].iloc[i]
            atr_val_trend = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
            current_df_trend = df_series.iloc[i] if not pd.isna(df_series.iloc[i]) else 0
            
            # Only enter if clear trend and displacement
            if atr_val_trend > 0 and current_df_trend >= 0.75:
                weekly_high_t, weekly_low_t = _get_weekly_levels(df, i)
                
                # BULLISH trend momentum: EMA20 > EMA50, sweep of weekly low
                if ema20_val > ema50_val and weekly_low_t > 0:
                    sweep_t = detect_liquidity_sweep(df, i, weekly_low_t, "weekly_low")
                    if sweep_t and sweep_t.direction == SweepDirection.BULLISH:
                        entry = current_close_trend
                        sl = sweep_t.sweep_extreme - atr_val_trend * 0.5
                        tp = entry + abs(entry - sl) * 2.5
                        risk = abs(entry - sl)
                        rr = abs(tp - entry) / risk if risk > 0 else 0
                        
                        if rr >= 1.5:
                            setup = TradeSetup(
                                direction='long',
                                entry_price=entry,
                                stop_loss=sl,
                                take_profit=tp,
                                position_size=(equity * risk_pct) / (atr_val_trend * 2),
                                risk_reward=rr,
                                regime="crypto_trend",
                                sweep=sweep_t,
                                fvg=FairValueGap(FVGDirection.BULLISH, entry, entry, entry, 0, i, current_df_trend),
                                displacement_df=current_df_trend,
                                index=i
                            )
                            setups.append(setup)
                
                # BEARISH trend momentum: EMA20 < EMA50, sweep of weekly high
                elif ema20_val < ema50_val and weekly_high_t > 0:
                    sweep_t = detect_liquidity_sweep(df, i, weekly_high_t, "weekly_high")
                    if sweep_t and sweep_t.direction == SweepDirection.BEARISH:
                        entry = current_close_trend
                        sl = sweep_t.sweep_extreme + atr_val_trend * 0.5
                        tp = entry - abs(sl - entry) * 2.5
                        risk = abs(entry - sl)
                        rr = abs(tp - entry) / risk if risk > 0 else 0
                        
                        if rr >= 1.5:
                            setup = TradeSetup(
                                direction='short',
                                entry_price=entry,
                                stop_loss=sl,
                                take_profit=tp,
                                position_size=(equity * risk_pct) / (atr_val_trend * 2),
                                risk_reward=rr,
                                regime="crypto_trend",
                                sweep=sweep_t,
                                fvg=FairValueGap(FVGDirection.BEARISH, entry, entry, entry, 0, i, current_df_trend),
                                displacement_df=current_df_trend,
                                index=i
                            )
                            setups.append(setup)
        
        # ============================================================
        # COMPRESSION STRATEGY (original)
        # Step 1: Check Volatility Ratio for compression
        # O4: Require minimum compression duration to filter false signals
        # on faster timeframes (1H). VR must stay < 0.8 for min_compression_bars.
        # ============================================================
        if pd.isna(vr.iloc[i]):
            continue
        
        current_vr = vr.iloc[i]
        
        # O4: Estimate timeframe from bar density to set min compression bars
        # 1H ~ 24 bars/day, 4H ~ 6 bars/day, 1D ~ 1 bar/day
        # Require ~6 bars of compression on any timeframe
        min_compression_bars = 6
        
        if current_vr < 0.8:
            if not high_alert:
                high_alert = True
                alert_start_index = i
            # Continue monitoring in high alert
        else:
            # VR expanded -- if we were in high alert and VR just crossed above,
            # the expansion is happening NOW
            if high_alert and current_vr >= 0.8:
                high_alert = False
                # O4: Only trigger if compression lasted long enough
                compression_duration = i - alert_start_index
                if compression_duration < min_compression_bars:
                    continue  # Too short — likely noise, not real compression
                # The expansion bar is the trigger -- check it below
            elif not high_alert:
                continue  # Not compressed, skip
        
        # ============================================================
        # Step 2: Scan for liquidity sweeps
        # ============================================================
        weekly_high, weekly_low = _get_weekly_levels(df, i)
        pdh, pdl = get_previous_day_levels(df, i)
        
        sweep = None
        
        # Check weekly levels first (higher significance)
        if weekly_high > 0:
            sweep = detect_liquidity_sweep(df, i, weekly_high, "weekly_high")
        if not sweep and weekly_low > 0:
            sweep = detect_liquidity_sweep(df, i, weekly_low, "weekly_low")
        
        # Then PDH/PDL
        if not sweep and pdh > 0:
            sweep = detect_liquidity_sweep(df, i, pdh, "pdh")
        if not sweep and pdl > 0:
            sweep = detect_liquidity_sweep(df, i, pdl, "pdl")
        
        if not sweep:
            continue
        
        # ============================================================
        # Step 3: Confirm expansion candle AND minimum displacement
        # Both required -- expansion alone lets in too many false signals
        # Priority 1.5: threshold lowered 0.75→0.65
        # ============================================================
        expansion = is_expansion_candle(df, i, threshold=0.65)
        
        if not expansion:
            continue  # Must have expansion candle
        
        # Require minimum Df > 0.5 even for fallback entries
        # Priority 1.4: Full FVG path now requires Df >= 1.0 (was 1.5)
        current_df = df_series.iloc[i] if not pd.isna(df_series.iloc[i]) else 0
        if current_df < 0.5:
            continue  # Expansion candle without any displacement = noise
        
        has_strong_displacement = current_df >= 1.0
        
        # ============================================================
        # Step 4: Check for FVG (Priority 1.4: min_df 1.5→1.0)
        # ============================================================
        fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                         overlap_tolerance_atr=0.1, precomputed_atr=atr_14)
        
        if fvg:
            # Immediate match: queue FVG for fill entry
            if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
               (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                pending_fvg_setups.append({
                    'fvg': fvg,
                    'sweep': sweep,
                })
        else:
            # No FVG -- try displacement fallback first
            # Priority 1.4: fallback threshold lowered 1.0→0.75
            entered_fallback = False
            if current_df >= 0.75:
                atr_val = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
                if atr_val > 0:
                    current_close = df['Close'].iloc[i]
                    df_val = current_df
                    
                    if sweep.direction == SweepDirection.BULLISH:
                        direction = 'long'
                        entry = current_close
                        sl = sweep.sweep_extreme - atr_val * 0.5
                        tp = entry + abs(entry - sl) * 2.5
                    else:
                        direction = 'short'
                        entry = current_close
                        sl = sweep.sweep_extreme + atr_val * 0.5
                        tp = entry - abs(sl - entry) * 2.5
                    
                    risk = abs(entry - sl)
                    reward = abs(tp - entry)
                    rr = reward / risk if risk > 0 else 0
                    
                    if rr >= 1.5:
                        # EMA trend filter (Priority 1.6: widened 2%→3%)
                        skip_trade = False
                        if not pd.isna(ema_50.iloc[i]):
                            ema_dist = (current_close - ema_50.iloc[i]) / ema_50.iloc[i]
                            if direction == 'long' and ema_dist < -0.03:
                                skip_trade = True  # Don't long well below EMA
                            if direction == 'short' and ema_dist > 0.03:
                                skip_trade = True  # Don't short well above EMA
                        
                        if not skip_trade:
                            setup = TradeSetup(
                                direction=direction,
                                entry_price=entry,
                                stop_loss=sl,
                                take_profit=tp,
                                position_size=(equity * risk_pct) / (atr_val * 2) if atr_val > 0 else 0,
                                risk_reward=rr,
                                regime="crypto_compression",
                                sweep=sweep,
                                fvg=FairValueGap(
                                    FVGDirection.BULLISH if direction == 'long' else FVGDirection.BEARISH,
                                    entry, entry, entry, 0, i, df_val
                                ),
                                displacement_df=df_val,
                                index=i
                            )
                            setups.append(setup)
                            entered_fallback = True
            
            # If no displacement fallback, buffer sweep for adjacent-bar FVG window
            if not entered_fallback:
                pending_sweeps.append({
                    'sweep': sweep,
                    'index': i,
                })
    
    return setups
