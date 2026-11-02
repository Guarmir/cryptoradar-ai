
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

    @classmethod
    def from_result(
        cls,
        result: ExtremeMovementDiscoveryResult,
        *,
        observed_at: datetime | None = None,
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
        )
