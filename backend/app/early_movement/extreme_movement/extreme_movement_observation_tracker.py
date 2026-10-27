from dataclasses import dataclass
from typing import Literal

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)


ObservationChange = Literal[
    "new_observation",
    "strengthening",
    "weakening",
    "direction_change",
    "stable",
]


@dataclass(frozen=True)
class ExtremeMovementObservation:
    coin_id: str
    change: ObservationChange
    previous: ExtremeMovementAnalysisEntry | None
    current: ExtremeMovementAnalysisEntry


class ExtremeMovementObservationTracker:
    MIN_RELEVANCE_CHANGE = 10.0

    MATURITY_RANK = {
        "early": 0,
        "developing": 1,
        "supported": 2,
    }

    def compare(
        self,
        previous: ExtremeMovementAnalysisEntry | None,
        current: ExtremeMovementAnalysisEntry,
    ) -> ExtremeMovementObservation:
        if previous is None:
            change = "new_observation"

        elif (
            previous.assessment.direction
            != current.assessment.direction
            and previous.assessment.direction != "neutral"
            and current.assessment.direction != "neutral"
        ):
            change = "direction_change"

        else:
            previous_maturity = self._maturity_rank(previous)
            current_maturity = self._maturity_rank(current)

            relevance_change = (
                current.assessment.relevance_score
                - previous.assessment.relevance_score
            )

            if current_maturity > previous_maturity:
                change = "strengthening"

            elif current_maturity < previous_maturity:
                change = "weakening"

            elif relevance_change >= self.MIN_RELEVANCE_CHANGE:
                change = "strengthening"

            elif relevance_change <= -self.MIN_RELEVANCE_CHANGE:
                change = "weakening"

            else:
                change = "stable"

        return ExtremeMovementObservation(
            coin_id=current.coin_id,
            change=change,
            previous=previous,
            current=current,
        )

    def _maturity_rank(
        self,
        entry: ExtremeMovementAnalysisEntry,
    ) -> int:
        if entry.maturity is None:
            return 0

        return self.MATURITY_RANK.get(
            entry.maturity.level,
            0,
        )