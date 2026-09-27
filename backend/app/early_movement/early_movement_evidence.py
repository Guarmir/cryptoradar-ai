from dataclasses import dataclass
from typing import Optional

from app.early_movement.early_movement_state import EarlyMovementState


@dataclass(frozen=True)
class EarlyMovementEvidence:
    state: EarlyMovementState

    price_acceleration: Optional[float] = None
    abnormal_volume_ratio: Optional[float] = None
    liquidity_score: Optional[float] = None
    volatility_expansion: Optional[float] = None

    support_break: bool = False
    resistance_break: bool = False
    retest_confirmed: bool = False

    persistence_score: Optional[float] = None
    false_breakout_risk: Optional[float] = None

    reason: Optional[str] = None
    invalidation_reason: Optional[str] = None