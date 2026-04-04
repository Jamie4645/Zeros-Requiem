"""
Backtest Runner — lightweight backtesting engine for pipeline-generated strategies.
Each strategy file has entry_signal(), exit_signal(), position_size() functions.

Usage:
    python -m strategy_pipeline.backtesting.bt_runner --strategy output/strategies/strategy_001.py --data data.csv
"""

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd


@dataclass
class TradeRecord:
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    position_size: float
    direction: str
    pnl: float
    pnl_pct: float
    hold_bars: int
    exit_reason: str


@dataclass
class BacktestResults:
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_hold_bars: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    trades: list = field(default_factory=list)
    equity_curve: Optional[pd.Series] = None


class BacktestRunner:
    def __init__(self, initial_capital=100_000, commission_pct=0.001, slippage_pct=0.0005):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def load_strategy(self, strategy_path):
        if not os.path.exists(strategy_path):
            raise FileNotFoundError(f"Strategy file not found: {strategy_path}")
        spec = importlib.util.spec_from_file_location("strategy", strategy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in ["entry_signal", "exit_signal", "STRATEGY_META"]:
            if not hasattr(module, attr):
                raise AttributeError(f"Strategy missing: {attr}")
        return module

    def run(self, strategy_path, df, risk_pct=0.01, params=None):
        strategy = self.load_strategy(strategy_path)
        meta = strategy.STRATEGY_META
        strategy_name = meta.get("name", os.path.basename(strategy_path))

        df = df.copy()
        df.columns = df.columns.str.lower()

        if hasattr(strategy, "compute_indicators"):
            df = strategy.compute_indicators(df, params)

        entries = strategy.entry_signal(df, params)
        exits = strategy.exit_signal(df, params)

        trades = []
        capital = self.initial_capital
        equity_curve = [capital]
        in_position = False
        entry_price = entry_idx = pos_size = 0

        for i in range(1, len(df)):
            if not in_position and entries.iloc[i]:
                entry_price = df["close"].iloc[i] * (1 + self.slippage_pct)
                stop = (strategy.get_stop_loss(df, i, params)
                        if hasattr(strategy, "get_stop_loss")
                        else entry_price * 0.98)
                if hasattr(strategy, "position_size"):
                    pos_size = strategy.position_size(capital, entry_price, stop, risk_pct)
                else:
                    price_risk = abs(entry_price - stop)
                    pos_size = (capital * risk_pct / price_risk) if price_risk > 0 else 0
                pos_size = min(pos_size, capital / entry_price)
                if pos_size > 0:
                    in_position = True
                    entry_idx = i
                    capital -= pos_size * entry_price * self.commission_pct

            elif in_position and exits.iloc[i]:
                exit_price = df["close"].iloc[i] * (1 - self.slippage_pct)
                pnl = (exit_price - entry_price) * pos_size
                pnl -= pos_size * exit_price * self.commission_pct
                capital += pnl
                trades.append(TradeRecord(
                    entry_date=str(df.index[entry_idx]),
                    exit_date=str(df.index[i]),
                    entry_price=entry_price, exit_price=exit_price,
                    position_size=pos_size, direction="long",
                    pnl=pnl, pnl_pct=(exit_price - entry_price) / entry_price,
                    hold_bars=i - entry_idx, exit_reason="signal",
                ))
                in_position = False

            equity_curve.append(
                capital if not in_position
                else capital + (df["close"].iloc[i] - entry_price) * pos_size
            )

        equity_series = pd.Series(equity_curve)
        if not trades:
            return BacktestResults(
                strategy_name=strategy_name,
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, total_pnl=0, total_return_pct=0,
                max_drawdown_pct=0, sharpe_ratio=0, profit_factor=0,
                avg_win=0, avg_loss=0, avg_hold_bars=0,
                max_consecutive_wins=0, max_consecutive_losses=0,
                trades=[], equity_curve=equity_series,
            )

        pnls = [t.pnl for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        peak = equity_series.expanding().max()
        max_dd = ((equity_series - peak) / peak).min()
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
        gross_losses = abs(sum(losses)) if losses else 1
        pf = (sum(wins) / gross_losses) if gross_losses > 0 else float("inf")

        max_w = max_l = curr_w = curr_l = 0
        for p in pnls:
            if p > 0:
                curr_w += 1; curr_l = 0; max_w = max(max_w, curr_w)
            else:
                curr_l += 1; curr_w = 0; max_l = max(max_l, curr_l)

        return BacktestResults(
            strategy_name=strategy_name,
            total_trades=len(trades), winning_trades=len(wins), losing_trades=len(losses),
            win_rate=len(wins)/len(trades), total_pnl=sum(pnls),
            total_return_pct=(capital - self.initial_capital) / self.initial_capital,
            max_drawdown_pct=max_dd, sharpe_ratio=sharpe, profit_factor=pf,
            avg_win=np.mean(wins) if wins else 0,
            avg_loss=np.mean(losses) if losses else 0,
            avg_hold_bars=np.mean([t.hold_bars for t in trades]),
            max_consecutive_wins=max_w, max_consecutive_losses=max_l,
            trades=trades, equity_curve=equity_series,
        )

    def run_all(self, strategies_dir, df, risk_pct=0.01):
        results = {}
        for sf in sorted(f for f in os.listdir(strategies_dir) if f.endswith(".py")):
            path = os.path.join(strategies_dir, sf)
            try:
                result = self.run(path, df, risk_pct)
                results[sf] = result
                print(f"  {sf}: {result.total_trades} trades | "
                      f"WR: {result.win_rate:.1%} | Sharpe: {result.sharpe_ratio:.2f}")
            except Exception as e:
                print(f"  [ERROR] {sf}: {e}")
        return results

    @staticmethod
    def results_to_dataframe(results):
        rows = [{
            "strategy": r.strategy_name, "file": n, "trades": r.total_trades,
            "win_rate": r.win_rate, "total_pnl": r.total_pnl,
            "return_pct": r.total_return_pct, "max_drawdown": r.max_drawdown_pct,
            "sharpe": r.sharpe_ratio, "profit_factor": r.profit_factor,
        } for n, r in results.items()]
        return pd.DataFrame(rows).sort_values("sharpe", ascending=False)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--capital", type=float, default=100000)
    parser.add_argument("--risk", type=float, default=0.01)
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=True, index_col=0)
    result = BacktestRunner(initial_capital=args.capital).run(args.strategy, df, args.risk)
    print(f"\nStrategy: {result.strategy_name}")
    print(f"Trades: {result.total_trades} | Win Rate: {result.win_rate:.1%}")
    print(f"Return: {result.total_return_pct:.2%} | Sharpe: {result.sharpe_ratio:.2f}")
    print(f"Max DD: {result.max_drawdown_pct:.2%} | PF: {result.profit_factor:.2f}")
