from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EarlyMovementBreakoutConfirmation:
    retest_confirmed: bool = False

    breakout_direction: Optional[str] = None
    breakout_level: Optional[float] = None
    breakout_price: Optional[float] = None
    retest_price: Optional[float] = None

    holding_breakout_level: bool = False

    sample_count: int = 0