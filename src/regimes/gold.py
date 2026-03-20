"""
Gold (XAUUSD) Regime for SCAF 2.0

Two modes (both run on daily data):
A. Mean Reversion Mode (Asia session on intraday, always-on for daily)
   - Bollinger Band (20, 2.5σ) extremes
   - Fade back to 20-SMA when price touches band with low volume
   - Trend filter: only mean-revert when EMA is flat

B. Momentum Drive Mode (NY overlap on intraday, always-on for daily)
   - Liquidity sweep of PDH/PDL, weekly levels, or swing levels
   - Breakout confirmed by Displacement Factor (Df > 1.0)
   - Entry at FVG midpoint after liquidity sweep

Priority 1.4: Df thresholds lowered (FVG: 1.5→1.0, fallback: 1.0→0.75)
Priority 1.6: EMA trend filter widened (1.5%→2.5%)
Priority 2.1: Weekly high/low levels added for daily data
Priority 2.2: Swing high/low detection added for daily data
Priority 2.3: Daily data runs BOTH mean reversion AND momentum modes
Priority 2.4: Near-FVG tolerance widened to 0.2 ATR for daily data
"""

import pandas as pd
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from ..indicators.technical import (
    atr, ema, sma, bollinger_bands, displacement_factor,
    detect_session, get_session_range
)
from ..execution.liquidity import (
    scan_for_sweeps, LiquiditySweep, SweepDirection,
    get_previous_day_levels, get_weekly_levels, get_swing_levels
)
from ..execution.displacement import detect_fvg, FairValueGap, FVGDirection
from ..execution.entries import validate_entry, TradeSetup


class GoldMode(Enum):
    ASIA_MEAN_REVERSION = "gold_asia_mr"
    NY_MOMENTUM = "gold_ny_momentum"
    INACTIVE = "gold_inactive"


@dataclass
class GoldMeanReversionSignal:
    """Signal from Asia session mean reversion."""
    direction: str  # 'long' or 'short'
    entry_price: float
    stop_loss: float
    take_profit: float
    index: int
    regime: str = "gold_asia_mr"


def detect_gold_mode(timestamp) -> GoldMode:
    """Determine Gold's current trading mode from timestamp."""
    session = detect_session(timestamp, 'gold')
    
    if session == 'asia':
        return GoldMode.ASIA_MEAN_REVERSION
    elif session in ('ny_overlap', 'london'):
        return GoldMode.NY_MOMENTUM
    else:
        return GoldMode.INACTIVE


