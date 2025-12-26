from fastapi import FastAPI
from datetime import datetime, timedelta
from random import choice, random
from typing import List

from app.schema import Signal

app = FastAPI(
    title="ML Service",
    root_path="/api/ml"
)

SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
DIRECTIONS = ["LONG", "SHORT", "HOLD"]


@app.get("/health")
def health():
    return {"service": "ml-service", "status": "ok"}


@app.get("/signal", response_model=Signal)
def get_signal():
    return Signal(
        symbol=choice(SYMBOLS),
        signal=choice(DIRECTIONS),
        confidence=round(random(), 2),
        timestamp=datetime.utcnow()
    )


@app.get("/signals/mock", response_model=List[Signal])
def get_mock_signals():
    now = datetime.utcnow()
    signals = []
    for i in range(10):
        signals.append(
            Signal(
                symbol=choice(SYMBOLS),
                signal=choice(DIRECTIONS),
                confidence=round(random(), 2),
                timestamp=now - timedelta(minutes=i)
            )
        )
    return signals
