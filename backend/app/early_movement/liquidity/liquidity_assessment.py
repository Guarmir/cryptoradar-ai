from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementLiquidityAssessment:
    score: Optional[float] = None

    total_volume: Optional[float] = None
    market_cap: Optional[float] = None

    volume_to_market_cap_ratio: Optional[float] = None

    available: bool = False

    factors: tuple[str, ...] = ()