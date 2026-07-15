"""
Sovereign Breakout Retest Realm (SBRS) 2.0 — Multi-Asset Regime

Breakout + Retest strategy based on 3-4 years of profitable manual Gold trading.
SBRS 2.0 adds confluence scoring, counter-trend trades, and smart money concepts
while preserving the proven core logic from SBRS 1.1.

Asset:      Gold (XAUUSD) primary, Forex, Indices
Timeframes: 1H for entries, 4H for trend context
Strategy:   Structure break -> retest -> confluence scoring -> enter

Upgrades over SBRS 1.1:
  - Confluence scoring replaces binary MA cross gate
  - Counter-trend trades allowed with higher confluence threshold
  - Fair Value Gap (FVG) detection (downweighted to +0.5 after Ablation Round 2)
  - Liquidity sweep detection for smart money confirmation
  - Level quality scoring (touch count)

Removed in Ablation Round 2 (2026-04-16) — all proved net-zero or negative:
  - Squeeze filter (dead: 0.0% impact)
  - Chop filter (dead: 0.0% impact)
  - Whipsaw detection (dead: 0.0% impact — previously deleted)

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
from ..indicators.smart_money import (
    detect_fvg_near_level,
    detect_liquidity_sweep,
    count_level_touches,
    detect_false_breakout
)
from ..execution.entries import TradeSetup, TradeDirection
from ..core.risk_manager import SYMBOL_RISK_CAP, _normalize_symbol_for_cap


def capped_risk_pct(risk_pct: float, symbol: str) -> float:
    """Clamp caller-requested risk to the authoritative per-symbol ceiling.

    SYMBOL_RISK_CAP (src/core/risk_manager.py) is the single source of truth for
    the Round 8 evidence-weighted sizing. Applying it HERE — inside the one
    function shared by backtest, walk-forward, and the live engine — guarantees
    strategy/live parity: no caller can size above the council-approved ceiling.

    Returns min(risk_pct, cap) when the symbol maps to a cap; otherwise the
    caller's value unchanged. A 0.0000 cap (e.g. USDJPY paper-only exclusion)
    returns 0.0, which collapses position_size to 0 and skips every setup.
    """
    key = _normalize_symbol_for_cap(symbol)
    cap = SYMBOL_RISK_CAP.get(key) if key else None
    return min(risk_pct, cap) if cap is not None else risk_pct


# ── Core Parameters (DO NOT OPTIMIZE) ─────────────────────────
WMA_PERIOD = 9
SMMA_PERIOD = 7
SWING_LOOKBACK = 20       # bars to search for swings
SWING_WINDOW = 3          # bars on each side for swing confirmation
MIN_RR = 3.0              # minimum risk:reward ratio (Gold)
MIN_RR_INDICES = 2.0      # indices have tighter moves — lower R:R still profitable
MIN_RR_FOREX = 2.5        # forex between Gold and indices
MIN_RR_CRYPTO = 2.5       # crypto similar to forex
RETEST_TOLERANCE_ATR = 0.7        # retest proximity for LONGS (ATR units)
RETEST_TOLERANCE_ATR_SHORT = 0.3  # tighter retest for SHORTS (shorts are weaker, demand better entries)

# ── Tunable Parameters (can test +/-20%) ────────────────────────
ATR_PERIOD = 14
MAX_RETEST_WAIT = 10      # max bars to wait for retest after break
SL_BUFFER_ATR = 0.3       # SL distance beyond retest extreme
BE_TRIGGER_R = 1.5        # move SL to breakeven at this R-multiple
BE_BUFFER_R = 0.1         # buffer above breakeven
MAX_HOLD_BARS = 40        # close trade after this many bars
MA_CROSS_LOOKBACK = 10    # bars to search for recent MA cross on 1H
TREND_CROSS_LOOKBACK = 5  # "recently crossed" on 4H (in 4H bars)

# ── Session Filter ────────────────────────────────────────────
# Gold: Round 5 council flipped this to the 99 sentinel (belt-and-braces with
# GOLD_SESSION_FILTER_ENABLED=False). `is_session_blocked` now returns False
# for every hour 0-23. Forex has its own FOREX_SESSION_START/END_HOUR below and
# is unaffected. Any future ablation or re-enable must be an explicit decision.
SESSION_BLOCK_START_HOUR = 99    # sentinel — Gold session filter permanently OFF
SESSION_BLOCK_START_MINUTE = 30  # retained for parity (unused when hour=99)
SESSION_BLOCK_END_HOUR = 24      # retained for parity (unused when hour=99)
# Gold session filter: Round 5 WF re-confirmed session-OFF beats session-ON by
# +31% ($21,785 vs $16,608), 7/8 windows profitable on session-OFF. The original
# "NY afternoon loses money" claim was Yahoo-era and did not survive OANDA data.
# See knowledge-base/67-Round-5-Post-Council-Validation.md.
GOLD_SESSION_FILTER_ENABLED = False

# ── Forex-Specific Parameters ─────────────────────────────────
FOREX_RETEST_TOLERANCE_ATR = 0.3  # tighter than Gold's 0.5 (both directions)
FOREX_SESSION_START_HOUR = 7      # London open (GMT)
FOREX_SESSION_END_HOUR = 16       # NY close (GMT)

# ── Indices-Specific Parameters ───────────────────────────────
INDICES_RETEST_TOLERANCE_ATR = 0.5  # same as Gold (trending instruments)

# Market hours (GMT) per index
INDICES_SESSIONS = {
    '^GSPC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},   # S&P 500
    '^IXIC':  {'open_h': 13, 'open_m': 30, 'close_h': 20, 'close_m': 0},   # NASDAQ
    '^GDAXI': {'open_h': 7,  'open_m': 0,  'close_h': 15, 'close_m': 30},  # DAX
}

# Constrained windows: first 90 min after open, last 60 min before close
INDICES_OPEN_WINDOW_MINUTES = 90
INDICES_CLOSE_WINDOW_MINUTES = 60

# ── SBRS 2.0 Confluence Scoring ──────────────────────────────
# FVG downweighted from 1.0 to 0.5 after Ablation Round 2 (2026-04-16):
# full 17-test ablation showed removing FVG lifted PnL +154%, PF 1.31→2.11,
# Sharpe 0.64→1.15, DD 10.1%→7.5%. At weight 1.0, FVG alone qualified
# marginal setups; at 0.5 it requires pairing with another booster to
# reach the 1.0 with-trend threshold. See knowledge-base/50-Ablation-Round-2-FVG-Downshift.md.
CONFLUENCE_SCORE_FVG = 0.5           # Fair value gap present (downweighted from 1.0)
CONFLUENCE_SCORE_LIQUIDITY = 1.0     # Liquidity sweep detected
CONFLUENCE_SCORE_MA_CROSS = 0.5      # MA crossover confirms direction
CONFLUENCE_SCORE_LEVEL_QUALITY = 0.5 # Level has 3+ touches (bonus)

CONFLUENCE_MIN_WITH_TREND = 1.0      # Min score for with-trend trades (at least 1 booster)
CONFLUENCE_MIN_COUNTER_TREND = 2.0   # Min score for counter-trend (2+ boosters required)
CONFLUENCE_MIN_AFTER_FALSE_BO = 2.0  # Min score when false breakout at level (2+ boosters)

# Forex-specific with-trend threshold (arbiter-forex Round 4 finding): at 1.0,
# FVG(0.5) + MA(0.5) setups qualified with no liquidity sweep — driver of
# GBP/USD W7 collapse. Forex requires at least Liquidity(1.0) + any partial.
# Precedent: MIN_RR_FOREX already differs from MIN_RR. Not global — forex only.
#
# Round 7 ablation (2026-04-19): 1.0 tested and REJECTED. Across 6 forex pairs:
# 3/6 went NEGATIVE (GBPUSD 12%-consistency, -$8.2k; USDJPY PF 0.60; NZDUSD -$569),
# 2/6 degraded materially (EURJPY/AUDJPY still profitable but below elite floor),
# 1/6 (USDCHF) cleared 500-trade gate at 1.0 but PF collapsed 2.12→1.52 and
# Sharpe 1.17→0.85 — sub-elite. 1.5 threshold is load-bearing for forex edge.
CONFLUENCE_MIN_WITH_TREND_FOREX = 1.5

# ── Counter-Trend ────────────────────────────────────────────
COUNTER_TREND_RR_MIN = 2.0          # Reduced R:R minimum for counter-trend
COUNTER_TREND_TP_FACTOR = 0.7       # Place TP at 70% of distance to prev swing

# ── Level Quality ────────────────────────────────────────────
MIN_LEVEL_TOUCHES = 2                  # Methodology: "at least two confirmed touches"

# ── Crypto-Specific Parameters ────────────────────────────────
CRYPTO_RETEST_TOLERANCE_ATR = 0.5  # Similar to Gold (trending + volatile)

# ── Regime Awareness: ATR Percentile Filter ──────────────────
ATR_PCTILE_LOOKBACK = 100    # bars of ATR history for percentile calc
ATR_PCTILE_THRESHOLD = 25    # skip entries when ATR below this percentile
ATR_PCTILE_ENABLED_GOLD = True
ATR_PCTILE_ENABLED_FOREX = True
ATR_PCTILE_ENABLED_INDICES = False   # indices already have session filters
ATR_PCTILE_ENABLED_CRYPTO = False    # crypto is always volatile

# ── Adaptive R:R Based on ATR Regime ─────────────────────────
ATR_RR_LOOKBACK = 50         # bars for ATR moving average
ATR_RR_CLAMP_LOW = 1.0      # minimum R:R scaling factor — 2026-07-02 audit fix:
                            #   was 0.7, which let with-trend targets shrink to
                            #   2.1R in violation of SACRED MIN_RR=3.0 (canon
                            #   Step 5: skip if R:R < 3.0). The old "gate" at the
                            #   call site compared effective_rr to its own clamp
                            #   floor (2.1 < 2.1) and could never fire. Adaptive
                            #   widening (up to 1.5x in high vol) is retained.
ATR_RR_CLAMP_HIGH = 1.5     # maximum R:R scaling factor

# ── Indices Retest (wider for erratic price action) ──────────
INDICES_RETEST_TOLERANCE_ATR_V2 = 0.6  # Wider than v1's 0.5

# ── Causal 4H context (backtest / walk-forward) ──────────────
# Enough 1H history for 4H WMA(9)/SMMA(7) + trend classification (~200+ days).
CAUSAL_4H_LOOKBACK_1H = 5000

# ── MA Convention Ablation Flag (test-only) ──────────────────
# When True, inverts WMA>SMMA bullish/bearish logic across ALL MA callsites:
#   - compute_4h_context (4H trend classifier)
#   - check_ma_cross (1H entry confluence)
#   - engine._check_ma_cross_inline (failed-BO reversal)
#   - engine.manage_sbrs_v2_trade MA exit block
# Ablation Round 3 erroneously patched only check_ma_cross (1/3 callsites) —
# produced PF 5.23 chimera result. Council Round 4 mandated a coherent
# whole-system flag. NEVER set True in production. Ablation harness toggles it.
USE_OLD_MA_CONVENTION = False


# ── State Tracking ────────────────────────────────────────────

@dataclass
class PendingSetupV2:
    """Tracks a structure break waiting for retest confirmation (v2)."""
    direction: str           # 'long' or 'short'
    broken_level: float      # the swing level that was broken
    break_bar: int           # bar index (iloc) where break occurred
    bars_waiting: int = 0    # incremented each bar while waiting
    is_counter_trend: bool = False
    false_breakout_at_level: bool = False
    breakout_attempt: int = 1
    in_squeeze: bool = False
    level_touches: int = 0
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
      Neutral: everything else
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
            if USE_OLD_MA_CONVENTION:
                # OLD convention: SMMA crossing above WMA = bullish
                if smma_vals[j] > wma_vals[j] and smma_vals[j-1] <= wma_vals[j-1]:
                    recently_crossed_bullish = True
                if smma_vals[j] < wma_vals[j] and smma_vals[j-1] >= wma_vals[j-1]:
                    recently_crossed_bearish = True
            else:
                # NEW (momentum) convention: WMA crossing above SMMA = bullish
                if wma_vals[j] > smma_vals[j] and wma_vals[j-1] <= smma_vals[j-1]:
                    recently_crossed_bullish = True
                if wma_vals[j] < smma_vals[j] and wma_vals[j-1] >= smma_vals[j-1]:
                    recently_crossed_bearish = True

        if USE_OLD_MA_CONVENTION:
            ma_bullish = smma_vals[i] > wma_vals[i]
            ma_bearish = smma_vals[i] < wma_vals[i]
        else:
            ma_bullish = wma_vals[i] > smma_vals[i]
            ma_bearish = wma_vals[i] < smma_vals[i]
        price_above_wma = closes[i] > wma_vals[i]
        price_below_wma = closes[i] < wma_vals[i]

        if price_above_wma and (ma_bullish or recently_crossed_bullish):
            trends.append('bullish')
        elif price_below_wma and (ma_bearish or recently_crossed_bearish):
            trends.append('bearish')
        else:
            trends.append('neutral')

    df_4h['trend_4h'] = trends
    return df_4h


def map_4h_to_1h(df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> pd.Series:
    """
    Map 4H trend context to each 1H bar.

    Each 1H bar gets the trend from the most recently COMPLETED 4H bar.
    This prevents look-ahead bias.

    Args:
        df_1h: 1H DataFrame
        df_4h: 4H DataFrame with trend_4h column

    Returns:
        pd.Series of trend values aligned to 1H index
    """
    trends_1h = pd.Series('neutral', index=df_1h.index)

    if len(df_4h) == 0:
        return trends_1h

    for i in range(len(df_1h)):
        ts_1h = df_1h.index[i]
        mask = df_4h.index <= ts_1h
        if mask.any():
            last_4h_idx = df_4h.index[mask][-1]
            trends_1h.iloc[i] = df_4h.loc[last_4h_idx, 'trend_4h']

    return trends_1h


def drop_incomplete_last_4h_bar(df_4h: pd.DataFrame, df_1h_sub: pd.DataFrame) -> pd.DataFrame:
    """
    Remove the trailing 4H row if the underlying 1H data does not yet cover
    the full 4-hour bucket (causal backtest: no peeking at future 1H bars).

    Assumes 4H labels are left-aligned (pandas default): bucket [T, T+4h) uses
    1H bars at T, T+1h, T+2h, T+3h.
    """
    if df_4h is None or len(df_4h) == 0 or df_1h_sub is None or len(df_1h_sub) == 0:
        return df_4h
    last_ts = df_1h_sub.index[-1]
    last_bin_start = df_4h.index[-1]
    last_hour_in_bin = last_bin_start + pd.Timedelta(hours=3)
    if last_ts < last_hour_in_bin:
        return df_4h.iloc[:-1]
    return df_4h


def trend_4h_at_bar_causal(df_1h: pd.DataFrame, bar_index: int) -> str:
    """
    4H trend as known at the close of 1H bar `bar_index` only — uses
    df_1h.iloc[:bar_index+1] (no future 1H), drops incomplete trailing 4H bucket.

    Prefer ``causal_4h_trend_series`` inside backtests (O(n)); this is for
    live logging and tests that need a single index.
    """
    if bar_index < 0 or bar_index >= len(df_1h):
        return 'neutral'
    start = max(0, bar_index - CAUSAL_4H_LOOKBACK_1H + 1)
    sub = df_1h.iloc[start : bar_index + 1]
    df4 = resample_to_4h(sub)
    df4 = drop_incomplete_last_4h_bar(df4, sub)
    if len(df4) < WMA_PERIOD + SMMA_PERIOD:
        return 'neutral'
    df4 = compute_4h_context(df4)
    return str(df4['trend_4h'].iloc[-1])


def causal_4h_trend_series(df_1h: pd.DataFrame) -> pd.Series:
    """
    For each 1H bar i, the 4H trend using only completed 4H bars (no future 1H).

    Vectorized O(n log n): resample once, compute trend once, then use
    searchsorted to map each 1H bar to the last *completed* 4H bar.
    A 4H bar labelled T is complete after the T+3h 1H bar closes.
    """
    if len(df_1h) == 0:
        return pd.Series(dtype=str)

    df_4h = resample_to_4h(df_1h)
    df_4h = drop_incomplete_last_4h_bar(df_4h, df_1h)

    if len(df_4h) < WMA_PERIOD + SMMA_PERIOD:
        return pd.Series('neutral', index=df_1h.index)

    df_4h = compute_4h_context(df_4h)

    completion_times = df_4h.index + pd.Timedelta(hours=3)
    positions = completion_times.searchsorted(df_1h.index, side='right') - 1

    trend_vals = df_4h['trend_4h'].values
    result = np.where(
        positions >= 0,
        trend_vals[np.clip(positions, 0, len(trend_vals) - 1)],
        'neutral',
    )
    return pd.Series(result, index=df_1h.index)


def check_trend_alignment(trend_4h: str, direction: str) -> bool:
    """
    Verify 4H trend aligns with proposed trade direction.

    Args:
        trend_4h: '4H trend -- 'bullish', 'bearish', or 'neutral'
        direction: Proposed trade direction -- 'long' or 'short'

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

        if USE_OLD_MA_CONVENTION:
            if direction == 'long':
                # OLD convention: SMMA crosses above WMA = bullish
                if s_curr > w_curr and s_prev <= w_prev:
                    return True
            else:
                if s_curr < w_curr and s_prev >= w_prev:
                    return True
        else:
            if direction == 'long':
                if w_curr > s_curr and w_prev <= s_prev:
                    return True
            else:
                if w_curr < s_curr and w_prev >= s_prev:
                    return True

    return False


