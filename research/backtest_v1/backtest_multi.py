import random
import pandas as pd

# CONFIG
INITIAL_CAPITAL = 10_000
FEE_RATE = 0.0004
SLIPPAGE_PCT = 0.10
MAX_DRAWDOWN = 0.30
COOLDOWN_CANDLES = 15
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# SYMBOL CONFIG
symbols_config = {
    "BTC": {"risk_pct": 0.15, "file": "../../data/BTC_USDT_15m.csv"},
    "ETH": {"risk_pct": 0.25, "file": "../../data/ETH_USDT_15m.csv"},
    "BNB": {"risk_pct": 0.05, "file": "../../data/BNB_USDT_15m.csv"},
}

# LOAD DATA
data = {}
for symbol, config in symbols_config.items():
    df = (
        pd.read_csv(config["file"], parse_dates=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    data[symbol] = df.set_index("timestamp")

common_index = set.intersection(*[set(df.index) for df in data.values()])
common_index = sorted(common_index)

# STATE
cash = INITIAL_CAPITAL
positions = {symbol: {"qty": 0, "entry": None} for symbol in symbols_config}
equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0
trading_state = "ENABLED"
cooldown_remaining = 0


# SIGNAL PROVIDER
class SignalProvider:
    def get_signal(self, symbol, timestamp):
        return random.choice(["LONG", "FLAT"])


signal_provider = SignalProvider()

# BACKTEST LOOP
for ts in common_index:
    # Prices snapshot
    prices = {}
    ranges = {}

    for symbol, df in data.items():
        row = df.loc[ts]
        prices[symbol] = row["close"]
        ranges[symbol] = max(row["high"] - row["low"], 1e-8)

    # Equity calculation
    equity = cash
    for symbol, pos in positions.items():
        equity += pos["qty"] * prices[symbol]

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
        for symbol, pos in positions.items():
            if pos["qty"] > 0:
                exit_price = prices[symbol] - ranges[symbol] * SLIPPAGE_PCT
                value = pos["qty"] * exit_price
                fee = value * FEE_RATE
                cash += value - fee
                positions[symbol] = {"qty": 0.0, "entry": None}

        if cooldown_remaining <= 0:
            trading_state = "ENABLED"
        continue

    # Process exits
    for symbol, pos in positions.items():
        signal = signal_provider.get_signal(symbol, ts)

        if pos["qty"] > 0 and signal == "FLAT":
            exit_price = prices[symbol] - ranges[symbol] * SLIPPAGE_PCT
            value = pos["qty"] * exit_price
            fee = value * FEE_RATE
            cash += value - fee
            positions[symbol] = {"qty": 0.0, "entry": None}

    # Process entries
    for symbol, cfg in symbols_config.items():
        pos = positions[symbol]
        signal = signal_provider.get_signal(symbol, ts)

        if pos["qty"] == 0 and signal == "LONG":
            position_value = equity * cfg["risk_pct"]

            if cash < position_value:
                continue  # not enough capital

            entry_price = prices[symbol] + ranges[symbol] * SLIPPAGE_PCT
            qty = position_value / entry_price
            fee = position_value * FEE_RATE

            cash -= position_value + fee
            positions[symbol] = {"qty": qty, "entry": entry_price}

# RESULTS
print(f"Initial Capital: {INITIAL_CAPITAL}")
print(f"Final Equity: {round(equity_curve[-1], 2)}")
print(f"Max Drawdown: {round(max_dd_seen * 100, 2)} %")
print(f"Trading State at End: {trading_state}")
print(f"Symbols traded: {list(symbols_config.keys())}")
