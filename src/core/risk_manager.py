"""
Risk Management for SCAF 2.0 -- The Mark Douglas Risk Kernel

5 layers of professional risk management:
1. Daily loss limit (3%)
2. Drawdown circuit breaker (10%)
3. Max concurrent risk (6%)
4. Correlation awareness (timeframe-adaptive)
5. Volatility-adjusted position sizing (ATR * 2)

Position Size = (Equity * 0.01) / (ATR(14) * 2)
This ensures every trade risks exactly 1% of capital regardless of asset.

O3 optimisation: max_same_direction is now timeframe-adaptive.
1H data generates clustered signals — needs higher concurrency limit.
"""

import pandas as pd
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RiskConfig:
    """Risk management parameters."""
    risk_per_trade: float = 0.01          # 1% risk per trade
    max_daily_loss_pct: float = 0.03      # 3% max daily loss
    max_drawdown_pct: float = 0.10        # 10% drawdown = pause
    max_concurrent_risk_pct: float = 0.06 # 6% total concurrent risk
    max_same_direction: int = 2           # Max trades in same direction (4H default)
    slippage_pips: float = 1.5            # Slippage tax per trade


def risk_config_for_interval(interval: str, risk_per_trade: float = 0.01) -> RiskConfig:
    """
    O3: Create a RiskConfig adapted to the timeframe.
    
    1H data clusters signals — needs wider concurrency limits.
    Daily data is sparse — can keep tighter limits.
    """
    config = RiskConfig(risk_per_trade=risk_per_trade)
    
    if interval in ('1m', '5m', '15m', '30m'):
        config.max_same_direction = 5       # Scalping: many concurrent trades
        config.max_concurrent_risk_pct = 0.08
        config.max_daily_loss_pct = 0.04    # Wider daily limit for fast TFs
    elif interval == '1h':
        config.max_same_direction = 4       # O3: 2→4 for 1H (was blocking 77 Gold trades)
        config.max_concurrent_risk_pct = 0.08  # Allow more concurrent risk
    elif interval == '4h':
        config.max_same_direction = 2       # Default
        config.max_concurrent_risk_pct = 0.06
    else:  # daily, weekly
        config.max_same_direction = 2
        config.max_concurrent_risk_pct = 0.06
    
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
        """Apply slippage tax to entry price."""
        # Convert pips to price units based on price magnitude
        if entry_price > 1000:
            slip = self.config.slippage_pips * 0.1  # Gold: 1 pip = $0.10
        elif entry_price > 10:
            slip = self.config.slippage_pips * 0.01  # Stocks
        elif entry_price > 1:
            slip = self.config.slippage_pips * 0.0001  # Forex
        else:
            slip = self.config.slippage_pips * 0.01  # Other
        
        if direction == 'long':
            return entry_price + slip  # Worse fill for longs
        else:
            return entry_price - slip  # Worse fill for shorts
    
    def can_trade(self, open_trades: list, new_direction: str, new_risk: float, timestamp) -> Tuple[bool, str]:
        """
        Master risk check. Returns (can_trade, reason_if_blocked).
        """
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
            same_dir = sum(1 for t in open_trades if getattr(t, 'direction', '') == new_direction)
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
