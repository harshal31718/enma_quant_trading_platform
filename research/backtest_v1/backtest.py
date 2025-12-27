import random
import pandas as pd

# CONFIG --------------------
INITIAL_CAPITAL = 10_000
POSITION_SIZE = 1_000        # fixed $ per trade
FEE_RATE = 0.0004            # 0.04%
SEED = 42

random.seed(SEED)


# LOAD DATA ------------------
df = pd.read_csv(
    "../../data/BTC_USDT_15m.csv",
    parse_dates=["timestamp"]
).sort_values("timestamp").reset_index(drop=True)

# STATE ---------------------
cash = INITIAL_CAPITAL
position = 0.0
entry_price = None
equity_curve = []

peak_equity = INITIAL_CAPITAL
max_drawdown = 0.0

# MOCK SIGNAL ------------------
def mock_signal():
    return random.choice(["LONG", "FLAT"])

# BACKTEST LOOP --------------
for idx, row in df.iterrows():
    price = row['close']
    signal = mock_signal()

    # Entry LONG
    if signal == "LONG" and position == 0.0:
        position = POSITION_SIZE / price
        cost = POSITION_SIZE * FEE_RATE
        cash -= (POSITION_SIZE + cost)
        entry_price = price

    # Exit LONG
    elif signal == "FLAT" and position > 0.0:
        value = position * price
        cost = value * FEE_RATE
        cash += (value - cost)
        position = 0.0
        entry_price = None

    # Update equity
    equity = cash + (position * price)
    equity_curve.append(equity)

    # Update peak equity and drawdown
    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity
    max_drawdown = max(max_drawdown, drawdown)

# RESULTS ----------------
final_equity = cash + (position * df.iloc[-1]['close'])
print(f"Final Equity: ${final_equity:,.2f}")
print(f"Max Drawdown: {max_drawdown*100:,.2f}%")
print(f"Trades (approx): {equity_curve.count != 0}")