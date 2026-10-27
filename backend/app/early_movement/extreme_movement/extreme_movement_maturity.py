from dataclasses import dataclass
from typing import Literal

from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)


ExtremeMovementMaturityLevel = Literal[
    "early",
    "developing",
    "supported",
]


@dataclass(frozen=True)
class ExtremeMovementMaturity:
    level: ExtremeMovementMaturityLevel
    evidence_count: int
    relevance_score: float


class ExtremeMovementMaturityEvaluator:
    def evaluate(
        self,
        assessment: ExtremeMovementAssessment,
    ) -> ExtremeMovementMaturity:
        evidence_count = max(
            0,
            assessment.supporting_evidence_count,
        )

        relevance_score = max(
            0.0,
            min(
                100.0,
                assessment.relevance_score,
            ),
        )

        if (
            evidence_count >= 3
            and relevance_score >= 50.0
        ):
            level = "supported"

        elif (
            evidence_count >= 1
            or relevance_score >= 25.0
        ):
            level = "developing"

        else:
            level = "early"

        return ExtremeMovementMaturity(
            level=level,
            evidence_count=evidence_count,
            relevance_score=relevance_score,
        )