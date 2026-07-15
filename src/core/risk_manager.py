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


# Per-symbol risk ceilings — Round 8 evidence-weighted sizing
# (merges Philosophical Council barbell with Arbiter Council per-strategy MC).
#
# Reasoning (see knowledge-base/76-Round-8-Evidence-Weighted-Sizing.md):
#   - Gold      0.50% — anchor; 100% WF, Sharpe 1.78, structural R3 hedge
#   - DAX       0.25% — PLATEAU slip curve; under-500 trades (457); MC 2.42%
#   - NDX       0.15% — SLOPE slip curve (fragile); concentrated 2022–23; MC 0.80%
#   - GBPUSD    0.20% — 100% WF, small trade count (275); MC 0.00%
#   - USDJPY    0.00% — REMOVED from live queue; 161 trades / Short-heavy;
#                       BT PF 3.18 > 3.0 red-flag; re-test when 500 trades clear
#
# Total portfolio live risk: 1.10% (was 1.50% post-R7).
# Falsifier #4 governs the auto-demote path if trade counts move.
# ⚠️ 2026-06-09 — Gold-only freeze for the ZTT rebuild.
# All non-Gold instruments PAUSED (capped to 0.0000) per user directive while
# the new intraday-Gold "Zero's True Trade" strategy is built and validated.
# Prior Round-8 sizes kept in comments for restoration. NOTE: a prior audit
# found this dict is only consulted by walk_forward.py + the sbrs_v2
# `capped_risk_pct` chokepoint, NOT the live runner — so pausing in
# src/live/runner.py (SYMBOLS_CONFIG) is the authoritative live brake; this is
# defense-in-depth + intent documentation.
SYMBOL_RISK_CAP = {
    'GOLD':   0.0100,  # 2026-06-09: raised 0.50%→1.00% — Gold is the ONLY live instrument
                       # under the ZTT freeze, so total portfolio risk = 1.00%. Reverts to
                       # ~0.50% when paused instruments are restored. (Takes effect only once
                       # ZTT clears the paper gate — nothing is live during the build.)
    'DAX':    0.0000,  # PAUSED (was 0.0025) — ZTT Gold-only freeze
    'NDX':    0.0000,  # PAUSED (was 0.0015) — ZTT Gold-only freeze
    'GBPUSD': 0.0000,  # PAUSED (was 0.0020) — ZTT Gold-only freeze
    'USDJPY': 0.0000,  # paper-only; excluded from live portfolio
}


def _normalize_symbol_for_cap(symbol: Optional[str]) -> Optional[str]:
    """Normalize a symbol identifier to match SYMBOL_RISK_CAP keys.

    Accepts:
      - Yahoo FX (`GBPUSD=X`, `USDJPY=X`)
      - OANDA FX (`GBP_USD`, `USD_JPY`)
      - Plain FX (`GBPUSD`, `gbpusd`)
      - Futures / index tickers: `GC=F` → GOLD, `^IXIC` → NDX, `^GDAXI` → DAX
    """
    if symbol is None:
        return None
    s = symbol.strip().upper()
    # Map the non-FX tickers first
    ticker_map = {
        'GC=F': 'GOLD', 'XAUUSD': 'GOLD', 'XAU_USD': 'GOLD', 'XAUUSD=X': 'GOLD',
        '^IXIC': 'NDX', 'NAS100_USD': 'NDX', 'NAS100': 'NDX',
        '^GDAXI': 'DAX', 'DE30_EUR': 'DAX', 'DE40_EUR': 'DAX', 'GER40': 'DAX',
    }
    if s in ticker_map:
        return ticker_map[s]
    # FX fallback: strip Yahoo suffix + OANDA underscore
    return s.replace('=X', '').replace('_', '')


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
    asset_class: str = ''                 # 2026-07-02 audit: when set, slippage is
                                          #   classified by ASSET, not price bracket
                                          #   (price brackets misfile early-window NDX
                                          #   bars <=5000 as Gold, ~10x under-cost, and
                                          #   will misfile Gold >5000 as an index)


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
    config = RiskConfig(risk_per_trade=effective_risk, asset_class=asset_class)
    
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
    
    # Per-asset slippage multipliers (× config.slippage_pips). 2026-07-02 audit:
    # replaces price-bracket classification, which misfiled early-window NDX
    # bars (<=5000 -> Gold bracket, ~10x under-cost) and would misfile Gold
    # once it trades >5000 (~10x OVER-cost). Values preserve the R7-recal
    # intent: indices 0.75pt/side, Gold $0.075, forex 0.000075.
    SLIP_MULT_BY_ASSET = {
        'indices': 1.0,
        'gold': 0.1,
        'commodity': 0.1,
        'forex': 0.0001,
        'stocks': 0.01,
    }

    def apply_slippage(self, entry_price: float, direction: str) -> float:
        """Apply slippage tax to entry price.

        Round 5 council (Y1): NASDAQ/DAX were under-costed 3-13x under the
        old `entry_price > 1000` bracket. 2026-07-02 audit: classification is
        now by config.asset_class when available (price drifts across a 10Y
        window; asset identity doesn't). Price brackets remain only as the
        fallback for legacy callers that never set asset_class (and crypto,
        whose wide price range the brackets were tuned for).
        """
        direction = normalize_direction(direction)
        mult = self.SLIP_MULT_BY_ASSET.get(self.config.asset_class)
        if mult is None:
            # Legacy price-bracket fallback (pre-audit behaviour)
            if entry_price > 5000:
                mult = 1.0       # Indices (NDX/DAX): 0.75 pt slip post R7 recal
            elif entry_price > 1000:
                mult = 0.1       # Gold: $0.075 slip post R7 recal
            elif entry_price > 10:
                mult = 0.01      # Stocks / low-priced indices
            elif entry_price > 0.01:
                mult = 0.0001    # Forex: 0.000075 price units post R7 recal
            else:
                mult = 0.000001  # Sub-penny assets
        slip = self.config.slippage_pips * mult
        
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
