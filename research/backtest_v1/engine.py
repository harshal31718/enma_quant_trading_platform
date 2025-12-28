# type: ignore
import pandas as pd
from backtest.config import *
from backtest.signals import SignalProvider
from backtest.portfolio import PortfolioRisk
from backtest.execution import open_position, close_position
from backtest.data_loader import load_price_data


# LOAD DATA
data, common_index = load_price_data(symbols_config)

# STATE
cash = INITIAL_CAPITAL
positions = {s: {"qty": 0.0, "entry": None, "risk_pct": 0.0} for s in symbols_config}

equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0

trading_state = "ENABLED"
cooldown_remaining = 0

portfolio = PortfolioRisk(max_risk=PORTFOLIO_MAX_RISK)

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

            portfolio.release(p["risk_pct"])
            positions[s] = {"qty": 0.0, "entry": None, "risk_pct": 0.0}

    # ---- entries ----
    for s, cfg in symbols_config.items():
        if portfolio.remaining_risk() <= 0:
            break

        if positions[s]["qty"] == 0 and signal_provider.get_signal(s, ts) == "LONG":
            requested = cfg["risk_pct"]
            applied = portfolio.allocate(requested)

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
            }


# RESULTS
print(f"Initial Capital: {INITIAL_CAPITAL}")
print(f"Final Equity: {round(equity_curve[-1], 2)}")
print(f"Max Drawdown: {round(max_dd_seen * 100, 2)} %")
print(f"Used Risk at End: {round(portfolio.used_risk * 100, 2)} %")
print(f"Trading State at End: {trading_state}")
print(f"Symbols traded: {list(symbols_config.keys())}")
