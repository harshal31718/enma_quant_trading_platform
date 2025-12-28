# type: ignore
# BACKTEST CONFIG

INITIAL_CAPITAL = 10_000
# Fees & execution
FEE_RATE = 0.0004
SLIPPAGE_PCT = 0.10
# Portfolio risk
PORTFOLIO_MAX_RISK = 0.40
# Risk control
MAX_DRAWDOWN = 0.30
COOLDOWN_CANDLES = 15
# Reproducibility       
RANDOM_SEED = 42

# SYMBOL CONFIG
symbols_config = {
    "BTC": {
        "risk_pct": 0.15,
        "file": "../../data/BTC_USDT_15m.csv",
    },
    "ETH": {
        "risk_pct": 0.10,
        "file": "../../data/ETH_USDT_15m.csv",
    },
    "BNB": {
        "risk_pct": 0.05,
        "file": "../../data/BNB_USDT_15m.csv",
    },
}
