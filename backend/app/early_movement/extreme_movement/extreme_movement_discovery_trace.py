
from dataclasses import dataclass
from datetime import datetime, timezone

from app.early_movement.extreme_movement.extreme_movement_discovery_runner import (
    ExtremeMovementDiscoveryResult,
)


@dataclass(frozen=True)
class ExtremeMovementDiscoveryTrace:
    observed_at: datetime
    universe_size: int
    candidate_count: int
    analyzed_count: int
    excluded_count: int
    selected_coin_ids: tuple[str, ...]
    submitted_coin_ids: tuple[str, ...]
    not_submitted_coin_ids: tuple[str, ...]

    
    experimental_status: str = "not_available"
    experimental_coin_ids: tuple[str, ...] = ()
    experimental_only_coin_ids: tuple[str, ...] = ()
    common_coin_ids: tuple[str, ...] = ()
    experimental_priorities: tuple = ()


   
    @classmethod
    def from_result(
        cls,
        result: ExtremeMovementDiscoveryResult,
        *,
        observed_at: datetime | None = None,
        experimental_comparison=None,
        experimental_error: Exception | None = None,
    ) -> "ExtremeMovementDiscoveryTrace":
        timestamp = (
            observed_at
            if observed_at is not None
            else datetime.now(timezone.utc)
        )

        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                "observed_at precisa conter fuso horario."
            )

        if experimental_error is not None:
            experimental_status = "error"
        elif experimental_comparison is not None:
            experimental_status = "completed"
        else:
            experimental_status = "not_available"

        comparison = (
            experimental_comparison
            if experimental_status == "completed"
            else None
        )

        priorities = (
            tuple(
                {
                    "coin_id": item.coin_id,
                    "score": item.score,
                    "state": item.state,
                    "direction": item.direction,
                    "evidence_count": item.evidence_count,
                }
                for item in comparison.experimental_priorities
            )
            if comparison is not None
            else ()
        )

        return cls(
            observed_at=timestamp,
            universe_size=result.universe_size,
            candidate_count=result.candidate_count,
            analyzed_count=result.analyzed_count,
            excluded_count=result.excluded_count,
            selected_coin_ids=result.selected_coin_ids,
            submitted_coin_ids=result.submitted_coin_ids,
            not_submitted_coin_ids=(
                result.not_submitted_coin_ids
            ),
            experimental_status=experimental_status,
            experimental_coin_ids=(
                comparison.experimental_coin_ids
                if comparison is not None
                else ()
            ),
            experimental_only_coin_ids=(
                comparison.experimental_only_coin_ids
                if comparison is not None
                else ()
            ),
            common_coin_ids=(
                comparison.common_coin_ids
                if comparison is not None
                else ()
            ),
            experimental_priorities=priorities,
        )

