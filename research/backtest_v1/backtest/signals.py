# type: ignore
import random
from backtest.config import RANDOM_SEED

random.seed(RANDOM_SEED)

class SignalProvider:
    
    # Mock signal provider.
    def get_signal(self, symbol: str, timestamp):
        return random.choice(["LONG", "FLAT"])