# ── Session Filters ──────────────────────────────────────────

def _to_utc_hour_minute(timestamp):
    """
    Extract (hour, minute) from a timestamp in UTC.

    All SBRS session filters are defined in GMT/UTC. Yahoo returns tz-aware
    America/New_York; OANDA returns tz-aware UTC; some sources return naive.
    Without normalisation, the same wall-clock hour means different real
    times across sources (arbiter-data Round 4: 18.9% Yahoo bars misclassified).

    Returns (hour, minute) in UTC for tz-aware timestamps; falls back to
    the raw hour/minute for naive timestamps (assumed to already be UTC).
    """
    try:
        if getattr(timestamp, 'tzinfo', None) is not None:
            ts_utc = timestamp.tz_convert('UTC')
            return ts_utc.hour, ts_utc.minute
        return timestamp.hour, timestamp.minute
    except AttributeError:
        return None


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
    hm = _to_utc_hour_minute(timestamp)
    if hm is None:
        return False
    hour, minute = hm

    session = INDICES_SESSIONS.get(symbol, INDICES_SESSIONS['^GSPC'])
    open_h, open_m = session['open_h'], session['open_m']
    close_h, close_m = session['close_h'], session['close_m']

    current_min = hour * 60 + minute
    open_min = open_h * 60 + open_m
    close_min = close_h * 60 + close_m

    # Block if outside market hours entirely
    if current_min < open_min or current_min >= close_min:
        return True

    if not constrained:
        return False

    # Constrained: only allow first 90 min and last 60 min
    open_window_end = open_min + INDICES_OPEN_WINDOW_MINUTES
    close_window_start = close_min - INDICES_CLOSE_WINDOW_MINUTES

    if current_min < open_window_end:
        return False  # In open window
    if current_min >= close_window_start:
        return False  # In close window

    return True  # Mid-session -- block in constrained mode


