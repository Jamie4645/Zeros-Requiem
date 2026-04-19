"""
Risk Management — 5-Layer System

1. Daily loss limit (3%)
2. Drawdown circuit breaker (10%)
3. Max concurrent risk (6-8%, timeframe-adaptive)
4. Direction concentration limits
5. Volatility-adjusted position sizing: (Equity * 1%) / (ATR(14) * 2)
"""

import pandas as pd
from typing import List, Tuple, Optional, Any
from dataclasses import dataclass


# Per-symbol risk ceilings. Instruments below the 500-trade minimum elite bar
# are capped at 0.25% until additional data lifts the count above 500.
#   - GBPUSD: Round 5 council, 274→275 WF trades
#   - USDJPY: Round 7 council, 161 BT / 160 WF trades; MC Elite-PASS but
#     under-sampled at ~20 trades/window
# Other Tier-1 strategies are already cleared and absent from this mapping.
SYMBOL_RISK_CAP = {
    'GBPUSD': 0.0025,
    'USDJPY': 0.0025,
}


def _normalize_symbol_for_cap(symbol: Optional[str]) -> Optional[str]:
    """Normalize a symbol identifier to match SYMBOL_RISK_CAP keys.

    Accepts Yahoo (`GBPUSD=X`), OANDA (`GBP_USD`), or plain (`GBPUSD` / `gbpusd`).
    """
    if symbol is None:
        return None
    normalized = symbol.strip().upper().replace('=X', '').replace('_', '')
    return normalized


def normalize_direction(direction: Any) -> str:
    """
    Normalize TradeDirection enum or string to 'long' | 'short'.

    Risk layers and slippage compare against plain strings; callers may pass
    TradeSetup.direction as TradeDirection — this keeps behaviour consistent.
    """
    if direction is None:
        return 'long'
    if isinstance(direction, str):
        d = direction.strip().lower()
        return d if d in ('long', 'short') else 'long'
    val = getattr(direction, 'value', direction)
    d = str(val).strip().lower()
    return d if d in ('long', 'short') else 'long'


@dataclass
class RiskConfig:
    """Risk management parameters."""
    risk_per_trade: float = 0.01          # 1% risk per trade
    max_daily_loss_pct: float = 0.03      # 3% max daily loss
    max_drawdown_pct: float = 0.10        # 10% drawdown = pause
    max_concurrent_risk_pct: float = 0.06 # 6% total concurrent risk
    max_same_direction: int = 2           # Max trades in same direction (4H default)
    slippage_pips: float = 0.75           # Slippage tax per trade (Round 7 recal from 1.5 — B1 was 2-3× realistic OANDA CFD cost)


def risk_config_for_interval(
    interval: str,
    risk_per_trade: float = 0.01,
    asset_class: str = 'gold',
    symbol: Optional[str] = None,
) -> RiskConfig:
    """
    Create a RiskConfig adapted to the timeframe and asset class.

    1H data clusters signals — needs wider concurrency limits.
    Daily data is sparse — can keep tighter limits.
    Indices/forex/crypto get a wider drawdown cap (20%) for proper sample sizes.

    `symbol` is consulted against SYMBOL_RISK_CAP; if the normalized symbol is
    present, the effective risk_per_trade is reduced to min(caller, cap). This
    is the mechanism for the Round 5 GBPUSD 0.25% hard-cap.
    """
    key = _normalize_symbol_for_cap(symbol)
    cap = SYMBOL_RISK_CAP.get(key) if key else None
    effective_risk = min(risk_per_trade, cap) if cap is not None else risk_per_trade
    config = RiskConfig(risk_per_trade=effective_risk)
    
    if interval in ('1m', '5m', '15m', '30m'):
        config.max_same_direction = 5
        config.max_concurrent_risk_pct = 0.08
        config.max_daily_loss_pct = 0.04
    elif interval == '1h':
        config.max_same_direction = 4
        config.max_concurrent_risk_pct = 0.08
    elif interval == '4h':
        config.max_same_direction = 2
        config.max_concurrent_risk_pct = 0.06
    else:
        config.max_same_direction = 2
        config.max_concurrent_risk_pct = 0.06
    
    if asset_class in ('indices', 'forex', 'crypto', 'gold', 'commodity'):
        config.max_drawdown_pct = 0.20
        config.max_daily_loss_pct = 0.05
        config.max_concurrent_risk_pct = 0.10
        config.max_same_direction = 5

    return config


