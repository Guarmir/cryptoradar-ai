from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementState,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturityLevel,
)


ExtremeMovementObservationChange = Literal[
    "new_observation",
    "strengthening",
    "weakening",
    "direction_change",
    "stable",
]


@dataclass(frozen=True)
class ExtremeMovementObservationRecord:
    observed_at: datetime

    coin_id: str
    symbol: str
    name: str

    state: ExtremeMovementState
    direction: str

    relevance_score: float
    supporting_evidence_count: int

    maturity_level: ExtremeMovementMaturityLevel

    observation_change: ExtremeMovementObservationChange