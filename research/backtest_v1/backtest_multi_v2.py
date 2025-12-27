import random
import pandas as pd

# CONFIG
INITIAL_CAPITAL = 10_000
FEE_RATE = 0.0004
SLIPPAGE_PCT = 0.10
PORTFOLIO_MAX_RISK = 0.40
MAX_DRAWDOWN = 0.30
COOLDOWN_CANDLES = 15
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# SYMBOL CONFIG
symbols_config = {
    "BTC": {"risk_pct": 0.15, "file": "../../data/BTC_USDT_15m.csv"},
    "ETH": {"risk_pct": 0.10, "file": "../../data/ETH_USDT_15m.csv"},
    "BNB": {"risk_pct": 0.05, "file": "../../data/BNB_USDT_15m.csv"},
}

# LOAD DATA
data = {}
for symbol, cfg in symbols_config.items():
    df = (
        pd.read_csv(cfg["file"], parse_dates=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    data[symbol] = df.set_index("timestamp")

common_index = sorted(set.intersection(*[set(df.index) for df in data.values()]))

# STATE
cash = INITIAL_CAPITAL
positions = {s: {"qty": 0.0, "entry": None, "risk_pct": 0.0} for s in symbols_config}
equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0
trading_state = "ENABLED"
cooldown_remaining = 0
used_risk_pct = 0.0


# SIGNAL PROVIDER
class SignalProvider:
    def get_signal(self, symbol, ts):
        return random.choice(["LONG", "FLAT"])


signal_provider = SignalProvider()

# BACKTEST LOOP
for ts in common_index:
    prices = {}
    ranges = {}
    for s, df in data.items():
        row = df.loc[ts]
        prices[s] = row["close"]
        ranges[s] = max(row["high"] - row["low"], 1e-8)

    # Equity calculation
    equity = cash + sum(p["qty"] * prices[s] for s, p in positions.items())
    equity_curve.append(equity)

    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity
    max_dd_seen = max(max_dd_seen, drawdown)

    # Risk state
    if drawdown >= MAX_DRAWDOWN and trading_state == "ENABLED":
        trading_state = "COOLDOWN"
        cooldown_remaining = COOLDOWN_CANDLES

    if trading_state == "COOLDOWN":
        cooldown_remaining -= 1
        # Force exit all positions
        for s, p in positions.items():
            if p["qty"] > 0:
                exit_price = prices[s] - ranges[s] * SLIPPAGE_PCT
                value = p["qty"] * exit_price
                fee = value * FEE_RATE
                cash += value - fee
                used_risk_pct -= p["risk_pct"]
                positions[s] = {"qty": 0.0, "entry": None, "risk_pct": 0.0}

        if cooldown_remaining <= 0:
            trading_state = "ENABLED"
        continue

    # Process exits
    for s, p in positions.items():
        if p["qty"] > 0 and signal_provider.get_signal(s, ts) == "FLAT":
            exit_price = prices[s] - ranges[s] * SLIPPAGE_PCT
            value = p["qty"] * exit_price
            fee = value * FEE_RATE
            cash += value - fee
            used_risk_pct -= p["risk_pct"]
            positions[s] = {"qty": 0.0, "entry": None, "risk_pct": 0.0}

    # Process entries
    remaining_risk = PORTFOLIO_MAX_RISK - used_risk_pct

    for s, cfg in symbols_config.items():
        if remaining_risk <= 0:
            break

        if positions[s]["qty"] == 0 and signal_provider.get_signal(s, ts) == "LONG":
            requested = cfg["risk_pct"]
            applied = min(requested, remaining_risk)

            if applied <= 0:
                continue

            position_value = equity * applied
            entry_price = prices[s] + ranges[s] * SLIPPAGE_PCT
            qty = position_value / entry_price
            fee = position_value * FEE_RATE

            if cash < position_value + fee:
                continue

            cash -= position_value + fee
            used_risk_pct += applied
            remaining_risk -= applied

            positions[s] = {
                "qty": qty,
                "entry": entry_price,
                "risk_pct": applied,
            }

# RESULTS
print(f"Initial Capital: {INITIAL_CAPITAL}")
print(f"Final Equity: {round(equity_curve[-1], 2)}")
print(f"Max Drawdown: {round(max_dd_seen * 100, 2)} %")
print(f"Used Risk at End: {round(used_risk_pct * 100, 2)} %")
print(f"Trading State at End: {trading_state}")
print(f"Symbols traded: {list(symbols_config.keys())}")
