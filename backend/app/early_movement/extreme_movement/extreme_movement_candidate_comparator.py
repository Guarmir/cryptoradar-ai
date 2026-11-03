
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.early_movement.extreme_movement.extreme_movement_candidate_priority import (
    ExtremeMovementCandidatePriority,
    ExtremeMovementCandidatePriorityEvaluator,
)
from app.early_movement.extreme_movement.extreme_movement_candidate_selector import (
    ExtremeMovementCandidateSelector,
)
from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateTracker,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


@dataclass(frozen=True)
class ExtremeMovementCandidateComparison:
    current_coin_ids: tuple[str, ...]
    experimental_coin_ids: tuple[str, ...]
    common_coin_ids: tuple[str, ...]
    experimental_only_coin_ids: tuple[str, ...]
    current_only_coin_ids: tuple[str, ...]
    experimental_priorities: tuple[
        ExtremeMovementCandidatePriority, ...
    ]


class ExtremeMovementCandidateComparator:
    def __init__(
        self,
        *,
        selector: ExtremeMovementCandidateSelector | None = None,
        tracker: ExtremeMovementCandidateTracker | None = None,
        evaluator: ExtremeMovementCandidatePriorityEvaluator | None = None,
    ) -> None:
        self._selector = (
            selector
            if selector is not None
            else ExtremeMovementCandidateSelector(
                min_absolute_change_24h=3.0,
                min_total_volume=100_000.0,
            )
        )
        self._tracker = (
            tracker
            if tracker is not None
            else ExtremeMovementCandidateTracker()
        )
        self._evaluator = (
            evaluator
            if evaluator is not None
            else ExtremeMovementCandidatePriorityEvaluator()
        )

    def compare(
        self,
        assets: Iterable[EarlyMovementScannerMarketAsset],
        *,
        limit: int = 20,
        observed_at: datetime | None = None,
    ) -> ExtremeMovementCandidateComparison:
        if limit < 1:
            raise ValueError("limit deve ser positivo.")

        market_assets = tuple(assets)

        current = self._selector.select(
            market_assets,
            limit=limit,
        )

        current_ids = tuple(
            item.coin_id for item in current
        )

        evolutions = self._tracker.observe(
            market_assets,
            observed_at=observed_at,
        )

        priorities = tuple(
            self._evaluator.evaluate(evolution)
            for evolution in evolutions
        )

        ranked = sorted(
            (
                item
                for item in priorities
                if item.evidence_count >= 2
                and item.score >= 20.0
            ),
            key=lambda item: (
                -item.score,
                item.coin_id,
            ),
        )

        experimental = tuple(ranked[:limit])

        experimental_ids = tuple(
            item.coin_id for item in experimental
        )

        current_set = set(current_ids)
        experimental_set = set(experimental_ids)

        return ExtremeMovementCandidateComparison(
            current_coin_ids=current_ids,
            experimental_coin_ids=experimental_ids,
            common_coin_ids=tuple(
                coin_id
                for coin_id in experimental_ids
                if coin_id in current_set
            ),
            experimental_only_coin_ids=tuple(
                coin_id
                for coin_id in experimental_ids
                if coin_id not in current_set
            ),
            current_only_coin_ids=tuple(
                coin_id
                for coin_id in current_ids
                if coin_id not in experimental_set
            ),
            experimental_priorities=experimental,
        )
