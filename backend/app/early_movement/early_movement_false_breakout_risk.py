from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementFalseBreakoutRisk:
    score: Optional[float] = None
    applicable: bool = False

    breakout_direction: Optional[str] = None
    breakout_distance_percent: Optional[float] = None

    factors: tuple[str, ...] = ()