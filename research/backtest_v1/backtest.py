import random
import pandas as pd

# CONFIG PHASE 3 --------------------
INITIAL_CAPITAL = 10_000
FEE_RATE = 0.0004  # 0.04%
SLIPPAGE_PCT = 0.10  # 10%
RISK_PCT = 0.10  # 10% of capital per trade
MAX_DRAWDOWN = 0.3  # 30%
COOLDOWN_CANDLES = 15
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# LOAD DATA ------------------
df = (
    pd.read_csv(  # type: ignore
        "../../data/BTC_USDT_15m.csv", parse_dates=["timestamp"]
    )
    .sort_values("timestamp")
    .reset_index(drop=True)
)

# STATE ---------------------
cash = INITIAL_CAPITAL
position_qty = 0.0
entry_price = None

equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0
trading_state = "ENABLED"
cooldown_remaining = 0


# MOCK SIGNAL ------------------
def mock_signal():
    return random.choice(["LONG", "FLAT"])


# BACKTEST LOOP --------------
for idx, row in df.iterrows():
    high = row["high"]
    low = row["low"]
    close = row["close"]

    candle_range = high - low
    slippage = candle_range * SLIPPAGE_PCT
    signal = mock_signal()

    # Handle cooldown
    if trading_state == "COOLDOWN":
        cooldown_remaining -= 1

        # Force exit if in position
        if position_qty > 0:
            exit_price = close - slippage
            value = position_qty * exit_price
            fee = value * FEE_RATE
            cash += value - fee
            position_qty = 0.0
            entry_price = None

        if cooldown_remaining <= 0:
            trading_state = "ENABLED"

    # Entry POSITION
    if trading_state == "ENABLED" and position_qty == 0 and signal == "LONG":
        position_value = cash * RISK_PCT
        entry_price = close + slippage
        position_qty = position_value / entry_price
        fee = position_value * FEE_RATE
        cash -= position_value + fee

    # Exit POSITION
    elif position_qty > 0 and signal == "FLAT":
        exit_price = close - slippage
        value = position_qty * exit_price
        fee = value * FEE_RATE
        cash += value - fee
        position_qty = 0.0
        entry_price = None

    # EQUITY & DRAWDOWN CALCULATION
    equity = cash + (position_qty * close)
    equity_curve.append(equity)  # type: ignore

    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity
    max_dd_seen = max(max_dd_seen, drawdown)

    if drawdown >= MAX_DRAWDOWN and trading_state == "ENABLED":
        trading_state = "COOLDOWN"
        cooldown_remaining = COOLDOWN_CANDLES
        position_qty = 0.0
        entry_price = None

# RESULTS ----------------
print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
print(f"Final Equity: ${cash:,.2f}")
print(f"Max Drawdown: {max_dd_seen*100:,.2f}%")
print(f"Trades (approx): {len(equity_curve)}")  # type: ignore
print(f"Trading state at End: {trading_state}")
