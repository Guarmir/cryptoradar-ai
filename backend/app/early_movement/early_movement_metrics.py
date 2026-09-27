from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementMetrics:
    price_acceleration: Optional[float] = None
    abnormal_volume_ratio: Optional[float] = None
    volatility_expansion: Optional[float] = None
    persistence_score: Optional[float] = None
    price_sample_count: int = 0
    volume_sample_count: int = 0