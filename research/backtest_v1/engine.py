# type: ignore
import json
import pandas as pd
from pathlib import Path
from backtest.config import *
from backtest.signals import SignalProvider
from backtest.portfolio import PortfolioRisk
from backtest.execution import open_position, close_position
from backtest.data_loader import load_price_data
from backtest.metrics import TradeLog, equity_metrics, sharpe_and_cagr

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# LOAD DATA
data, common_index = load_price_data(symbols_config)
trade_log = TradeLog()

# STATE
cash = INITIAL_CAPITAL
positions = {s: {"qty": 0.0, "entry": None, "risk_pct": 0.0} for s in symbols_config}

equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0

trading_state = "ENABLED"
cooldown_remaining = 0

portfolio = PortfolioRisk(
    max_risk=PORTFOLIO_MAX_RISK,
    max_notional=MAX_PORTFOLIO_NOTIONAL,
    symbol_caps=SYMBOL_MAX_RISK,
)
portfolio.setup_buckets(RISK_BUCKETS)

# SIGNAL PROVIDER
signal_provider = SignalProvider()

# BACKTEST LOOP
for ts in common_index:
    prices = {}
    ranges = {}

    for s, df in data.items():
        row = df.loc[ts]
        prices[s] = row["close"]
        ranges[s] = max(row["high"] - row["low"], 1e-8)

    # ---- equity ----
    equity = cash + sum(p["qty"] * prices[s] for s, p in positions.items())
    equity_curve.append(equity)

    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity
    max_dd_seen = max(max_dd_seen, drawdown)

    # ---- drawdown risk ----
    if drawdown >= MAX_DRAWDOWN and trading_state == "ENABLED":
        trading_state = "COOLDOWN"
        cooldown_remaining = COOLDOWN_CANDLES

    # ---- cooldown ----
    if trading_state == "COOLDOWN":
        cooldown_remaining -= 1

        for s, p in positions.items():
            if p["qty"] > 0:
                exit_price = prices[s] - ranges[s] * SLIPPAGE_PCT
                value = p["qty"] * exit_price
                fee = value * FEE_RATE
                cash += value - fee

                portfolio.release(p["risk_pct"])
                positions[s] = {"qty": 0.0, "entry": None, "risk_pct": 0.0}

        if cooldown_remaining <= 0:
            trading_state = "ENABLED"
        continue

    # ---- exits ----
    for s, p in positions.items():
        if p["qty"] > 0 and signal_provider.get_signal(s, ts) == "FLAT":
            cash = close_position(
                cash,
                p["qty"],
                prices[s],
                ranges[s],
                FEE_RATE,
                SLIPPAGE_PCT,
            )

            portfolio.release(s, p["risk_pct"], p["notional"])
            positions[s] = {"qty": 0.0, "entry": None, "risk_pct": 0.0}
            trade_log.close(
                symbol=s,
                time=ts,
                price=prices[s],
            )

    # ---- entries ----
    for s, cfg in symbols_config.items():
        if portfolio.remaining_risk() <= 0:
            break

        if positions[s]["qty"] == 0 and signal_provider.get_signal(s, ts) == "LONG":
            requested = cfg["risk_pct"]
            applied = portfolio.allocate(
                symbol=s,
                requested_risk=requested,
                equity=equity,
                requested_notional=equity * requested,
            )

            if applied <= 0:
                continue

            result = open_position(
                cash,
                equity,
                prices[s],
                ranges[s],
                applied,
                FEE_RATE,
                SLIPPAGE_PCT,
            )

            if result is None:
                portfolio.release(applied)
                continue

            cash = result["cash"]
            positions[s] = {
                "qty": result["qty"],
                "entry": result["entry_price"],
                "risk_pct": applied,
                "notional": equity * applied,
            }
            trade_log.open(
                symbol=s,
                time=ts,
                price=result["entry_price"],
                qty=result["qty"],
            )


equity_metrics_result = equity_metrics(equity_curve)
risk_metrics_result = sharpe_and_cagr(equity_curve)
results = {
    "equity_metrics": equity_metrics_result,
    "risk_metrics": risk_metrics_result,
    "summary": {
        "initial_capital": INITIAL_CAPITAL,
        "final_equity": round(equity_curve[-1], 2),
        "max_drawdown_pct": round(max_dd_seen * 100, 2),
        "used_risk_pct": round(portfolio.used_risk * 100, 2),
        "trading_state": trading_state,
        "symbols": list(symbols_config.keys()),
        "total_trades": len(trade_log.results()),
    },
}

print("=== EQUITY METRICS ===")
for k, v in results["equity_metrics"].items():
    print(f"{k}: {v}")

print("=== RISK METRICS ===")
for k, v in results["risk_metrics"].items():
    print(f"{k}: {v}")


equity_df = pd.DataFrame(
    {
        "timestamp": common_index,
        "equity": equity_curve,
    }
)
equity_df.to_csv(OUTPUT_DIR / "equity_curve.csv", index=False)


trades = trade_log.results()

trades_df = pd.DataFrame(
    [
        {
            "symbol": t.symbol,
            "entry_time": t.entry_time,
            "entry_price": t.entry_price,
            "exit_time": t.exit_time,
            "exit_price": t.exit_price,
            "qty": t.qty,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
        }
        for t in trades
    ]
)

trades_df.to_csv(OUTPUT_DIR / "trades.csv", index=False)


with open(OUTPUT_DIR / "metrics.json", "w") as f:
    json.dump(results, f, indent=2)
