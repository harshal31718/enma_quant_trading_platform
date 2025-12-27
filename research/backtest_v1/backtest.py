import random
import pandas as pd

# CONFIG --------------------
INITIAL_CAPITAL = 10_000
FEE_RATE = 0.0004  # 0.04%
SLIPPAGE_PCT = 0.10  # 10%
RISK_PCT = 0.10  # 10% of capital per trade
MAX_DRAWDOWN = 0.3  # 30%
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# LOAD DATA ------------------
df = pd.read_csv(
    "../../data/BTC_USDT_15m.csv",
    parse_dates=["timestamp"]
).sort_values("timestamp").reset_index(drop=True)

# STATE ---------------------
cash = INITIAL_CAPITAL
position_qty = 0.0
entry_price = None

equity_curve = []
peak_equity = INITIAL_CAPITAL
max_dd_seen = 0.0
trading_enabled = True

# MOCK SIGNAL ------------------
def mock_signal():
    return random.choice(["LONG", "FLAT"])

# BACKTEST LOOP --------------
for idx, row in df.iterrows():
    open_p = row['open']
    high_p = row['high']
    low_p = row['low']
    close_p = row['close']
    
    candle_range = high_p - low_p
    slippage = candle_range * SLIPPAGE_PCT

    signal = mock_signal()

    # Entry POSITION
    if trading_enabled and position_qty == 0 and signal == "LONG":
        equity = cash
        position_value = equity * RISK_PCT

        entry_price = close_p + slippage
        position_qty = position_value / entry_price

        fee = position_value * FEE_RATE
        cash -= (position_value + fee)
    
    # Exit POSITION
    elif position_qty > 0 and signal == "FLAT":
        exit_price = close_p - slippage
        value = position_qty * exit_price

        fee = value * FEE_RATE
        cash += (value - fee)

        position_qty = 0.0
        entry_price = None

    # Update equity
    equity = cash + (position_qty * close_p)
    equity_curve.append(equity)

    # Update peak equity and drawdown
    peak_equity = max(peak_equity, equity)
    drawdown = (peak_equity - equity) / peak_equity
    max_dd_seen = max(max_dd_seen, drawdown)

# RESULTS ----------------
final_equity = cash + (position_qty * df.iloc[-1]['close'])
print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
print(f"Final Equity: ${final_equity:,.2f}")
print(f"Max Drawdown: {max_dd_seen*100:,.2f}%")
print(f"Trades (approx): {len(equity_curve)}")
print(f"Trading stopped due to drawdown limit: {not trading_enabled}")