from dataclasses import dataclass
from typing import Literal


ExtremeMovementState = Literal[
    "extreme_acceleration",
    "movement_pressure",
    "possible_reversal",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class ExtremeMovementAssessment:
    state: ExtremeMovementState
    direction: str
    relevance_score: float
    supporting_evidence_count: int