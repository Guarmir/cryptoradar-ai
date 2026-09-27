from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementPriceStructure:
    current_price: Optional[float] = None

    support_level: Optional[float] = None
    resistance_level: Optional[float] = None

    support_break: bool = False
    resistance_break: bool = False

    support_break_distance_percent: Optional[float] = None
    resistance_break_distance_percent: Optional[float] = None

    sample_count: int = 0