def is_forex_session_blocked(timestamp) -> bool:
    """
    Check if current bar is outside London/NY for forex.
    Forex only trades 07:00-16:00 GMT (London open to NY close).
    """
    hm = _to_utc_hour_minute(timestamp)
    if hm is None:
        return False
    hour, _ = hm
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
    hm = _to_utc_hour_minute(timestamp)
    if hm is None:
        return False  # Daily data -- no session filter
    hour, minute = hm

    # Block from 16:30 to 23:59 GMT
    if hour > SESSION_BLOCK_START_HOUR:
        return True
    if hour == SESSION_BLOCK_START_HOUR and minute >= SESSION_BLOCK_START_MINUTE:
        return True

    return False


# ── Regime Awareness: ATR Percentile Filter ──────────────────

def is_low_volatility(
    atr_vals: pd.Series,
    current_idx: int,
    lookback: int = ATR_PCTILE_LOOKBACK,
    threshold: int = ATR_PCTILE_THRESHOLD
) -> bool:
    """
    Skip entries when current ATR is below the Nth percentile of recent history.
    Targets low-vol dead zones (Gold W5-W6, GBP W4/W6/W7).
    """
    start = max(0, current_idx - lookback)
    history = atr_vals.iloc[start:current_idx + 1].dropna()

    if len(history) < 20:
        return False

    current_atr = atr_vals.iloc[current_idx]
    if np.isnan(current_atr):
        return False

    pctile_value = np.percentile(history.values, threshold)
    return current_atr < pctile_value


