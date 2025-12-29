# type: ignore
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class Trade:
    symbol: str
    entry_time: object
    entry_price: float
    qty: float
    exit_time: Optional[object] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None

class TradeLog:
    def __init__(self):
        self.open_trades: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []

    def open(self, symbol, time, price, qty):
        self.open_trades[symbol] = Trade(
            symbol=symbol,
            entry_time=time,
            entry_price=price,
            qty=qty,
        )

    def close(self, symbol, time, price):
        trade = self.open_trades.pop(symbol, None)
        if trade is None:
            return

        trade.exit_time = time
        trade.exit_price = price
        trade.pnl = (price - trade.entry_price) * trade.qty
        trade.pnl_pct = (price / trade.entry_price - 1.0) * 100.0
        self.closed_trades.append(trade)

    def results(self):
        return self.closed_trades

def equity_metrics(equity_curve):
    equity = pd.Series(equity_curve)

    final_equity = equity.iloc[-1]
    returns_pct = (final_equity / equity.iloc[0] - 1) * 100

    peak = equity.cummax()
    drawdown = (peak - equity) / peak
    max_drawdown = drawdown.max() * 100

    return {
        "final_equity": round(final_equity, 2),
        "return_pct": round(returns_pct, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
    }

def sharpe_and_cagr(equity_curve, periods_per_year=365 * 24 * 4):
    """
    periods_per_year:
    - 15m candles ≈ 4 per hour * 24 * 365
    """
    equity = pd.Series(equity_curve)
    returns = equity.pct_change().dropna()

    if returns.std() == 0 or len(returns) < 2:
        sharpe = 0.0
    else:
        sharpe = (returns.mean() / returns.std()) * (periods_per_year ** 0.5)

    total_return = equity.iloc[-1] / equity.iloc[0]
    years = len(equity) / periods_per_year
    cagr = (total_return ** (1 / years) - 1) * 100 if years > 0 else 0.0

    return {
        "sharpe": round(sharpe, 3),
        "cagr_pct": round(cagr, 2),
    }
