# type: ignore
from dataclasses import dataclass


@dataclass
class PortfolioRisk:
    max_risk: float
    used_risk: float = 0.0

    def remaining_risk(self) -> float:
        return max(self.max_risk - self.used_risk, 0.0)

    def allocate(self, requested_risk: float) -> float:
        applied = min(requested_risk, self.remaining_risk())
        if applied > 0:
            self.used_risk += applied
        return applied

    def release(self, risk_pct: float):
        self.used_risk = max(self.used_risk - risk_pct, 0.0)