def compute_adaptive_rr(
    atr_vals: pd.Series,
    current_idx: int,
    base_rr: float,
    lookback: int = ATR_RR_LOOKBACK,
    clamp_low: float = ATR_RR_CLAMP_LOW,
    clamp_high: float = ATR_RR_CLAMP_HIGH
) -> float:
    """
    Scale R:R target based on current ATR relative to its recent average.
    High vol -> wider TP (up to 1.5x), low vol -> tighter TP (down to 0.7x).
    """
    start = max(0, current_idx - lookback)
    history = atr_vals.iloc[start:current_idx + 1].dropna()

    if len(history) < 10:
        return base_rr

    current_atr = atr_vals.iloc[current_idx]
    avg_atr = history.mean()

    if np.isnan(current_atr) or np.isnan(avg_atr) or avg_atr <= 0:
        return base_rr

    ratio = current_atr / avg_atr
    clamped = max(clamp_low, min(clamp_high, ratio))
    return base_rr * clamped


# ── Main Strategy Function ────────────────────────────────────

def analyze_sbrs_v2(
    df: pd.DataFrame,
    equity: float = 10000.0,
    risk_pct: float = 0.01,
    asset_class: str = 'gold',
    symbol: str = '',
    indices_constrained: bool = False,
    entry_mode: str = 'close'
) -> List[TradeSetup]:
    """
    SBRS 2.0 — Confluence-scored Breakout + Retest for Gold, Forex, and Indices.

    Processes 1H/4H data bar-by-bar, generating TradeSetup objects
    compatible with the backtest engine.

    Entry Protocol (ALL conditions required):
      1. 4H trend context checked (with-trend preferred, counter-trend allowed)
      2. Structure break: close beyond recent swing high/low (20-bar lookback)
      3. Retest: price returns within tolerance ATR of broken level
      4. Confluence scoring: FVG + liquidity sweep + MA cross + level quality
      5. Filters: session, R:R check, min confluence score

    SBRS 2.0 upgrades over 1.1:
      - Confluence scoring replaces binary MA cross gate
      - Counter-trend trades allowed with higher confluence threshold (2.0)
      - FVG (+0.5 downweighted) and liquidity sweep (+1.0) for smart money confirmation
      - Level quality bonus for levels with 3+ touches

    Asset-specific adjustments:
      Gold:    0.5 ATR longs / 0.3 shorts, no entries after 16:30 GMT
      Forex:   0.3 ATR both directions, London/NY only (07-16 GMT)
      Indices: 0.6 ATR both directions (wider for erratic PA), market hours only.

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
    # Enforce the authoritative per-symbol risk ceiling at the single shared
    # entry point (backtest + walk-forward + live all flow through here).
    risk_pct = capped_risk_pct(risk_pct, symbol)

    is_forex = asset_class == 'forex'
    is_gold = asset_class in ('gold', 'commodity')
    is_indices = asset_class == 'indices'
    is_crypto = asset_class == 'crypto'

    if is_forex:
        regime_tag = 'sbrs_v2_forex'
        min_rr = MIN_RR_FOREX
    elif is_indices:
        regime_tag = 'sbrs_v2_indices'
        min_rr = MIN_RR_INDICES
    elif is_crypto:
        regime_tag = 'sbrs_v2_crypto'
        min_rr = MIN_RR_CRYPTO
    else:
        regime_tag = 'sbrs_v2_gold'
        min_rr = MIN_RR

    if len(df) < 50:
        return []

    # ================================================================
    # Phase 1: Pre-computation (1H + causal 4H trend — no future 1H bars)
    # ================================================================

    trend_context = causal_4h_trend_series(df)

    # 1H indicators
    wma_1h = wma(df['Close'], WMA_PERIOD)
    smma_1h = smma(df['Close'], SMMA_PERIOD)
    atr_vals = atr(df, ATR_PERIOD)

    # Swing detection (pre-compute full masks)
    swing_high_mask = detect_swing_high(df['High'], left=SWING_WINDOW, right=SWING_WINDOW)
    swing_low_mask = detect_swing_low(df['Low'], left=SWING_WINDOW, right=SWING_WINDOW)

    # ================================================================
    # Phase 2: Bar-by-bar loop
    # ================================================================

    pending_setups: List[PendingSetupV2] = []
    setups: List[TradeSetup] = []

    # Track breakout attempts per level (keyed by rounded level)
    breakout_attempts: dict = {}

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

        # V2: detect breaks in BOTH trend directions (counter-trend allowed)
        # With-trend breaks: standard entry path
        # Counter-trend breaks: require higher confluence score

        # Look for LONG setup: price closes ABOVE recent swing high
        swing_high_result = get_recent_swing_high(
            df['High'], swing_high_mask, i, SWING_LOOKBACK
        )
        if swing_high_result is not None:
            sh_idx, sh_level = swing_high_result
            if current_close > sh_level:
                # Check we don't already have a pending setup for this level
                already_pending = any(
                    abs(p.broken_level - sh_level) < current_atr * 0.1
                    for p in pending_setups
                )
                if not already_pending:
                    # Determine if this is counter-trend
                    is_ct = not check_trend_alignment(current_trend, 'long')

                    # Check for false breakout history at this level
                    level_key = round(sh_level / current_atr) * current_atr
                    false_bo = detect_false_breakout(df, sh_level, 'long', i, current_atr)

                    # Track breakout attempts at this level
                    attempt_key = round(sh_level, 2)
                    breakout_attempts[attempt_key] = breakout_attempts.get(attempt_key, 0) + 1
                    attempt_num = breakout_attempts[attempt_key]

                    # Squeeze detection removed in Ablation Round 2 — confirmed net-zero impact.
                    squeeze = False

                    # Count level touches for quality
                    touches = count_level_touches(df, sh_level, i, current_atr)

                    # Hard gate: methodology requires at least 2 confirmed touches
                    if touches >= MIN_LEVEL_TOUCHES:
                        pending_setups.append(PendingSetupV2(
                            direction='long',
                            broken_level=sh_level,
                            break_bar=i,
                            bars_waiting=0,
                            is_counter_trend=is_ct,
                            false_breakout_at_level=false_bo,
                            breakout_attempt=attempt_num,
                            in_squeeze=squeeze,
                            level_touches=touches,
                            created_at=ts_str
                        ))

        # Look for SHORT setup: price closes BELOW recent swing low
        swing_low_result = get_recent_swing_low(
            df['Low'], swing_low_mask, i, SWING_LOOKBACK
        )
        if swing_low_result is not None:
            sl_idx, sl_level = swing_low_result
            if current_close < sl_level:
                already_pending = any(
                    abs(p.broken_level - sl_level) < current_atr * 0.1
                    for p in pending_setups
                )
                if not already_pending:
                    is_ct = not check_trend_alignment(current_trend, 'short')

                    false_bo = detect_false_breakout(df, sl_level, 'short', i, current_atr)

                    attempt_key = round(sl_level, 2)
                    breakout_attempts[attempt_key] = breakout_attempts.get(attempt_key, 0) + 1
                    attempt_num = breakout_attempts[attempt_key]

                    squeeze = False  # removed in Ablation Round 2

                    touches = count_level_touches(df, sl_level, i, current_atr)

                    # Hard gate: methodology requires at least 2 confirmed touches
                    if touches >= MIN_LEVEL_TOUCHES:
                        pending_setups.append(PendingSetupV2(
                            direction='short',
                            broken_level=sl_level,
                            break_bar=i,
                            bars_waiting=0,
                            is_counter_trend=is_ct,
                            false_breakout_at_level=false_bo,
                            breakout_attempt=attempt_num,
                            in_squeeze=squeeze,
                            level_touches=touches,
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
                long_tolerance = FOREX_RETEST_TOLERANCE_ATR
                short_tolerance = FOREX_RETEST_TOLERANCE_ATR
            elif is_indices:
                long_tolerance = INDICES_RETEST_TOLERANCE_ATR_V2
                short_tolerance = RETEST_TOLERANCE_ATR_SHORT
            elif is_crypto:
                long_tolerance = CRYPTO_RETEST_TOLERANCE_ATR
                short_tolerance = CRYPTO_RETEST_TOLERANCE_ATR
            else:
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
            # Step 4: Confluence Scoring (replaces binary MA cross gate)
            # ==============================================================

            score = 0.0

            # Fair Value Gap during the breakout move (between break bar and retest bar)
            # Per methodology: FVG must form during the breakout, not just anywhere
            fvg_lookback = min(i - pending.break_bar, 10)  # Only search breakout window
            fvg = detect_fvg_near_level(
                df, i, pending.broken_level, pending.direction, current_atr,
                lookback=max(fvg_lookback, 3), proximity_atr=0.5  # Tighter proximity
            )

            # Liquidity sweep detected
            liq = detect_liquidity_sweep(df, i, swing_high_mask, swing_low_mask, pending.direction,
                                         swing_confirm_lag=SWING_WINDOW)

            # MA cross confirmation
            ma_valid = check_ma_cross(wma_1h, smma_1h, i, pending.direction, MA_CROSS_LOOKBACK)

            if fvg:
                score += CONFLUENCE_SCORE_FVG
            if liq:
                score += CONFLUENCE_SCORE_LIQUIDITY
            if ma_valid:
                score += CONFLUENCE_SCORE_MA_CROSS
            if pending.level_touches >= 3:
                score += CONFLUENCE_SCORE_LEVEL_QUALITY

            # Determine minimum score based on trade type
            if pending.is_counter_trend:
                min_score = CONFLUENCE_MIN_COUNTER_TREND
            elif pending.false_breakout_at_level:
                min_score = CONFLUENCE_MIN_AFTER_FALSE_BO
            elif is_forex:
                min_score = CONFLUENCE_MIN_WITH_TREND_FOREX
            else:
                min_score = CONFLUENCE_MIN_WITH_TREND

            if score < min_score:
                continue  # Not enough confluence

            # ==============================================================
            # Step 5: Filters
            # ==============================================================

            # Filter 0: Session block (crypto trades 24/7 — no session filter)
            try:
                ts = df.index[i]
                if is_gold and GOLD_SESSION_FILTER_ENABLED and is_session_blocked(ts):
                    continue
                if is_forex and is_forex_session_blocked(ts):
                    continue
                if is_indices and is_indices_session_blocked(ts, symbol, indices_constrained):
                    continue
            except (IndexError, AttributeError):
                pass

            # Filter 0.5: Low-volatility regime filter (ATR percentile)
            use_vol_filter = (
                (is_gold and ATR_PCTILE_ENABLED_GOLD) or
                (is_forex and ATR_PCTILE_ENABLED_FOREX) or
                (is_indices and ATR_PCTILE_ENABLED_INDICES) or
                (is_crypto and ATR_PCTILE_ENABLED_CRYPTO)
            )
            if use_vol_filter and is_low_volatility(atr_vals, i):
                continue

            # Filter 1: Calculate SL, TP, check R:R
            if pending.direction == 'long':
                stop_loss = retest_extreme - (SL_BUFFER_ATR * current_atr)
                sl_distance = current_close - stop_loss
            else:  # short
                stop_loss = retest_extreme + (SL_BUFFER_ATR * current_atr)
                sl_distance = stop_loss - current_close

            # Sanity: SL distance must be positive
            if sl_distance <= 0:
                continue

            # TP calculation: counter-trend uses reduced target
            if pending.is_counter_trend:
                # Find previous swing extreme in trade direction
                if pending.direction == 'long':
                    prev_swing = get_recent_swing_high(
                        df['High'], swing_high_mask, i, SWING_LOOKBACK * 2
                    )
                    if prev_swing is not None:
                        _, prev_level = prev_swing
                        raw_distance = prev_level - current_close
                        if raw_distance > 0:
                            take_profit = current_close + (COUNTER_TREND_TP_FACTOR * raw_distance)
                        else:
                            take_profit = current_close + (min_rr * sl_distance)
                    else:
                        take_profit = current_close + (min_rr * sl_distance)
                else:  # short counter-trend
                    prev_swing = get_recent_swing_low(
                        df['Low'], swing_low_mask, i, SWING_LOOKBACK * 2
                    )
                    if prev_swing is not None:
                        _, prev_level = prev_swing
                        raw_distance = current_close - prev_level
                        if raw_distance > 0:
                            take_profit = current_close - (COUNTER_TREND_TP_FACTOR * raw_distance)
                        else:
                            take_profit = current_close - (min_rr * sl_distance)
                    else:
                        take_profit = current_close - (min_rr * sl_distance)

                ct_rr = abs(take_profit - current_close) / sl_distance
                if ct_rr < COUNTER_TREND_RR_MIN:
                    continue
                rr_ratio = ct_rr
            else:
                # Standard with-trend target (adaptive R:R based on ATR regime)
                effective_rr = compute_adaptive_rr(atr_vals, i, min_rr)
                if pending.direction == 'long':
                    take_profit = current_close + (effective_rr * sl_distance)
                else:
                    take_profit = current_close - (effective_rr * sl_distance)

                rr_ratio = abs(take_profit - current_close) / sl_distance
                # Defensive invariant, NOT the primary control (rr_ratio is
                # derived from effective_rr, which compute_adaptive_rr already
                # clamps to >= min_rr since ATR_RR_CLAMP_LOW = 1.0). Enforces
                # SACRED MIN_RR if either of those ever drifts again.
                if rr_ratio < min_rr:
                    continue

            # Position sizing: Risk = 1% of equity / SL distance
            position_size = (equity * risk_pct) / sl_distance

            if position_size <= 0:
                continue

            # ==============================================================
            # Create TradeSetup (single trade, full target)
            # ==============================================================

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
                confluence_score=score,
                fvg_present=fvg,
                liquidity_sweep=liq,
                ma_cross_confirmed=ma_valid,
                is_counter_trend=pending.is_counter_trend,
                level_touches=pending.level_touches,
                in_squeeze=pending.in_squeeze,
                breakout_attempt=pending.breakout_attempt,
            )

            # Methodology-faithful limit-at-retest entry (A/B mode). Reprice the
            # entry from the retest-bar close to the broken level — where the
            # discretionary trader rests the limit ("limit orders exclusively").
            # The engine then fills only on a real touch of the level. SACRED
            # params are untouched; only entry pricing + sizing change.
            if entry_mode == 'limit':
                lvl = pending.broken_level
                limit_sl_dist = abs(lvl - stop_loss)
                if lvl > 0 and limit_sl_dist > 0:
                    if pending.direction == 'long':
                        setup.take_profit = lvl + rr_ratio * limit_sl_dist
                    else:
                        setup.take_profit = lvl - rr_ratio * limit_sl_dist
                    setup.entry_price = lvl
                    setup.position_size = (equity * risk_pct) / limit_sl_dist
                    setup.is_limit = True

            setups.append(setup)

            # Remove this pending setup (it's been used)
            expired.append(setup_idx)

        # Clean up expired/used setups (remove in reverse order to maintain indices)
        for idx in sorted(set(expired), reverse=True):
            if idx < len(pending_setups):
                pending_setups.pop(idx)

    # Deduplicate: one setup per bar, keep highest confluence score
    if setups:
        by_bar = {}
        for s in setups:
            if s.index not in by_bar or s.confluence_score > by_bar[s.index].confluence_score:
                by_bar[s.index] = s
        setups = sorted(by_bar.values(), key=lambda s: s.index)

    return setups


def get_sbrs_v2_indicators(df: pd.DataFrame) -> dict:
    """
    Compute SBRS 2.0 indicator series for the engine's trade management.

    Call this AFTER analyze_sbrs_v2() with the same DataFrame,
    then pass the result to run_backtest(sbrs_indicators=...).

    Args:
        df: 1H OHLC DataFrame (same one passed to analyze_sbrs_v2)

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
