# type: ignore
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PortfolioRisk:
    max_risk: float
    used_risk: float = 0.0
    symbol_caps: Dict[str, float] = field(default_factory=dict)
    symbol_used: Dict[str, float] = field(default_factory=dict)
    bucket_caps: Dict[str, float] = field(default_factory=dict)
    bucket_used: Dict[str, float] = field(default_factory=dict)
    symbol_to_bucket: Dict[str, str] = field(default_factory=dict)

    max_notional: float = 1.0
    used_notional: float = 0.0

    def remaining_notional(self, equity: float) -> float:
        return max((self.max_notional * equity) - self.used_notional, 0.0)

    def remaining_risk(self) -> float:
        return max(self.max_risk - self.used_risk, 0.0)

    def remaining_symbol_risk(self, symbol: str) -> float:
        cap = self.symbol_caps.get(symbol)
        if cap is None:
            return self.remaining_risk()
        used = self.symbol_used.get(symbol, 0.0)
        return max(cap - used, 0.0)

    def setup_buckets(self, buckets: dict):
        for bucket, cfg in buckets.items():
            self.bucket_caps[bucket] = cfg["max_risk"]
            self.bucket_used[bucket] = 0.0
            for s in cfg["symbols"]:
                self.symbol_to_bucket[s] = bucket

    def remaining_bucket_risk(self, symbol: str) -> float:
        bucket = self.symbol_to_bucket.get(symbol)
        if bucket is None:
            return self.remaining_risk()
        return max(
            self.bucket_caps[bucket] - self.bucket_used.get(bucket, 0.0),
            0.0,
        )

    def allocate(
        self,
        symbol: str,
        requested_risk: float,
        equity: float,
        requested_notional: float,
    ) -> float:
        portfolio_room = self.remaining_risk()
        symbol_room = self.remaining_symbol_risk(symbol)
        notional_room = self.remaining_notional(equity)
        bucket_room = self.remaining_bucket_risk(symbol)

        applied = min(
            requested_risk,
            portfolio_room,
            symbol_room,
            bucket_room,
        )
        if notional_room <= 0:
            return 0.0

        applied_risk = min(requested_risk, portfolio_room, symbol_room)

        if applied_risk <= 0:
            return 0.0

        applied_notional = equity * applied_risk
        if applied_notional > notional_room:
            applied_risk = notional_room / equity

        if applied_risk > 0:
            self.used_risk += applied_risk
            self.used_notional += equity * applied_risk
            self.symbol_used[symbol] = self.symbol_used.get(symbol, 0.0) + applied_risk

        bucket = self.symbol_to_bucket.get(symbol)
        if bucket:
            self.bucket_used[bucket] += applied
        return applied_risk

    def release(self, symbol: str, risk_pct: float, notional: float):
        self.used_risk = max(self.used_risk - risk_pct, 0.0)
        self.used_notional = max(self.used_notional - notional, 0.0)
        bucket = self.symbol_to_bucket.get(symbol)
        if bucket:
            self.bucket_used[bucket] = max(
                self.bucket_used[bucket] - risk_pct, 0.0
            )
        if symbol in self.symbol_used:
            self.symbol_used[symbol] = max(self.symbol_used[symbol] - risk_pct, 0.0)
