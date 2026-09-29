from dataclasses import dataclass

from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


@dataclass(frozen=True)
class EarlyMovementScannerAlertDecision:
    should_alert: bool
    results: tuple[
        EarlyMovementScannerRankedResult,
        ...,
    ]


class EarlyMovementScannerAlertDecisionMaker:
    DEFAULT_MIN_RELEVANCE_SCORE = 0.0
    DEFAULT_MAX_ALERTS = 3

    def __init__(
        self,
        *,
        min_relevance_score: float = (
            DEFAULT_MIN_RELEVANCE_SCORE
        ),
        max_alerts: int = DEFAULT_MAX_ALERTS,
    ) -> None:
        if max_alerts < 1:
            raise ValueError(
                "O limite de alertas deve ser "
                "maior que zero."
            )

        self._min_relevance_score = (
            min_relevance_score
        )
        self._max_alerts = max_alerts

    def decide(
        self,
        scan_result: EarlyMovementScannerRunResult,
    ) -> EarlyMovementScannerAlertDecision:
        alertable_results = tuple(
            result
            for result in scan_result.ranked_results
            if (
                result.state is not None
                and result.relevance_score
                >= self._min_relevance_score
            )
        )[
            : self._max_alerts
        ]

        return EarlyMovementScannerAlertDecision(
            should_alert=bool(
                alertable_results
            ),
            results=alertable_results,
        )