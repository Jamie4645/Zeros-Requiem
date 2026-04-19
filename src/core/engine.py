"""
SBRS 1.1 Backtest Engine

Runs backtests with:
- Slippage modelling (1.5 pips per trade)
- 5-layer risk management integration
- SBRS trade management (breakeven, MA cross exit, structure exit, timeout)
- Elite metrics: Sharpe, Sortino, Expectancy, RoMaD, consecutive streaks
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .risk_manager import RiskManager, RiskConfig
from ..execution.entries import TradeSetup, TradeDirection
from ..data.fetcher import detect_asset_class
from ..regimes import sbrs_v2 as _sbrs_v2_mod


# ── SBRS 1.0 Trade Management Parameters ─────────────────────
# These match the constants in sbrs_gold.py. Imported here to keep
# engine.py self-contained (no circular imports).
SBRS_BE_TRIGGER_R = 1.5     # Move SL to breakeven at 1.5R profit
SBRS_BE_BUFFER_R = 0.1      # Buffer above breakeven
SBRS_MAX_HOLD_BARS = 40     # Close trade after 40 bars
SBRS_TRAILING_TRIGGER_R = 3.0  # Start trailing at 3R profit

# ── SBRS 2.0 Trade Management Parameters ────────────────────
SBRS_V2_BE_TRIGGER_R = 1.5       # Same as v1
SBRS_V2_BE_BUFFER_R = 0.1        # Same as v1
SBRS_V2_MAX_HOLD_BARS = 40       # Same as v1
SBRS_V2_TRAILING_TRIGGER_R = 3.0 # Same as v1
SBRS_V2_COUNTER_TREND_TRAIL_R = 1.5  # Tighter trailing for counter-trend

# ── SBRS 2.0 Indices-Specific Exit Parameters ───────────────
SBRS_V2_INDICES_MAX_HOLD = 25        # Indices trend shorter than Gold
SBRS_V2_INDICES_BE_TRIGGER = 1.0     # Move to BE faster on indices
SBRS_V2_INDICES_TRAIL_R = 2.0        # Start trailing earlier on indices


class TradeStatus(Enum):
    PENDING = "pending"       # Limit order placed, waiting for fill
    OPEN = "open"
    CLOSED_TP = "closed_tp"
    CLOSED_SL = "closed_sl"
    CLOSED_TIME = "closed_time"  # Regime change exit
    CANCELLED = "cancelled"


@dataclass
class BacktestTrade:
    """A completed or active backtest trade."""
    trade_id: int
    setup: TradeSetup
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    regime: str
    status: TradeStatus = TradeStatus.OPEN
    exit_price: float = 0.0
    pnl: float = 0.0
    entry_index: int = 0
    exit_index: int = 0
    stop_moved_to_be: bool = False  # N2: Has stop been moved to breakeven?
    exit_reason: str = ""  # SBRS: 'tp', 'sl', 'exit_ma_cross', 'exit_structure', 'exit_timeout', 'breakeven_sl'


@dataclass
class BacktestResult:
    """Complete backtest result with elite performance metrics."""
    trades: List[BacktestTrade]
    equity_curve: List[float]
    initial_capital: float
    final_capital: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    regime_breakdown: Dict[str, Dict] = field(default_factory=dict)
    risk_stats: Dict = field(default_factory=dict)
    # Priority 6: Elite Metrics
    sharpe_ratio: float = 0.0           # Annualised risk-adjusted return
    sortino_ratio: float = 0.0          # Downside-only risk-adjusted return
    expectancy: float = 0.0             # Average $ per trade
    expectancy_r: float = 0.0           # Average R per trade (risk-adjusted)
    avg_win: float = 0.0                # Average winning trade $
    avg_loss: float = 0.0               # Average losing trade $
    max_consecutive_losses: int = 0     # Longest losing streak
    max_consecutive_wins: int = 0       # Longest winning streak
    romad: float = 0.0                  # Return on Max Drawdown
    total_return_pct: float = 0.0       # Total return as percentage


def manage_sbrs_trade(
    trade: BacktestTrade,
    df: pd.DataFrame,
    current_idx: int,
    wma_1h: pd.Series,
    smma_1h: pd.Series,
    atr_vals: pd.Series,
    swing_high_mask: pd.Series,
    swing_low_mask: pd.Series,
) -> Optional[str]:
    """
    Manage an open SBRS trade — check all exit conditions.
    
    Called once per bar for each open SBRS trade, AFTER the standard SL/TP 
    check. Only called when trade.regime == 'sbrs_gold'.
    
    Exit conditions checked (in priority order):
      1. SL/TP hit — already handled by engine before this is called
      2. Breakeven move — at 1.5R profit, move SL to entry + 0.1R
      3. MA cross reversal — WMA(9) crosses back through SMMA(7) against direction
      4. Structure break against — new confirmed swing forms against position
      5. Max hold time — 40 bars since entry, close at market
      6. Trailing stop (only if trade > 3R) — trail with most recent swing
    
    Args:
        trade: The open BacktestTrade (direction, entry_price, stop_loss, etc.)
        df: Full 1H OHLC DataFrame
        current_idx: Current bar integer position
        wma_1h: Pre-computed WMA(9) series
        smma_1h: Pre-computed SMMA(7) series
        atr_vals: Pre-computed ATR(14) series
        swing_high_mask: Boolean series from detect_swing_high()
        swing_low_mask: Boolean series from detect_swing_low()
    
    Returns:
        None — trade stays open, no action needed
        'breakeven' — SL moved to breakeven (trade stays open)
        'trailing_update' — trailing stop tightened (trade stays open)
        'exit_ma_cross' — close trade: MA crossed against direction
        'exit_structure' — close trade: adverse structure break
        'exit_timeout' — close trade: max hold time exceeded
    
    Side effects:
        Mutates trade.stop_loss (breakeven/trailing) and trade.stop_moved_to_be
    """
    is_long = trade.direction == 'long'
    initial_risk = abs(trade.entry_price - trade.setup.stop_loss)  # Use ORIGINAL SL for R calc
    
    if initial_risk <= 0:
        return None
    
    current_close = df['Close'].iloc[current_idx]
    current_high = df['High'].iloc[current_idx]
    current_low = df['Low'].iloc[current_idx]
    bars_held = current_idx - trade.entry_index
    
    # Current unrealised profit in R
    if is_long:
        current_profit = current_close - trade.entry_price
    else:
        current_profit = trade.entry_price - current_close
    current_r = current_profit / initial_risk
    
    # ------------------------------------------------------------------
    # Check 2: Breakeven move (at 1.5R profit)
    # ------------------------------------------------------------------
    if not trade.stop_moved_to_be:
        if is_long:
            bar_profit = current_high - trade.entry_price
        else:
            bar_profit = trade.entry_price - current_low
        
        if bar_profit >= SBRS_BE_TRIGGER_R * initial_risk:
            be_buffer = SBRS_BE_BUFFER_R * initial_risk
            if is_long:
                new_sl = trade.entry_price + be_buffer
                if new_sl > trade.stop_loss:
                    trade.stop_loss = new_sl
            else:
                new_sl = trade.entry_price - be_buffer
                if new_sl < trade.stop_loss:
                    trade.stop_loss = new_sl
            trade.stop_moved_to_be = True
            return 'breakeven'
    
    # ------------------------------------------------------------------
    # Check 3: MA cross reversal exit
    # WMA(9) crosses back through SMMA(7) AGAINST trade direction on 1H
    # ------------------------------------------------------------------
    if current_idx >= 1:
        w_curr = wma_1h.iloc[current_idx]
        s_curr = smma_1h.iloc[current_idx]
        w_prev = wma_1h.iloc[current_idx - 1]
        s_prev = smma_1h.iloc[current_idx - 1]
        
        if not (np.isnan(w_curr) or np.isnan(s_curr) or np.isnan(w_prev) or np.isnan(s_prev)):
            if _sbrs_v2_mod.USE_OLD_MA_CONVENTION:
                # OLD convention: long exits when SMMA crosses below WMA
                if is_long:
                    if s_curr < w_curr and s_prev >= w_prev:
                        return 'exit_ma_cross'
                else:
                    if s_curr > w_curr and s_prev <= w_prev:
                        return 'exit_ma_cross'
            else:
                if is_long:
                    if w_curr < s_curr and w_prev >= s_prev:
                        return 'exit_ma_cross'
                else:
                    if w_curr > s_curr and w_prev <= s_prev:
                        return 'exit_ma_cross'

    # ------------------------------------------------------------------
    # Check 4: Structure break against position
    # Long: new swing HIGH forms BELOW entry price (lower high = bearish)
    # Short: new swing LOW forms ABOVE entry price (higher low = bullish)
    # Only check swings that are detectable (3-bar lag already in mask)
    # ------------------------------------------------------------------
    if current_idx >= 3:
        if is_long:
            # Check if a recent swing high formed below our entry
            # Look at the most recent detectable swing high
            check_idx = current_idx - 3  # 3-bar confirmation lag
            if check_idx >= 0 and swing_high_mask.iloc[check_idx]:
                swing_val = df['High'].iloc[check_idx]
                if swing_val < trade.entry_price:
                    return 'exit_structure'
        else:
            # Check if a recent swing low formed above our entry
            check_idx = current_idx - 3
            if check_idx >= 0 and swing_low_mask.iloc[check_idx]:
                swing_val = df['Low'].iloc[check_idx]
                if swing_val > trade.entry_price:
                    return 'exit_structure'
    
    # ------------------------------------------------------------------
    # Check 5: Max hold time (40 bars)
    # ------------------------------------------------------------------
    if bars_held >= SBRS_MAX_HOLD_BARS:
        return 'exit_timeout'
    
    # ------------------------------------------------------------------
    # Check 6: Trailing stop (only if trade > 3R and keeps running)
    # Trail with most recent swing low (long) or swing high (short)
    # ------------------------------------------------------------------
    if current_r >= SBRS_TRAILING_TRIGGER_R and trade.stop_moved_to_be:
        if is_long:
            # Trail with most recent swing low
            search_end = current_idx - 3
            search_start = max(trade.entry_index, current_idx - 20)
            for j in range(search_end, search_start - 1, -1):
                if j >= 0 and swing_low_mask.iloc[j]:
                    trail_level = df['Low'].iloc[j]
                    if trail_level > trade.stop_loss and trail_level < current_close:
                        trade.stop_loss = trail_level
                        return 'trailing_update'
                    break  # Only check most recent
        else:
            # Trail with most recent swing high
            search_end = current_idx - 3
            search_start = max(trade.entry_index, current_idx - 20)
            for j in range(search_end, search_start - 1, -1):
                if j >= 0 and swing_high_mask.iloc[j]:
                    trail_level = df['High'].iloc[j]
                    if trail_level < trade.stop_loss and trail_level > current_close:
                        trade.stop_loss = trail_level
                        return 'trailing_update'
                    break
    
    return None


def manage_sbrs_v2_trade(
    trade: BacktestTrade,
    df: pd.DataFrame,
    current_idx: int,
    wma_1h: pd.Series,
    smma_1h: pd.Series,
    atr_vals: pd.Series,
    swing_high_mask: pd.Series,
    swing_low_mask: pd.Series,
) -> Optional[str]:
    """
    Manage an open SBRS 2.0 trade — inherits ALL v1 exit logic with
    counter-trend trailing enhancement and indices-specific parameters.

    Differences from v1:
      - Counter-trend trades start trailing at 1.5R instead of 3R
      - Indices trades use shorter max hold (25), faster BE (1.0R), earlier trailing (2.0R)

    Args / Returns: Same as manage_sbrs_trade().
    """
    is_long = trade.direction == 'long'
    is_indices_trade = trade.regime == 'sbrs_v2_indices'
    initial_risk = abs(trade.entry_price - trade.setup.stop_loss)

    if initial_risk <= 0:
        return None

    be_trigger = SBRS_V2_INDICES_BE_TRIGGER if is_indices_trade else SBRS_V2_BE_TRIGGER_R
    max_hold = SBRS_V2_INDICES_MAX_HOLD if is_indices_trade else SBRS_V2_MAX_HOLD_BARS

    current_close = df['Close'].iloc[current_idx]
    current_high = df['High'].iloc[current_idx]
    current_low = df['Low'].iloc[current_idx]
    bars_held = current_idx - trade.entry_index

    # Current unrealised profit in R
    if is_long:
        current_profit = current_close - trade.entry_price
    else:
        current_profit = trade.entry_price - current_close
    current_r = current_profit / initial_risk

    # ------------------------------------------------------------------
    # Check 2: Breakeven move (at 1.5R profit)
    # ------------------------------------------------------------------
    if not trade.stop_moved_to_be:
        if is_long:
            bar_profit = current_high - trade.entry_price
        else:
            bar_profit = trade.entry_price - current_low

        if bar_profit >= be_trigger * initial_risk:
            be_buffer = SBRS_V2_BE_BUFFER_R * initial_risk
            if is_long:
                new_sl = trade.entry_price + be_buffer
                if new_sl > trade.stop_loss:
                    trade.stop_loss = new_sl
            else:
                new_sl = trade.entry_price - be_buffer
                if new_sl < trade.stop_loss:
                    trade.stop_loss = new_sl
            trade.stop_moved_to_be = True
            return 'breakeven'

    # ------------------------------------------------------------------
    # Check 3: MA cross reversal exit
    # ------------------------------------------------------------------
    if current_idx >= 1:
        w_curr = wma_1h.iloc[current_idx]
        s_curr = smma_1h.iloc[current_idx]
        w_prev = wma_1h.iloc[current_idx - 1]
        s_prev = smma_1h.iloc[current_idx - 1]

        if not (np.isnan(w_curr) or np.isnan(s_curr) or np.isnan(w_prev) or np.isnan(s_prev)):
            if _sbrs_v2_mod.USE_OLD_MA_CONVENTION:
                if is_long:
                    if s_curr < w_curr and s_prev >= w_prev:
                        return 'exit_ma_cross'
                else:
                    if s_curr > w_curr and s_prev <= w_prev:
                        return 'exit_ma_cross'
            else:
                if is_long:
                    if w_curr < s_curr and w_prev >= s_prev:
                        return 'exit_ma_cross'
                else:
                    if w_curr > s_curr and w_prev <= s_prev:
                        return 'exit_ma_cross'

    # ------------------------------------------------------------------
    # Check 4: Structure break against position
    # ------------------------------------------------------------------
    if current_idx >= 3:
        if is_long:
            check_idx = current_idx - 3
            if check_idx >= 0 and swing_high_mask.iloc[check_idx]:
                swing_val = df['High'].iloc[check_idx]
                if swing_val < trade.entry_price:
                    return 'exit_structure'
        else:
            check_idx = current_idx - 3
            if check_idx >= 0 and swing_low_mask.iloc[check_idx]:
                swing_val = df['Low'].iloc[check_idx]
                if swing_val > trade.entry_price:
                    return 'exit_structure'

    # ------------------------------------------------------------------
    # Check 5: Max hold time (40 bars)
    # ------------------------------------------------------------------
    if bars_held >= max_hold:
        return 'exit_timeout'

    # ------------------------------------------------------------------
    # Check 6: Trailing stop — counter-trend trades trail earlier (1.5R)
    # ------------------------------------------------------------------
    is_counter_trend = getattr(trade.setup, 'is_counter_trend', False)
    if is_counter_trend:
        trailing_trigger = SBRS_V2_COUNTER_TREND_TRAIL_R
    elif is_indices_trade:
        trailing_trigger = SBRS_V2_INDICES_TRAIL_R
    else:
        trailing_trigger = SBRS_V2_TRAILING_TRIGGER_R

    if current_r >= trailing_trigger and trade.stop_moved_to_be:
        if is_long:
            search_end = current_idx - 3
            search_start = max(trade.entry_index, current_idx - 20)
            for j in range(search_end, search_start - 1, -1):
                if j >= 0 and swing_low_mask.iloc[j]:
                    trail_level = df['Low'].iloc[j]
                    if trail_level > trade.stop_loss and trail_level < current_close:
                        trade.stop_loss = trail_level
                        return 'trailing_update'
                    break  # Only check most recent
        else:
            search_end = current_idx - 3
            search_start = max(trade.entry_index, current_idx - 20)
            for j in range(search_end, search_start - 1, -1):
                if j >= 0 and swing_high_mask.iloc[j]:
                    trail_level = df['High'].iloc[j]
                    if trail_level < trade.stop_loss and trail_level > current_close:
                        trade.stop_loss = trail_level
                        return 'trailing_update'
                    break

    return None



def _check_ma_cross_inline(wma_1h, smma_1h, idx, direction, lookback=5):
    """
    Inline MA cross check for failed breakout reversal logic.
    Avoids circular import from sbrs_v2.

    Returns True if WMA crossed SMMA in the given direction within lookback bars.
    """
    if idx < 1 or idx >= len(wma_1h):
        return False

    for k in range(max(1, idx - lookback), idx + 1):
        w_curr = wma_1h.iloc[k]
        s_curr = smma_1h.iloc[k]
        w_prev = wma_1h.iloc[k - 1]
        s_prev = smma_1h.iloc[k - 1]

        if np.isnan(w_curr) or np.isnan(s_curr) or np.isnan(w_prev) or np.isnan(s_prev):
            continue

        if _sbrs_v2_mod.USE_OLD_MA_CONVENTION:
            if direction == 'long':
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


def run_backtest(
    df: pd.DataFrame,
    setups: List[TradeSetup],
    initial_capital: float = 10000.0,
    risk_config: Optional[RiskConfig] = None,
    apply_slippage: bool = True,
    sbrs_indicators: Optional[Dict[str, Any]] = None,
    sbrs_v2_indicators: Optional[Dict[str, Any]] = None
) -> BacktestResult:
    """
    Run a backtest on a list of TradeSetups.
    
    This is a universal engine -- it doesn't know about regimes.
    It receives validated setups and executes them with risk management.
    
    SBRS 1.0 trades get additional management via manage_sbrs_trade()
    when sbrs_indicators is provided.
    
    Args:
        df: OHLCV DataFrame
        setups: List of TradeSetup objects (from any regime)
        initial_capital: Starting capital
        risk_config: Risk management configuration
        apply_slippage: Whether to apply slippage tax
        sbrs_indicators: Optional dict with pre-computed SBRS 1.0 indicators:
            - wma_1h: WMA(9) series
            - smma_1h: SMMA(7) series
            - atr_vals: ATR(14) series
            - swing_high_mask: Boolean series from detect_swing_high()
            - swing_low_mask: Boolean series from detect_swing_low()
        sbrs_v2_indicators: Optional dict with pre-computed SBRS 2.0 indicators.
            Same structure as sbrs_indicators. If None, falls back to
            sbrs_indicators for v2 trades.
    """
    if risk_config is None:
        risk_config = RiskConfig()
    
    risk_mgr = RiskManager(risk_config, initial_capital)
    
    trades: List[BacktestTrade] = []
    open_trades: List[BacktestTrade] = []
    equity_curve = [initial_capital]
    trade_counter = 0
    current_capital = initial_capital
    
    # Sort setups by index
    setups_sorted = sorted(setups, key=lambda s: s.index)
    setup_idx = 0

    # SBRS 2.0: Failed breakout reversal — injected setups from SL exits
    injected_setups: List[tuple] = []  # List of (bar_index, TradeSetup)

    for i in range(len(df)):
        timestamp = df.index[i]
        current_high = df['High'].iloc[i]
        current_low = df['Low'].iloc[i]
        closed_this_bar: List[BacktestTrade] = []  # Track trades closed on this bar

        # ============================================================
        # Check exits for open trades
        # ============================================================
        for trade in open_trades[:]:
            exit_price = None
            status = None
            
            # N2: Breakeven stop — move SL to entry+buffer when trade is up 1.5R
            # Regime-aware: DISABLED for ALL Gold regimes (big winners need room to run)
            # Gold's edge is asymmetric: rare large wins (avg $212) vs small losses (avg $79).
            # The BE stop clips these fat-tail winners, destroying the edge.
            # Active for Forex and Crypto where it improves win rate.
            # SBRS trades have their own BE logic in manage_sbrs_trade() — skip here.
            gold_regimes = ('gold_ny_momentum', 'gold_daily_momentum', 'gold_asia_mr', 'gold_daily_mr')
            sbrs_regimes = ('sbrs_gold', 'sbrs_forex', 'sbrs_indices')
            sbrs_v2_regimes = ('sbrs_v2_gold', 'sbrs_v2_forex', 'sbrs_v2_indices', 'sbrs_v2_crypto')
            if not trade.stop_moved_to_be and trade.risk_amount > 0 \
               and trade.regime not in gold_regimes \
               and trade.regime not in sbrs_regimes \
               and trade.regime not in sbrs_v2_regimes:
                initial_risk = abs(trade.entry_price - trade.stop_loss)
                if initial_risk > 0:
                    be_trigger = initial_risk * 1.5  # Trigger at 1.5R profit
                    be_buffer = initial_risk * 0.1   # Small buffer past breakeven
                    if trade.direction == 'long':
                        current_profit = current_high - trade.entry_price
                        if current_profit >= be_trigger:
                            trade.stop_loss = trade.entry_price + be_buffer
                            trade.stop_moved_to_be = True
                    else:  # short
                        current_profit = trade.entry_price - current_low
                        if current_profit >= be_trigger:
                            trade.stop_loss = trade.entry_price - be_buffer
                            trade.stop_moved_to_be = True
            
            if trade.direction == 'long':
                if current_low <= trade.stop_loss:
                    exit_price = trade.stop_loss
                    status = TradeStatus.CLOSED_SL
                elif current_high >= trade.take_profit:
                    exit_price = trade.take_profit
                    status = TradeStatus.CLOSED_TP
            else:  # short
                if current_high >= trade.stop_loss:
                    exit_price = trade.stop_loss
                    status = TradeStatus.CLOSED_SL
                elif current_low <= trade.take_profit:
                    exit_price = trade.take_profit
                    status = TradeStatus.CLOSED_TP
            
            if exit_price is not None:
                # Apply slippage to exit
                if apply_slippage:
                    exit_price = risk_mgr.apply_slippage(exit_price, 
                        'short' if trade.direction == 'long' else 'long')  # Adverse slippage
                
                trade.exit_price = exit_price
                trade.exit_index = i
                trade.status = status
                # Tag exit reason for analysis
                if not trade.exit_reason:
                    if status == TradeStatus.CLOSED_TP:
                        trade.exit_reason = 'tp'
                    elif status == TradeStatus.CLOSED_SL:
                        trade.exit_reason = 'sl_be' if trade.stop_moved_to_be else 'sl'
                
                # Calculate PnL
                if trade.direction == 'long':
                    trade.pnl = (exit_price - trade.entry_price) * trade.position_size
                else:
                    trade.pnl = (trade.entry_price - exit_price) * trade.position_size
                
                current_capital += trade.pnl
                risk_mgr.update_capital(current_capital, trade.pnl)
                open_trades.remove(trade)
                closed_this_bar.append(trade)

        # ============================================================
        # SBRS 2.0 Trade Management (for sbrs_v2_* trades)
        # Runs AFTER SL/TP check — same structure as v1 with counter-trend
        # trailing enhancement.
        # ============================================================
        v2_ind = sbrs_v2_indicators or sbrs_indicators
        if v2_ind is not None:
            for trade in open_trades[:]:
                if trade.regime not in ('sbrs_v2_gold', 'sbrs_v2_forex', 'sbrs_v2_indices'):
                    continue

                result = manage_sbrs_v2_trade(
                    trade, df, i,
                    v2_ind['wma_1h'],
                    v2_ind['smma_1h'],
                    v2_ind['atr_vals'],
                    v2_ind['swing_high_mask'],
                    v2_ind['swing_low_mask'],
                )

                if result is not None and result.startswith('exit_'):
                    exit_price = df['Close'].iloc[i]
                    if apply_slippage:
                        exit_price = risk_mgr.apply_slippage(exit_price,
                            'short' if trade.direction == 'long' else 'long')

                    trade.exit_price = exit_price
                    trade.exit_index = i
                    trade.status = TradeStatus.CLOSED_TIME
                    trade.exit_reason = result

                    if trade.direction == 'long':
                        trade.pnl = (exit_price - trade.entry_price) * trade.position_size
                    else:
                        trade.pnl = (trade.entry_price - exit_price) * trade.position_size

                    current_capital += trade.pnl
                    risk_mgr.update_capital(current_capital, trade.pnl)
                    open_trades.remove(trade)

        # ============================================================
        # SBRS 1.0 Trade Management (only for sbrs_gold trades)
        # Runs AFTER SL/TP check — handles breakeven, MA cross exit,
        # structure break exit, timeout, and trailing stops.
        # ============================================================
        if sbrs_indicators is not None:
            for trade in open_trades[:]:
                if trade.regime not in ('sbrs_gold', 'sbrs_forex', 'sbrs_indices'):
                    continue
                
                result = manage_sbrs_trade(
                    trade, df, i,
                    sbrs_indicators['wma_1h'],
                    sbrs_indicators['smma_1h'],
                    sbrs_indicators['atr_vals'],
                    sbrs_indicators['swing_high_mask'],
                    sbrs_indicators['swing_low_mask'],
                )
                
                if result is not None and result.startswith('exit_'):
                    # Close trade at current bar's close
                    exit_price = df['Close'].iloc[i]
                    if apply_slippage:
                        exit_price = risk_mgr.apply_slippage(exit_price,
                            'short' if trade.direction == 'long' else 'long')
                    
                    trade.exit_price = exit_price
                    trade.exit_index = i
                    trade.status = TradeStatus.CLOSED_TIME  # Managed exit
                    trade.exit_reason = result  # Store specific reason
                    
                    if trade.direction == 'long':
                        trade.pnl = (exit_price - trade.entry_price) * trade.position_size
                    else:
                        trade.pnl = (trade.entry_price - exit_price) * trade.position_size
                    
                    current_capital += trade.pnl
                    risk_mgr.update_capital(current_capital, trade.pnl)
                    open_trades.remove(trade)
        
        # ============================================================
        # SBRS 2.0: Failed Breakout Reversal
        # When a v2 trade hits SL, check if a reverse trade is valid
        # ============================================================
        for closed_trade in closed_this_bar:
            if not closed_trade.regime.startswith('sbrs_v2'):
                continue
            if closed_trade.exit_reason != 'sl':
                continue

            indicators = sbrs_v2_indicators or sbrs_indicators
            if indicators is None:
                continue

            opposite_dir = 'short' if closed_trade.direction == 'long' else 'long'
            wma_1h = indicators['wma_1h']
            smma_1h = indicators['smma_1h']

            ma_confirms = _check_ma_cross_inline(wma_1h, smma_1h, i, opposite_dir, lookback=5)

            if not ma_confirms:
                continue

            atr_val = indicators['atr_vals'].iloc[i] if i < len(indicators['atr_vals']) else None
            if atr_val is None or pd.isna(atr_val):
                continue

            broken_level = closed_trade.setup.broken_level
            if broken_level == 0.0:
                continue

            # Calculate reverse SL/TP
            sl_buffer = atr_val * 0.3
            if opposite_dir == 'long':
                entry_price = broken_level
                sl = closed_trade.entry_price - sl_buffer
                sl = min(sl, broken_level - sl_buffer)
                risk = entry_price - sl
                tp = entry_price + risk * 3.0
            else:
                entry_price = broken_level
                sl = closed_trade.entry_price + sl_buffer
                sl = max(sl, broken_level + sl_buffer)
                risk = sl - entry_price
                tp = entry_price - risk * 3.0

            if risk <= 0:
                continue

            rr = abs(tp - entry_price) / risk
            if rr < 2.0:
                continue

            # Create reverse TradeSetup
            equity = current_capital
            pos_size = (equity * risk_config.risk_per_trade) / risk if risk > 0 else 0
            reverse_setup = TradeSetup(
                direction=TradeDirection.LONG if opposite_dir == 'long' else TradeDirection.SHORT,
                entry_price=entry_price,
                stop_loss=sl,
                take_profit=tp,
                position_size=pos_size,
                risk_reward=rr,
                regime=closed_trade.regime,  # Keep same v2 regime tag
                index=i + 1,                 # Execute on next bar
                broken_level=broken_level,
                retest_bar=i,
                break_bar=closed_trade.setup.break_bar,
                confluence_score=1.5,
                fvg_present=closed_trade.setup.fvg_present,
                liquidity_sweep=closed_trade.setup.liquidity_sweep,
                ma_cross_confirmed=True,
                is_counter_trend=False,
            )

            injected_setups.append((i + 1, reverse_setup))

        # ============================================================
        # Process new setups at this bar (includes injected reversals)
        # ============================================================
        # Check for injected setups ready at this bar
        ready_injected = [s for bar_idx, s in injected_setups if bar_idx <= i]
        injected_setups = [(bar_idx, s) for bar_idx, s in injected_setups if bar_idx > i]

        while setup_idx < len(setups_sorted) and setups_sorted[setup_idx].index <= i:
            setup = setups_sorted[setup_idx]
            setup_idx += 1
            
            # Skip if setup is for a future bar (limit order not yet reached)
            if setup.index != i:
                continue
            
            # Risk management check
            risk_amount = abs(setup.entry_price - setup.stop_loss) * setup.position_size
            can_trade, reason = risk_mgr.can_trade(
                open_trades, setup.direction, risk_amount, timestamp
            )
            
            if not can_trade:
                continue
            
            # Apply slippage to entry
            entry_price = setup.entry_price
            if apply_slippage:
                entry_price = risk_mgr.apply_slippage(entry_price, setup.direction)
            
            # Create trade
            # Normalise direction to string — TradeSetup may store
            # TradeDirection enum or plain string depending on regime.
            raw_dir = setup.direction
            dir_str = raw_dir.value if hasattr(raw_dir, 'value') else str(raw_dir)
            
            trade_counter += 1
            trade = BacktestTrade(
                trade_id=trade_counter,
                setup=setup,
                direction=dir_str,
                entry_price=entry_price,
                stop_loss=setup.stop_loss,
                take_profit=setup.take_profit,
                position_size=setup.position_size,
                risk_amount=risk_amount,
                regime=setup.regime,
                entry_index=i
            )
            
            trades.append(trade)
            open_trades.append(trade)

        # ── Process injected setups (SBRS 2.0 failed breakout reversals) ──
        for setup in ready_injected:
            risk_amount = abs(setup.entry_price - setup.stop_loss) * setup.position_size
            can_trade, reason = risk_mgr.can_trade(
                open_trades, setup.direction, risk_amount, timestamp
            )

            if not can_trade:
                continue

            entry_price = setup.entry_price
            if apply_slippage:
                entry_price = risk_mgr.apply_slippage(entry_price, setup.direction)

            raw_dir = setup.direction
            dir_str = raw_dir.value if hasattr(raw_dir, 'value') else str(raw_dir)

            trade_counter += 1
            trade = BacktestTrade(
                trade_id=trade_counter,
                setup=setup,
                direction=dir_str,
                entry_price=entry_price,
                stop_loss=setup.stop_loss,
                take_profit=setup.take_profit,
                position_size=setup.position_size,
                risk_amount=risk_amount,
                regime=setup.regime,
                entry_index=i
            )

            trades.append(trade)
            open_trades.append(trade)

        equity_curve.append(current_capital)
    
    # Close any remaining open trades at last price
    if open_trades:
        last_close = df['Close'].iloc[-1]
        for trade in open_trades:
            trade.exit_price = last_close
            trade.exit_index = len(df) - 1
            trade.status = TradeStatus.CLOSED_TIME
            if trade.direction == 'long':
                trade.pnl = (last_close - trade.entry_price) * trade.position_size
            else:
                trade.pnl = (trade.entry_price - last_close) * trade.position_size
            current_capital += trade.pnl
    
    # ============================================================
    # Generate report
    # ============================================================
    closed = [t for t in trades if t.status != TradeStatus.PENDING]
    winners = [t for t in closed if t.pnl > 0]
    losers = [t for t in closed if t.pnl <= 0]
    
    total_pnl = sum(t.pnl for t in closed)
    win_rate = len(winners) / len(closed) * 100 if closed else 0
    
    gross_win = sum(t.pnl for t in winners) if winners else 0
    gross_loss = abs(sum(t.pnl for t in losers)) if losers else 0
    profit_factor = gross_win / gross_loss if gross_loss > 0 else float('inf')
    
    # Max drawdown from equity curve
    equity = np.array(equity_curve)
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak * 100
    max_dd = np.max(drawdown) if len(drawdown) > 0 else 0
    
    # Regime breakdown
    regime_breakdown = {}
    for trade in closed:
        r = trade.regime
        if r not in regime_breakdown:
            regime_breakdown[r] = {'count': 0, 'wins': 0, 'pnl': 0.0}
        regime_breakdown[r]['count'] += 1
        regime_breakdown[r]['pnl'] += trade.pnl
        if trade.pnl > 0:
            regime_breakdown[r]['wins'] += 1
    
    # ============================================================
    # Priority 6: Elite Performance Metrics
    # ============================================================
    
    # Average win / average loss
    avg_win = gross_win / len(winners) if winners else 0.0
    avg_loss = gross_loss / len(losers) if losers else 0.0
    
    # Expectancy: average $ per trade
    expectancy = total_pnl / len(closed) if closed else 0.0
    
    # Expectancy R: average risk-adjusted return per trade
    # R = pnl / risk_amount for each trade
    r_values = []
    for t in closed:
        if t.risk_amount > 0:
            r_values.append(t.pnl / t.risk_amount)
    expectancy_r = np.mean(r_values) if r_values else 0.0
    
    # Max consecutive wins / losses
    max_con_losses = 0
    max_con_wins = 0
    current_streak = 0
    streak_type = None  # 'w' or 'l'
    for t in closed:
        if t.pnl > 0:
            if streak_type == 'w':
                current_streak += 1
            else:
                current_streak = 1
                streak_type = 'w'
            max_con_wins = max(max_con_wins, current_streak)
        else:
            if streak_type == 'l':
                current_streak += 1
            else:
                current_streak = 1
                streak_type = 'l'
            max_con_losses = max(max_con_losses, current_streak)
    
    # Sharpe Ratio (annualised)
    # Convert equity curve to periodic returns, then annualise
    sharpe = 0.0
    sortino = 0.0
    if len(equity) > 2:
        returns = np.diff(equity) / equity[:-1]
        returns = returns[np.isfinite(returns)]
        if len(returns) > 1 and np.std(returns) > 0:
            # Estimate periods per year based on data length and timeframe
            # equity has one entry per bar, so len(equity) ~ number of bars
            # For annualisation: assume ~252 trading days
            # 1H ~ 6 bars/day => ~1512/year
            # 4H ~ 1.5 bars/day => ~378/year
            # 1D ~ 1 bar/day => ~252/year
            bars_per_year = min(len(equity), 1512)  # Cap at 1H estimate
            if len(df) > 0:
                # Estimate from actual data span
                try:
                    span_days = (df.index[-1] - df.index[0]).days
                    if span_days > 0:
                        bars_per_year = len(df) / span_days * 252
                except (TypeError, AttributeError):
                    pass
            
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (mean_return / std_return) * np.sqrt(bars_per_year)
            
            # Sortino: only penalise downside deviation
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = np.std(downside_returns)
                if downside_std > 0:
                    sortino = (mean_return / downside_std) * np.sqrt(bars_per_year)
    
    # Return on Max Drawdown (RoMaD)
    max_dd_amount = (np.max(peak - equity)) if len(equity) > 0 else 0
    romad = total_pnl / max_dd_amount if max_dd_amount > 0 else float('inf') if total_pnl > 0 else 0.0
    
    # Total return %
    total_return_pct = (current_capital - initial_capital) / initial_capital * 100
    
    return BacktestResult(
        trades=trades,
        equity_curve=equity_curve,
        initial_capital=initial_capital,
        final_capital=current_capital,
        total_trades=len(closed),
        winning_trades=len(winners),
        losing_trades=len(losers),
        win_rate=round(win_rate, 2),
        total_pnl=round(total_pnl, 2),
        profit_factor=round(profit_factor, 2),
        max_drawdown_pct=round(max_dd, 2),
        regime_breakdown=regime_breakdown,
        risk_stats=risk_mgr.get_stats(),
        sharpe_ratio=round(sharpe, 2),
        sortino_ratio=round(sortino, 2),
        expectancy=round(expectancy, 2),
        expectancy_r=round(expectancy_r, 3),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        max_consecutive_losses=max_con_losses,
        max_consecutive_wins=max_con_wins,
        romad=round(romad, 2),
        total_return_pct=round(total_return_pct, 2)
    )