def analyze_gold(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01
) -> List[TradeSetup]:
    """
    Run Gold regime analysis across all bars.
    
    Returns list of TradeSetup objects.
    
    On intraday data: Asia session → Mean Reversion, NY → Momentum (exclusive).
    On daily data: BOTH modes run on every bar (Priority 2.3).
    
    Priority 2.1: Weekly levels added for daily sweep detection.
    Priority 2.2: Swing high/low levels added for daily sweep detection.
    Priority 2.3: Daily data runs both BB mean reversion AND momentum.
    Priority 2.4: Near-FVG tolerance widened to 0.2 ATR on daily data.
    """
    setups = []
    
    # Pre-calculate indicators
    atr_14 = atr(df, 14)
    sma_20 = sma(df['Close'], 20)
    ema_50 = ema(df['Close'], 50)
    bb_upper, bb_middle, bb_lower = bollinger_bands(df['Close'], 20, 2.5)
    df_series = displacement_factor(df, 50)
    
    # Detect if this is daily data (no intraday timestamps)
    is_daily = False
    try:
        hours = [df.index[i].hour for i in range(min(20, len(df)))]
        if len(set(hours)) <= 2:
            is_daily = True
    except AttributeError:
        is_daily = True
    
    # Priority 2.4: Wider near-FVG tolerance for daily candles
    fvg_overlap_tolerance = 0.2 if is_daily else 0.1
    
    # Weekly lookback: 7 bars on daily, 40 bars on 4H
    weekly_lookback = 7 if is_daily else 40
    
    # N4: Detect fast timeframe (1H) for momentum confirmation bar
    # 4H has ~6 unique hours in 30 bars, 1H has ~24. Threshold at 12.
    is_fast_tf = False
    if not is_daily:
        try:
            sample_hours = [df.index[j].hour for j in range(min(30, len(df)))]
            is_fast_tf = len(set(sample_hours)) >= 12  # Only 1H and faster
        except (AttributeError, IndexError):
            pass
    
    # Track active FVGs for momentum mode
    pending_fvg_setups: List[dict] = []
    pending_sweeps: List[dict] = []
    # N4: Sweeps awaiting confirmation bar on fast TFs
    pending_confirmation: List[dict] = []
    
    for i in range(52, len(df)):
        # Determine mode(s) to run
        if is_daily:
            # Priority 2.3: daily runs BOTH modes
            run_mean_reversion = True
            run_momentum = True
        else:
            try:
                mode = detect_gold_mode(df.index[i])
            except AttributeError:
                mode = GoldMode.NY_MOMENTUM
            run_mean_reversion = (mode == GoldMode.ASIA_MEAN_REVERSION)
            run_momentum = (mode == GoldMode.NY_MOMENTUM)
        
        # ============================================================
        # Check pending FVG fills (price returning to FVG midpoint)
        # ============================================================
        for pending in pending_fvg_setups[:]:
            fvg = pending['fvg']
            sweep = pending['sweep']
            bars_since = i - fvg.index
            
            if bars_since > 30:
                pending_fvg_setups.remove(pending)
                continue
            
            if fvg.direction == FVGDirection.BULLISH and df['Low'].iloc[i] <= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "gold_ny_momentum", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
            elif fvg.direction == FVGDirection.BEARISH and df['High'].iloc[i] >= fvg.midpoint:
                setup = validate_entry(sweep, fvg, df, i, "gold_ny_momentum", equity, risk_pct)
                if setup:
                    setups.append(setup)
                pending_fvg_setups.remove(pending)
        
        # ============================================================
        # Check pending sweeps for FVG formation (adjacent-bar window)
        # ============================================================
        for ps in pending_sweeps[:]:
            bars_since_sweep = i - ps['index']
            if bars_since_sweep > 3:
                pending_sweeps.remove(ps)
                continue
            
            fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                             overlap_tolerance_atr=fvg_overlap_tolerance,
                             precomputed_atr=atr_14)
            if fvg:
                for sweep in ps['sweeps']:
                    if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
                       (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                        pending_fvg_setups.append({
                            'fvg': fvg,
                            'sweep': sweep,
                        })
                        pending_sweeps.remove(ps)
                        break
                else:
                    continue
                break
        
        # ============================================================
        # MEAN REVERSION MODE (Asia session on intraday, always on daily)
        # ============================================================
        if run_mean_reversion:
            if not (pd.isna(bb_upper.iloc[i]) or pd.isna(sma_20.iloc[i]) or pd.isna(ema_50.iloc[i])):
                current_close = df['Close'].iloc[i]
                current_high = df['High'].iloc[i]
                current_low = df['Low'].iloc[i]
                
                # EMA slope trend filter: skip MR when trending strongly
                skip_mr = False
                if i > 20:
                    ema_slope = (ema_50.iloc[i] - ema_50.iloc[i-20]) / ema_50.iloc[i-20]
                    # Daily data: relax slope filter (daily trends are noisier)
                    slope_threshold = 0.03 if is_daily else 0.02
                    if abs(ema_slope) > slope_threshold:
                        skip_mr = True
                
                if not skip_mr:
                    ema_distance = (current_close - ema_50.iloc[i]) / ema_50.iloc[i]
                    atr_val = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
                    
                    if atr_val > 0:
                        # O2: Wider SL (1.0 ATR instead of 0.5) + improved TP
                        # Old SL was too tight — Gold pushes through BB by $20-30 before reversing
                        # TP uses opposite BB for better reward capture
                        
                        # Bollinger Band touch + fade (SHORT at upper band)
                        if current_high >= bb_upper.iloc[i] and current_close < bb_upper.iloc[i]:
                            if ema_distance <= 0.025:  # Don't short into strong uptrend
                                entry = current_close
                                sl = bb_upper.iloc[i] + atr_val * 1.0  # O2: widened 0.5→1.0 ATR
                                # O2: TP at SMA(20) but with a minimum reward of 1.5x the BB band width
                                tp_sma = sma_20.iloc[i]
                                tp_band = bb_lower.iloc[i]  # Opposite BB as extended target
                                # Use SMA target but ensure minimum 1.5R
                                risk = abs(entry - sl)
                                tp = tp_sma
                                if abs(tp_sma - entry) < risk * 1.2:
                                    # SMA too close — use midpoint between SMA and opposite BB
                                    tp = (tp_sma + tp_band) / 2
                                
                                reward = abs(tp - entry)
                                rr = reward / risk if risk > 0 else 0
                                
                                if rr >= 1.2:  # O2: lowered from 1.5 (wider SL needs lower min RR)
                                    regime_label = "gold_daily_mr" if is_daily else "gold_asia_mr"
                                    setup = TradeSetup(
                                        direction='short',
                                        entry_price=entry,
                                        stop_loss=sl,
                                        take_profit=tp,
                                        position_size=(equity * risk_pct) / (atr_val * 2),
                                        risk_reward=rr,
                                        regime=regime_label,
                                        sweep=LiquiditySweep(SweepDirection.BEARISH, bb_upper.iloc[i], current_high, current_close, i, "bb_upper"),
                                        fvg=FairValueGap(FVGDirection.BEARISH, entry, entry, entry, 0, i, 0),
                                        displacement_df=0,
                                        index=i
                                    )
                                    setups.append(setup)
                        
                        # Bollinger Band touch + fade (LONG at lower band)
                        elif current_low <= bb_lower.iloc[i] and current_close > bb_lower.iloc[i]:
                            if ema_distance >= -0.025:  # Don't long into strong downtrend
                                entry = current_close
                                sl = bb_lower.iloc[i] - atr_val * 1.0  # O2: widened 0.5→1.0 ATR
                                tp_sma = sma_20.iloc[i]
                                tp_band = bb_upper.iloc[i]
                                risk = abs(entry - sl)
                                tp = tp_sma
                                if abs(tp_sma - entry) < risk * 1.2:
                                    tp = (tp_sma + tp_band) / 2
                                
                                reward = abs(tp - entry)
                                rr = reward / risk if risk > 0 else 0
                                
                                if rr >= 1.2:  # O2: lowered from 1.5 (wider SL needs lower min RR)
                                    regime_label = "gold_daily_mr" if is_daily else "gold_asia_mr"
                                    setup = TradeSetup(
                                        direction='long',
                                        entry_price=entry,
                                        stop_loss=sl,
                                        take_profit=tp,
                                        position_size=(equity * risk_pct) / (atr_val * 2),
                                        risk_reward=rr,
                                        regime=regime_label,
                                        sweep=LiquiditySweep(SweepDirection.BULLISH, bb_lower.iloc[i], current_low, current_close, i, "bb_lower"),
                                        fvg=FairValueGap(FVGDirection.BULLISH, entry, entry, entry, 0, i, 0),
                                        displacement_df=0,
                                        index=i
                                    )
                                    setups.append(setup)
        
        # ============================================================
        # MOMENTUM MODE (NY session on intraday, always on daily)
        # ============================================================
        if run_momentum:
            # N4: Process pending confirmation bars (fast TF only)
            # Sweeps from the previous bar are confirmed if this bar
            # closes in the expected direction
            for pc in pending_confirmation[:]:
                bars_since_conf = i - pc['index']
                if bars_since_conf > 1:
                    pending_confirmation.remove(pc)
                    continue
                if bars_since_conf == 1:
                    confirmed = False
                    current_close_conf = df['Close'].iloc[i]
                    prev_close_conf = df['Close'].iloc[i - 1]
                    for sweep in pc['sweeps']:
                        if sweep.direction == SweepDirection.BULLISH and current_close_conf > prev_close_conf:
                            confirmed = True
                        elif sweep.direction == SweepDirection.BEARISH and current_close_conf < prev_close_conf:
                            confirmed = True
                    
                    if confirmed:
                        # Process confirmed sweeps through normal FVG/fallback path
                        conf_fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                                              overlap_tolerance_atr=fvg_overlap_tolerance,
                                              precomputed_atr=atr_14)
                        if conf_fvg:
                            for sweep in pc['sweeps']:
                                if (sweep.direction == SweepDirection.BULLISH and conf_fvg.direction == FVGDirection.BULLISH) or \
                                   (sweep.direction == SweepDirection.BEARISH and conf_fvg.direction == FVGDirection.BEARISH):
                                    pending_fvg_setups.append({'fvg': conf_fvg, 'sweep': sweep})
                                    break
                        else:
                            # Displacement fallback for confirmed sweep
                            conf_df_val = df_series.iloc[i] if not pd.isna(df_series.iloc[i]) else 0
                            if conf_df_val >= 0.75:
                                conf_atr = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
                                if conf_atr > 0:
                                    best_sweep = pc['sweeps'][0]
                                    cc = df['Close'].iloc[i]
                                    if best_sweep.direction == SweepDirection.BULLISH:
                                        direction = 'long'
                                        entry = cc
                                        sl = best_sweep.sweep_extreme - conf_atr * 0.5
                                        tp = entry + abs(entry - sl) * 2.5
                                    else:
                                        direction = 'short'
                                        entry = cc
                                        sl = best_sweep.sweep_extreme + conf_atr * 0.5
                                        tp = entry - abs(sl - entry) * 2.5
                                    risk = abs(entry - sl)
                                    rr = abs(tp - entry) / risk if risk > 0 else 0
                                    if rr >= 1.5:
                                        skip = False
                                        if not pd.isna(ema_50.iloc[i]):
                                            ed = (cc - ema_50.iloc[i]) / ema_50.iloc[i]
                                            if direction == 'long' and ed < -0.025:
                                                skip = True
                                            if direction == 'short' and ed > 0.025:
                                                skip = True
                                        if not skip:
                                            rl = "gold_daily_momentum" if is_daily else "gold_ny_momentum"
                                            setup = TradeSetup(
                                                direction=direction, entry_price=entry,
                                                stop_loss=sl, take_profit=tp,
                                                position_size=(equity * risk_pct) / (conf_atr * 2),
                                                risk_reward=rr, regime=rl, sweep=best_sweep,
                                                fvg=FairValueGap(
                                                    FVGDirection.BULLISH if direction == 'long' else FVGDirection.BEARISH,
                                                    entry, entry, entry, 0, i, conf_df_val),
                                                displacement_df=conf_df_val, index=i)
                                            setups.append(setup)
                    pending_confirmation.remove(pc)
            
            # Step 1: Gather all liquidity levels
            session_high, session_low = 0, 0
            if not is_daily:
                try:
                    session_high, session_low = get_session_range(df, i, 'london')
                except Exception:
                    pass
            
            # Priority 2.1: Weekly levels (crucial for daily data)
            wk_high, wk_low = get_weekly_levels(df, i, lookback_bars=weekly_lookback)
            
            # Priority 2.2: Swing levels (natural stop-loss clusters)
            sw_high, sw_low = get_swing_levels(df, i, lookback=20, swing_window=3)
            
            # Scan all levels for sweeps
            sweeps = scan_for_sweeps(
                df, i,
                session_high=session_high, session_low=session_low,
                weekly_high=wk_high, weekly_low=wk_low,
                swing_high=sw_high, swing_low=sw_low
            )
            
            if not sweeps:
                continue  # Nothing to do on this bar
            
            # N4: On fast TFs (1H), buffer sweeps for confirmation bar
            if is_fast_tf:
                pending_confirmation.append({
                    'sweeps': sweeps,
                    'index': i,
                })
                continue  # Don't process immediately, wait for confirmation
            
            # Step 2: Check for FVG (Priority 2.4: wider tolerance for daily)
            fvg = detect_fvg(df, i, min_df=1.0, precomputed_df=df_series,
                             overlap_tolerance_atr=fvg_overlap_tolerance,
                             precomputed_atr=atr_14)
            
            if fvg:
                for sweep in sweeps:
                    if (sweep.direction == SweepDirection.BULLISH and fvg.direction == FVGDirection.BULLISH) or \
                       (sweep.direction == SweepDirection.BEARISH and fvg.direction == FVGDirection.BEARISH):
                        pending_fvg_setups.append({
                            'fvg': fvg,
                            'sweep': sweep,
                        })
                        break
            else:
                # Displacement fallback: enter on close when Df >= 0.75
                entered_fallback = False
                current_df_val = df_series.iloc[i] if not pd.isna(df_series.iloc[i]) else 0
                
                if current_df_val >= 0.75:
                    atr_val = atr_14.iloc[i] if not pd.isna(atr_14.iloc[i]) else 0
                    if atr_val > 0:
                        current_close = df['Close'].iloc[i]
                        best_sweep = sweeps[0]
                        
                        if best_sweep.direction == SweepDirection.BULLISH:
                            direction = 'long'
                            entry = current_close
                            sl = best_sweep.sweep_extreme - atr_val * 0.5
                            tp = entry + abs(entry - sl) * 2.5
                        else:
                            direction = 'short'
                            entry = current_close
                            sl = best_sweep.sweep_extreme + atr_val * 0.5
                            tp = entry - abs(sl - entry) * 2.5
                        
                        risk = abs(entry - sl)
                        reward = abs(tp - entry)
                        rr = reward / risk if risk > 0 else 0
                        
                        if rr >= 1.5:
                            skip_trade = False
                            if not pd.isna(ema_50.iloc[i]):
                                ema_dist = (current_close - ema_50.iloc[i]) / ema_50.iloc[i]
                                if direction == 'long' and ema_dist < -0.025:
                                    skip_trade = True
                                if direction == 'short' and ema_dist > 0.025:
                                    skip_trade = True
                            
                            if not skip_trade:
                                regime_label = "gold_daily_momentum" if is_daily else "gold_ny_momentum"
                                setup = TradeSetup(
                                    direction=direction,
                                    entry_price=entry,
                                    stop_loss=sl,
                                    take_profit=tp,
                                    position_size=(equity * risk_pct) / (atr_val * 2),
                                    risk_reward=rr,
                                    regime=regime_label,
                                    sweep=best_sweep,
                                    fvg=FairValueGap(
                                        FVGDirection.BULLISH if direction == 'long' else FVGDirection.BEARISH,
                                        entry, entry, entry, 0, i, current_df_val
                                    ),
                                    displacement_df=current_df_val,
                                    index=i
                                )
                                setups.append(setup)
                                entered_fallback = True
                
                if not entered_fallback:
                    pending_sweeps.append({
                        'sweeps': sweeps,
                        'index': i,
                    })
    
    return setups
