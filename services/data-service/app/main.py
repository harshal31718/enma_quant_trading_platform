# type: ignore
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import ccxt
import pandas as pd
from pathlib import Path

app = FastAPI(title="Data Service", root_path="/api/data")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATA_DIR = Path("/app/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})


def fetch_ohlcv(symbol: str, timeframe: str = "15m", limit: int = 500):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


@app.get("/health")
def health():
    return {"service": "data-service", "status": "ok"}


@app.get("/historical")
def get_historical(
    symbol: str = Query(..., example="BTC/USDT"),
    timeframe: str = "15m",
    limit: int = 500,
):
    df = fetch_ohlcv(symbol, timeframe, limit)

    file_path = DATA_DIR / f"{symbol.replace('/', '_')}_{timeframe}.csv"
    df.to_csv(file_path, index=False)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "rows": len(df),
        "candles": df.to_dict(orient="records"),
    }