class RiskManager:
    """Professional-grade risk management system."""
    
    def __init__(self, config: RiskConfig, initial_capital: float):
        self.config = config
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.peak_equity = initial_capital
        
        # Daily tracking
        self.daily_start_capital = initial_capital
        self.daily_pnl = 0.0
        self.current_day = None
        
        # State
        self.paused = False
        
        # Stats
        self.stats = {
            'blocked_daily_limit': 0,
            'blocked_drawdown': 0,
            'blocked_concurrent': 0,
            'blocked_correlation': 0,
            'total_blocked': 0,
            'max_drawdown_pct': 0.0,
            'peak_equity': initial_capital,
        }
    
    def update_day(self, timestamp) -> None:
        """Reset daily P&L on new day."""
        try:
            day = timestamp.date()
        except AttributeError:
            return
        
        if self.current_day is None:
            self.current_day = day
        elif day != self.current_day:
            self.current_day = day
            self.daily_start_capital = self.current_capital
            self.daily_pnl = 0.0
    
    def update_capital(self, new_capital: float, trade_pnl: float = 0) -> None:
        """Update capital and track peak."""
        self.current_capital = new_capital
        self.daily_pnl += trade_pnl
        
        if new_capital > self.peak_equity:
            self.peak_equity = new_capital
            self.stats['peak_equity'] = new_capital
            self.paused = False
        
        # Track max drawdown
        dd = (self.peak_equity - new_capital) / self.peak_equity if self.peak_equity > 0 else 0
        if dd > self.stats['max_drawdown_pct']:
            self.stats['max_drawdown_pct'] = dd
    
    def calculate_position_size(self, atr_value: float) -> float:
        """
        Volatility-adjusted position sizing.
        PositionSize = (Equity * risk_pct) / (ATR(14) * 2)
        """
        if atr_value <= 0:
            return 0
        return (self.current_capital * self.config.risk_per_trade) / (atr_value * 2)
    
    def apply_slippage(self, entry_price: float, direction: str) -> float:
        """Apply slippage tax to entry price.

        Round 5 council (Y1): NASDAQ/DAX were under-costed 3-13x under the
        old `entry_price > 1000` bracket. New `>5000` bracket applies a full
        index-point (1.5 * 1.0) adverse slip to reflect real spread+impact.
        """
        direction = normalize_direction(direction)
        if entry_price > 5000:
            slip = self.config.slippage_pips * 1.0     # Indices (NDX/DAX): 0.75 pt slip post R7 recal
        elif entry_price > 1000:
            slip = self.config.slippage_pips * 0.1     # Gold: $0.075 slip post R7 recal
        elif entry_price > 10:
            slip = self.config.slippage_pips * 0.01    # Stocks / low-priced indices
        elif entry_price > 0.01:
            slip = self.config.slippage_pips * 0.0001  # Forex: 0.000075 price units post R7 recal
        else:
            slip = self.config.slippage_pips * 0.000001  # Sub-penny assets
        
        if direction == 'long':
            return entry_price + slip
        else:
            return entry_price - slip
    
    def can_trade(self, open_trades: list, new_direction: str, new_risk: float, timestamp) -> Tuple[bool, str]:
        """
        Master risk check. Returns (can_trade, reason_if_blocked).
        """
        new_direction = normalize_direction(new_direction)
        self.update_day(timestamp)
        
        # Layer 1: Daily loss limit
        max_daily = self.daily_start_capital * self.config.max_daily_loss_pct
        if self.daily_pnl < -max_daily:
            self.stats['blocked_daily_limit'] += 1
            self.stats['total_blocked'] += 1
            return (False, "daily_loss_limit")
        
        # Layer 2: Drawdown circuit breaker
        dd = (self.peak_equity - self.current_capital) / self.peak_equity if self.peak_equity > 0 else 0
        if dd >= self.config.max_drawdown_pct:
            self.paused = True
            self.stats['blocked_drawdown'] += 1
            self.stats['total_blocked'] += 1
            return (False, "drawdown_breaker")
        
        # Layer 3: Concurrent risk
        current_risk = sum(getattr(t, 'risk_amount', 0) for t in open_trades)
        max_risk = self.current_capital * self.config.max_concurrent_risk_pct
        if current_risk + new_risk > max_risk:
            self.stats['blocked_concurrent'] += 1
            self.stats['total_blocked'] += 1
            return (False, "concurrent_risk")
        
        # Layer 4: Direction concentration
        if open_trades:
            same_dir = sum(
                1 for t in open_trades
                if normalize_direction(getattr(t, 'direction', '')) == new_direction
            )
            if same_dir >= self.config.max_same_direction:
                self.stats['blocked_correlation'] += 1
                self.stats['total_blocked'] += 1
                return (False, "correlation")
        
        return (True, "")
    
    def get_stats(self) -> dict:
        """Return risk management statistics."""
        return {
            **self.stats,
            'current_drawdown_pct': (self.peak_equity - self.current_capital) / self.peak_equity * 100 if self.peak_equity > 0 else 0,
        }
