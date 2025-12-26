from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class Signal(BaseModel):
    symbol: str
    signal: Literal["LONG", "SHORT", "HOLD"]
    confidence: float
    timestamp: datetime
