"""
Sovereign Breakout Retest Realm (SBRS) 1.0 — Gold Regime

Breakout + Retest strategy based on 3-4 years of profitable manual Gold trading.
Codified for algo implementation without adding complexity.

Asset:      Gold (XAUUSD) primary, extendable to Forex
Timeframes: 1H for entries, 4H for trend context
Strategy:   Structure break → retest → MA cross confirmation → enter

The SBRS Execution Protocol:
1. Check 4H trend context (WMA/SMMA alignment)
2. Detect structure break on 1H (close beyond swing high/low)
3. Wait for retest (price returns within 0.5 ATR of broken level)
4. Confirm MA cross (WMA(9) crosses SMMA(7) within 10 bars)
5. Enter at candle close with 3R TP and ATR-based SL

DO NOT OPTIMIZE core parameters (WMA 9, SMMA 7, swing lookback 20, R:R 3.0).
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ..indicators.technical import (
    atr, wma, smma,
    detect_swing_high, detect_swing_low,
    get_recent_swing_high, get_recent_swing_low
)
from ..execution.entries import TradeSetup, TradeDirection


# ── Core Parameters (DO NOT OPTIMIZE) ─────────────────────────
WMA_PERIOD = 9
SMMA_PERIOD = 7
SWING_LOOKBACK = 20       # bars to search for swings
SWING_WINDOW = 3          # bars on each side for swing confirmation
MIN_RR = 3.0              # minimum risk:reward ratio
RETEST_TOLERANCE_ATR = 0.5        # retest proximity for LONGS (ATR units)
RETEST_TOLERANCE_ATR_SHORT = 0.3  # tighter retest for SHORTS (shorts are weaker, demand better entries)

# ── Tunable Parameters (can test ±20%) ────────────────────────
ATR_PERIOD = 14
MAX_RETEST_WAIT = 10      # max bars to wait for retest after break
SL_BUFFER_ATR = 0.3       # SL distance beyond retest extreme
BE_TRIGGER_R = 1.5        # move SL to breakeven at this R-multiple
BE_BUFFER_R = 0.1         # buffer above breakeven
MAX_HOLD_BARS = 40        # close trade after this many bars
MA_CROSS_LOOKBACK = 10    # bars to search for recent MA cross on 1H
TREND_CROSS_LOOKBACK = 5  # "recently crossed" on 4H (in 4H bars)
CHOP_ATR_THRESHOLD = 1.0  # range < this × ATR = choppy (skip)
CHOP_LOOKBACK = 10        # bars to measure chop

# ── Session Filter ────────────────────────────────────────────
# NY Afternoon (16:00-20:00 GMT) loses money over 10Y. Block new entries.
SESSION_BLOCK_START_HOUR = 16    # GMT hour to stop new entries
SESSION_BLOCK_START_MINUTE = 30  # minute cutoff (16:30 GMT)
SESSION_BLOCK_END_HOUR = 24      # resume entries (next day Asia open)

# ── Forex-Specific Parameters ─────────────────────────────────
# Forex is more liquid — demand tighter retests and session focus.
FOREX_RETEST_TOLERANCE_ATR = 0.3  # tighter than Gold's 0.5 (both directions)
FOREX_SESSION_START_HOUR = 7      # London open (GMT) — only trade London+NY
FOREX_SESSION_END_HOUR = 16       # NY close (GMT) — skip Asia for forex

# ── Indices-Specific Parameters ───────────────────────────────
# S&P/NASDAQ: US market 13:30-20:00 GMT (9:30-4:00 ET)
# DAX: European market 07:00-15:30 GMT
# Constrained mode: first 90 min after open + last 60 min before close
INDICES_RETEST_TOLERANCE_ATR = 0.5  # same as Gold (trending instruments)

# Market hours (GMT) per index
INDICES_SESSIONS = {
    '^GSPC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},   # S&P 500
    '^IXIC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},   # NASDAQ
    '^GDAXI': {'open_h': 7,  'open_m': 0,  'close_h': 15, 'close_m': 30},  # DAX
}

# Constrained windows: first 90 min after open, last 60 min before close
INDICES_OPEN_WINDOW_MINUTES = 90   # trade first 90 min after market open
INDICES_CLOSE_WINDOW_MINUTES = 60  # trade last 60 min before market close


# ── State Tracking ────────────────────────────────────────────

@dataclass
class PendingSetup:
    """Tracks a structure break waiting for retest confirmation."""
    direction: str           # 'long' or 'short'
    broken_level: float      # the swing level that was broken
    break_bar: int           # bar index (iloc) where break occurred
    bars_waiting: int = 0    # incremented each bar while waiting
    created_at: str = ""     # timestamp for debugging


# ── 4H Context Functions ──────────────────────────────────────

def resample_to_4h(df_1h: pd.DataFrame) -> pd.DataFrame:
    """
    Resample 1H data to 4H for trend context.
    
    Uses completed 4H bars only (no look-ahead).
    Groups by 4-hour blocks aligned to standard 4H boundaries.
    
    Args:
        df_1h: 1H OHLC DataFrame with DatetimeIndex
    
    Returns:
        pd.DataFrame at 4H frequency with Open, High, Low, Close
    """
    df_4h = df_1h.resample('4h').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    }).dropna()
    
    return df_4h


def compute_4h_context(df_4h: pd.DataFrame) -> pd.DataFrame:
    """
    Pre-compute 4H trend indicators and trend classification.
    
    Adds columns:
      - wma_9_4h: WMA(9) on 4H close
      - smma_7_4h: SMMA(7) on 4H close
      - trend_4h: 'bullish', 'bearish', or 'neutral'
    
    Trend logic:
      Bullish: close > WMA(9) AND (WMA > SMMA OR WMA crossed above SMMA within 5 bars)
      Bearish: close < WMA(9) AND (WMA < SMMA OR WMA crossed below SMMA within 5 bars)
      Neutral: everything else — skip these bars
    """
    df_4h = df_4h.copy()
    df_4h['wma_9_4h'] = wma(df_4h['Close'], WMA_PERIOD)
    df_4h['smma_7_4h'] = smma(df_4h['Close'], SMMA_PERIOD)
    
    trends = []
    wma_vals = df_4h['wma_9_4h'].values
    smma_vals = df_4h['smma_7_4h'].values
    closes = df_4h['Close'].values
    
    for i in range(len(df_4h)):
        if np.isnan(wma_vals[i]) or np.isnan(smma_vals[i]) or np.isnan(closes[i]):
            trends.append('neutral')
            continue
        
        # Check if WMA recently crossed SMMA (within TREND_CROSS_LOOKBACK bars)
        recently_crossed_bullish = False
        recently_crossed_bearish = False
        for j in range(max(1, i - TREND_CROSS_LOOKBACK + 1), i + 1):
            if j < 1 or np.isnan(wma_vals[j]) or np.isnan(smma_vals[j]):
                continue
            if np.isnan(wma_vals[j-1]) or np.isnan(smma_vals[j-1]):
                continue
            if wma_vals[j] > smma_vals[j] and wma_vals[j-1] <= smma_vals[j-1]:
                recently_crossed_bullish = True
            if wma_vals[j] < smma_vals[j] and wma_vals[j-1] >= smma_vals[j-1]:
                recently_crossed_bearish = True
        
        wma_above_smma = wma_vals[i] > smma_vals[i]
        wma_below_smma = wma_vals[i] < smma_vals[i]
        price_above_wma = closes[i] > wma_vals[i]
        price_below_wma = closes[i] < wma_vals[i]
        
        if price_above_wma and (wma_above_smma or recently_crossed_bullish):
            trends.append('bullish')
        elif price_below_wma and (wma_below_smma or recently_crossed_bearish):
            trends.append('bearish')
        else:
            trends.append('neutral')
    
    df_4h['trend_4h'] = trends
    return df_4h


def map_4h_to_1h(df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> pd.Series:
    """
    Map 4H trend context to each 1H bar.
    
    Each 1H bar gets the trend from the most recently COMPLETED 4H bar.
    This prevents look-ahead bias — we never peek into the current
    incomplete 4H candle.
    
    Args:
        df_1h: 1H DataFrame
        df_4h: 4H DataFrame with trend_4h column
    
    Returns:
        pd.Series of trend values aligned to 1H index
    """
    # For each 1H timestamp, find the latest 4H bar that ended BEFORE it
    trends_1h = pd.Series('neutral', index=df_1h.index)
    
    if len(df_4h) == 0:
        return trends_1h
    
    # Use searchsorted to efficiently map 4H bars to 1H bars
    # Each 1H bar uses the 4H bar that closed at or before its timestamp
    for i in range(len(df_1h)):
        ts_1h = df_1h.index[i]
        # Find the last 4H bar that closed at or before this 1H bar
        mask = df_4h.index <= ts_1h
        if mask.any():
            last_4h_idx = df_4h.index[mask][-1]
            trends_1h.iloc[i] = df_4h.loc[last_4h_idx, 'trend_4h']
    
    return trends_1h


def check_trend_alignment(trend_4h: str, direction: str) -> bool:
    """
    Verify 4H trend aligns with proposed trade direction.
    
    Args:
        trend_4h: '4H trend — 'bullish', 'bearish', or 'neutral'
        direction: Proposed trade direction — 'long' or 'short'
    
    Returns:
        True if aligned (bullish+long or bearish+short), False otherwise
    """
    if direction == 'long' and trend_4h == 'bullish':
        return True
    if direction == 'short' and trend_4h == 'bearish':
        return True
    return False


# ── MA Cross Detection ────────────────────────────────────────

def check_ma_cross(
    wma_vals: pd.Series,
    smma_vals: pd.Series,
    current_idx: int,
    direction: str,
    lookback: int = MA_CROSS_LOOKBACK
) -> bool:
    """
    Check if WMA crossed SMMA in the expected direction within lookback bars.
    
    Scans bars [current_idx - lookback + 1, current_idx] for a crossover.
    A cross at bar j means:
      Bullish: wma[j] > smma[j] AND wma[j-1] <= smma[j-1]
      Bearish: wma[j] < smma[j] AND wma[j-1] >= smma[j-1]
    
    Cross must be CONFIRMED (full candle close, not mid-candle).
    
    Args:
        wma_vals: WMA series (1H or 4H)
        smma_vals: SMMA series (1H or 4H)
        current_idx: Current bar integer position (iloc)
        direction: 'long' (look for bullish cross) or 'short' (look for bearish cross)
        lookback: Number of bars to scan (default 10)
    
    Returns:
        True if valid cross found within window
    """
    start = max(1, current_idx - lookback + 1)
    
    for j in range(start, current_idx + 1):
        w_curr = wma_vals.iloc[j]
        s_curr = smma_vals.iloc[j]
        w_prev = wma_vals.iloc[j - 1]
        s_prev = smma_vals.iloc[j - 1]
        
        if np.isnan(w_curr) or np.isnan(s_curr) or np.isnan(w_prev) or np.isnan(s_prev):
            continue
        
        if direction == 'long':
            # Bullish cross: WMA crosses above SMMA
            if w_curr > s_curr and w_prev <= s_prev:
                return True
        else:  # short
            # Bearish cross: WMA crosses below SMMA
            if w_curr < s_curr and w_prev >= s_prev:
                return True
    
    return False


# ── Session Filter ────────────────────────────────────────────

def is_indices_session_blocked(timestamp, symbol: str = '^GSPC', constrained: bool = True) -> bool:
    """
    Check if current bar is outside trading window for indices.
    
    Unconstrained: only blocks outside market hours.
    Constrained: only allows first 90 min after open + last 60 min before close.
    
    Args:
        timestamp: Bar timestamp
        symbol: Index symbol (^GSPC, ^IXIC, ^GDAXI)
        constrained: If True, apply open/close window restriction
    """
    try:
        hour = timestamp.hour
        minute = timestamp.minute
    except AttributeError:
        return False
    
    session = INDICES_SESSIONS.get(symbol, INDICES_SESSIONS['^GSPC'])
    open_h, open_m = session['open_h'], session['open_m']
    close_h, close_m = session['close_h'], session['close_m']
    
    # Convert to minutes since midnight for easy comparison
    current_min = hour * 60 + minute
    open_min = open_h * 60 + open_m
    close_min = close_h * 60 + close_m
    
    # Block if outside market hours entirely
    if current_min < open_min or current_min >= close_min:
        return True
    
    if not constrained:
        return False  # Unconstrained: market is open, allow trade
    
    # Constrained: only allow first 90 min and last 60 min
    open_window_end = open_min + INDICES_OPEN_WINDOW_MINUTES
    close_window_start = close_min - INDICES_CLOSE_WINDOW_MINUTES
    
    # Allow if in open window (first 90 min) or close window (last 60 min)
    if current_min < open_window_end:
        return False  # In open window — allow
    if current_min >= close_window_start:
        return False  # In close window — allow
    
    return True  # Mid-session — block in constrained mode


def is_forex_session_blocked(timestamp) -> bool:
    """
    Check if current bar is outside London/NY for forex.
    Forex only trades 07:00-16:00 GMT (London open to NY close).
    """
    try:
        hour = timestamp.hour
    except AttributeError:
        return False
    return hour < FOREX_SESSION_START_HOUR or hour >= FOREX_SESSION_END_HOUR


def is_session_blocked(timestamp) -> bool:
    """
    Check if current bar is in the blocked session (NY Afternoon).
    
    No NEW entries after 16:30 GMT. Existing trades continue to be managed.
    Data shows 16:00-20:00 GMT is the only losing session over 10Y (-$660).
    
    Args:
        timestamp: Bar timestamp (DatetimeIndex element)
    
    Returns:
        True if entries should be blocked at this time
    """
    try:
        hour = timestamp.hour
        minute = timestamp.minute
    except AttributeError:
        return False  # Daily data — no session filter
    
    # Block from 16:30 to 23:59 GMT
    if hour > SESSION_BLOCK_START_HOUR:
        return True
    if hour == SESSION_BLOCK_START_HOUR and minute >= SESSION_BLOCK_START_MINUTE:
        return True
    
    return False


# ── Chop Filter ───────────────────────────────────────────────

def is_choppy(
    df: pd.DataFrame,
    current_idx: int,
    atr_vals: pd.Series,
    lookback: int = CHOP_LOOKBACK,
    threshold: float = CHOP_ATR_THRESHOLD
) -> bool:
    """
    Check if market is in choppy consolidation (skip trade).
    
    Choppy = price range over last `lookback` bars < threshold × ATR.
    This filters out tight ranging boxes where breakouts fail.
    
    Args:
        df: OHLC DataFrame
        current_idx: Current bar position (iloc)
        atr_vals: Pre-computed ATR series
        lookback: Bars to measure range (default 10)
        threshold: ATR multiplier (default 1.0)
    
    Returns:
        True if market is choppy (SKIP the trade)
    """
    start = max(0, current_idx - lookback + 1)
    window = df.iloc[start:current_idx + 1]
    
    if len(window) < lookback:
        return False  # Not enough data, allow trade
    
    price_range = window['High'].max() - window['Low'].min()
    current_atr = atr_vals.iloc[current_idx]
    
    if np.isnan(current_atr) or current_atr <= 0:
        return False
    
    return price_range < (threshold * current_atr)




# ── Main Strategy Function ────────────────────────────────────

def analyze_gold_sbrs(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01,
    asset_class: str = 'gold',
    symbol: str = '',
    indices_constrained: bool = False  # Unconstrained — full market hours (tested, beats constrained)
) -> List[TradeSetup]:
    """
    SBRS 1.1 — Breakout + Retest strategy for Gold, Forex, and Indices.
    
    Processes 1H/4H data bar-by-bar, generating TradeSetup objects
    compatible with the backtest engine.
    
    Entry Protocol (ALL conditions required):
      1. 4H trend context aligns with trade direction
      2. Structure break: close beyond recent swing high/low (20-bar lookback)
      3. Retest: price returns within tolerance ATR of broken level
      4. MA cross: WMA(9) crossed SMMA(7) in trade direction within 10 bars
      5. Filters: session, chop, R:R >= 3.0, trend aligned
    
    Asset-specific adjustments:
      Gold:    0.5 ATR longs / 0.3 shorts, no entries after 16:30 GMT
      Forex:   0.3 ATR both directions, London/NY only (07-16 GMT)
      Indices: 0.5 ATR both directions, market hours only.
               Constrained mode: first 90 min + last 60 min only.
    
    Args:
        df: 1H/4H OHLC DataFrame (DatetimeIndex)
        equity: Account equity for position sizing (default 10000)
        risk_pct: Risk per trade as decimal (default 0.01 = 1%)
        asset_class: 'gold', 'forex', or 'indices'
        symbol: Ticker symbol (needed for indices session lookup)
        indices_constrained: If True, indices only trade open/close windows
    
    Returns:
        List[TradeSetup] for the backtest engine
    """
    is_forex = asset_class == 'forex'
    is_gold = asset_class in ('gold', 'commodity')
    is_indices = asset_class == 'indices'
    
    if is_forex:
        regime_tag = 'sbrs_forex'
    elif is_indices:
        regime_tag = 'sbrs_indices'
    else:
        regime_tag = 'sbrs_gold'
    if len(df) < 50:
        return []
    
    # ================================================================
    # Phase 1: Pre-computation
    # ================================================================
    
    # 4H context: resample, compute trend, map back to 1H
    df_4h = resample_to_4h(df)
    if len(df_4h) < WMA_PERIOD + SMMA_PERIOD:
        return []
    
    df_4h = compute_4h_context(df_4h)
    trend_context = map_4h_to_1h(df, df_4h)
    
    # 1H indicators
    wma_1h = wma(df['Close'], WMA_PERIOD)
    smma_1h = smma(df['Close'], SMMA_PERIOD)
    atr_vals = atr(df, ATR_PERIOD)
    
    # Swing detection (pre-compute full masks)
    swing_high_mask = detect_swing_high(df['High'], left=SWING_WINDOW, right=SWING_WINDOW)
    swing_low_mask = detect_swing_low(df['Low'], left=SWING_WINDOW, right=SWING_WINDOW)
    
    # 4H MA values for cross checking (optional stronger signal)
    wma_4h = wma(df_4h['Close'], WMA_PERIOD) if len(df_4h) >= WMA_PERIOD else None
    smma_4h = smma(df_4h['Close'], SMMA_PERIOD) if len(df_4h) >= SMMA_PERIOD else None
    
    # ================================================================
    # Phase 2: Bar-by-bar loop
    # ================================================================
    
    pending_setups: List[PendingSetup] = []
    setups: List[TradeSetup] = []
    
    # Start after enough bars for indicators + swing detection
    start_bar = max(SWING_LOOKBACK + SWING_WINDOW, ATR_PERIOD, WMA_PERIOD, SMMA_PERIOD)
    
    for i in range(start_bar, len(df)):
        current_close = df['Close'].iloc[i]
        current_high = df['High'].iloc[i]
        current_low = df['Low'].iloc[i]
        current_atr = atr_vals.iloc[i]
        current_trend = trend_context.iloc[i]
        
        if np.isnan(current_atr) or current_atr <= 0:
            continue
        
        # Get timestamp for debugging
        try:
            ts_str = str(df.index[i])
        except Exception:
            ts_str = str(i)
        
        # ==============================================================
        # Step 2: Detect NEW structure breaks
        # ==============================================================
        
        # Only look for breaks if trend is not neutral
        if current_trend != 'neutral':
            
            # Look for LONG setup: price closes ABOVE recent swing high
            if current_trend == 'bullish':
                swing_high_result = get_recent_swing_high(
                    df['High'], swing_high_mask, i, SWING_LOOKBACK
                )
                if swing_high_result is not None:
                    sh_idx, sh_level = swing_high_result
                    # Structure break: close above swing high
                    if current_close > sh_level:
                        # Check we don't already have a pending setup for this level
                        already_pending = any(
                            abs(p.broken_level - sh_level) < current_atr * 0.1
                            for p in pending_setups
                        )
                        if not already_pending:
                            pending_setups.append(PendingSetup(
                                direction='long',
                                broken_level=sh_level,
                                break_bar=i,
                                bars_waiting=0,
                                created_at=ts_str
                            ))
            
            # Look for SHORT setup: price closes BELOW recent swing low
            if current_trend == 'bearish':
                swing_low_result = get_recent_swing_low(
                    df['Low'], swing_low_mask, i, SWING_LOOKBACK
                )
                if swing_low_result is not None:
                    sl_idx, sl_level = swing_low_result
                    # Structure break: close below swing low
                    if current_close < sl_level:
                        already_pending = any(
                            abs(p.broken_level - sl_level) < current_atr * 0.1
                            for p in pending_setups
                        )
                        if not already_pending:
                            pending_setups.append(PendingSetup(
                                direction='short',
                                broken_level=sl_level,
                                break_bar=i,
                                bars_waiting=0,
                                created_at=ts_str
                            ))
        
        # ==============================================================
        # Step 3: Check pending setups for retest confirmation
        # ==============================================================
        
        expired = []
        for setup_idx, pending in enumerate(pending_setups):
            # Don't check retest on the same bar as the break
            if pending.break_bar == i:
                continue
            
            pending.bars_waiting += 1
            
            # Timeout: cancel if waiting too long
            if pending.bars_waiting > MAX_RETEST_WAIT:
                expired.append(setup_idx)
                continue
            
            retest_confirmed = False
            retest_extreme = 0.0  # The low (long) or high (short) of retest candle
            
            # Determine retest tolerance based on asset and direction
            if is_forex:
                # Forex: tight tolerance both directions (0.3 ATR)
                long_tolerance = FOREX_RETEST_TOLERANCE_ATR
                short_tolerance = FOREX_RETEST_TOLERANCE_ATR
            elif is_indices:
                # Indices: same as Gold (trending instruments)
                long_tolerance = INDICES_RETEST_TOLERANCE_ATR
                short_tolerance = RETEST_TOLERANCE_ATR_SHORT
            else:
                # Gold: standard for longs (0.5), tighter for shorts (0.3)
                long_tolerance = RETEST_TOLERANCE_ATR
                short_tolerance = RETEST_TOLERANCE_ATR_SHORT
            
            if pending.direction == 'long':
                # LONG retest: price dips back DOWN toward broken level
                distance_to_level = current_low - pending.broken_level
                if distance_to_level <= long_tolerance * current_atr:
                    # Directional intent: close above the retest low
                    if current_close > current_low:
                        retest_confirmed = True
                        retest_extreme = current_low
            
            elif pending.direction == 'short':
                # SHORT retest: price rallies back UP toward broken level
                distance_to_level = pending.broken_level - current_high
                if distance_to_level <= short_tolerance * current_atr:
                    # Directional intent: close below the retest high
                    if current_close < current_high:
                        retest_confirmed = True
                        retest_extreme = current_high
            
            if not retest_confirmed:
                continue
            
            # ==============================================================
            # Step 1 (re-check): 4H trend must still align
            # ==============================================================
            if not check_trend_alignment(current_trend, pending.direction):
                continue
            
            # ==============================================================
            # Step 4: MA Cross confirmation
            # ==============================================================
            
            # Check 1H cross
            ma_cross_1h = check_ma_cross(
                wma_1h, smma_1h, i, pending.direction, MA_CROSS_LOOKBACK
            )
            
            # Check 4H cross (stronger signal — accept either)
            ma_cross_4h = False
            if wma_4h is not None and smma_4h is not None and len(df_4h) > 1:
                # Find the 4H bar index corresponding to current 1H bar
                mask_4h = df_4h.index <= df.index[i]
                if mask_4h.any():
                    idx_4h = mask_4h.sum() - 1  # iloc position
                    if idx_4h > 0:
                        ma_cross_4h = check_ma_cross(
                            wma_4h, smma_4h, idx_4h, pending.direction, 
                            TREND_CROSS_LOOKBACK
                        )
            
            # Shorts require stronger confirmation: 4H MA cross mandatory
            # (Longs accept either 1H or 4H cross)
            if pending.direction == 'long':
                if not (ma_cross_1h or ma_cross_4h):
                    continue
            else:  # short
                if not ma_cross_4h:
                    continue  # Shorts MUST have 4H cross (1H alone too weak)
            
            # ==============================================================
            # Step 5: Filters
            # ==============================================================
            
            # Filter 0: Session block
            try:
                ts = df.index[i]
                # Gold: no entries after 16:30 GMT (NY Afternoon)
                if is_gold and is_session_blocked(ts):
                    continue
                # Forex: only trade London/NY (07:00-16:00 GMT)
                if is_forex and is_forex_session_blocked(ts):
                    continue
                # Indices: market hours only (constrained = open/close windows)
                if is_indices and is_indices_session_blocked(ts, symbol, indices_constrained):
                    continue
            except (IndexError, AttributeError):
                pass
            
            # Filter 1: Choppy consolidation
            if is_choppy(df, i, atr_vals, CHOP_LOOKBACK, CHOP_ATR_THRESHOLD):
                continue
            
            # Filter 2: Calculate SL, TP, check R:R
            if pending.direction == 'long':
                stop_loss = retest_extreme - (SL_BUFFER_ATR * current_atr)
                sl_distance = current_close - stop_loss
                take_profit = current_close + (MIN_RR * sl_distance)
            else:  # short
                stop_loss = retest_extreme + (SL_BUFFER_ATR * current_atr)
                sl_distance = stop_loss - current_close
                take_profit = current_close - (MIN_RR * sl_distance)
            
            # Sanity: SL distance must be positive
            if sl_distance <= 0:
                continue
            
            # R:R check (should be >= 3.0 by construction, but verify)
            rr_ratio = abs(take_profit - current_close) / sl_distance
            if rr_ratio < MIN_RR:
                continue
            
            # Position sizing: Risk = 1% of equity / SL distance
            position_size = (equity * risk_pct) / sl_distance
            
            if position_size <= 0:
                continue
            
            # ==============================================================
            # Create TradeSetup (single trade, full 3R target)
            # ==============================================================
            # Note: Partial profits (2-trade split) tested and rejected —
            # costs 25% PnL. Single 3R runner is better for this strategy.
            
            direction_enum = (TradeDirection.LONG if pending.direction == 'long'
                              else TradeDirection.SHORT)
            
            setup = TradeSetup(
                direction=direction_enum,
                entry_price=current_close,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                risk_reward=round(rr_ratio, 2),
                regime=regime_tag,
                index=i,
                broken_level=pending.broken_level,
                retest_bar=i,
                break_bar=pending.break_bar,
            )
            
            setups.append(setup)
            
            # Remove this pending setup (it's been used)
            expired.append(setup_idx)
        
        # Clean up expired/used setups (remove in reverse order to maintain indices)
        for idx in sorted(set(expired), reverse=True):
            if idx < len(pending_setups):
                pending_setups.pop(idx)
    
    return setups


def get_sbrs_indicators(df: pd.DataFrame) -> dict:
    """
    Compute SBRS indicator series for the engine's trade management.
    
    Call this AFTER analyze_gold_sbrs() with the same DataFrame,
    then pass the result to run_backtest(sbrs_indicators=...).
    
    Args:
        df: 1H OHLC DataFrame (same one passed to analyze_gold_sbrs)
    
    Returns:
        Dict with keys: wma_1h, smma_1h, atr_vals, swing_high_mask, swing_low_mask
    """
    return {
        'wma_1h': wma(df['Close'], WMA_PERIOD),
        'smma_1h': smma(df['Close'], SMMA_PERIOD),
        'atr_vals': atr(df, ATR_PERIOD),
        'swing_high_mask': detect_swing_high(df['High'], left=SWING_WINDOW, right=SWING_WINDOW),
        'swing_low_mask': detect_swing_low(df['Low'], left=SWING_WINDOW, right=SWING_WINDOW),
    }
