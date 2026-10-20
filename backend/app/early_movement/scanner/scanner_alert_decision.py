
from dataclasses import dataclass

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_early_observation_evaluator import (
    EarlyMovementScannerEarlyObservationEvaluator,
)
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
    DEFAULT_MIN_OBSERVATION_SCORE = 70.0
    DEFAULT_MAX_ALERTS = 3

    ALERTABLE_STATES = (
        EarlyMovementState.OBSERVATION,
        EarlyMovementState.EARLY_MOVEMENT,
        EarlyMovementState.CONFIRMED_MOVEMENT,
    )

    def __init__(
        self,
        *,
        min_relevance_score: float = DEFAULT_MIN_RELEVANCE_SCORE,
        min_observation_score: float = DEFAULT_MIN_OBSERVATION_SCORE,
        max_alerts: int = DEFAULT_MAX_ALERTS,
        enable_early_observation: bool = False,
    ) -> None:
        if max_alerts < 1:
            raise ValueError(
                "O limite de alertas deve ser maior que zero."
            )

        self._min_relevance_score = min_relevance_score
        self._min_observation_score = min_observation_score
        self._max_alerts = max_alerts
        self._enable_early_observation = enable_early_observation

        self._early_observation_evaluator = (
            EarlyMovementScannerEarlyObservationEvaluator()
        )

    def decide(
        self,
        scan_result: EarlyMovementScannerRunResult,
    ) -> EarlyMovementScannerAlertDecision:
        alertable_results: list[
            EarlyMovementScannerRankedResult
        ] = []

        for result in scan_result.ranked_results:
            if result.state not in self.ALERTABLE_STATES:
                continue

            if not self._is_alertable(result):
                continue

            alertable_results.append(result)

            if len(alertable_results) >= self._max_alerts:
                break

        selected_results = tuple(alertable_results)

        return EarlyMovementScannerAlertDecision(
            should_alert=bool(selected_results),
            results=selected_results,
        )

    def _is_alertable(
        self,
        result: EarlyMovementScannerRankedResult,
    ) -> bool:
        if result.relevance_score < self._min_relevance_score:
            return False

        if result.state != EarlyMovementState.OBSERVATION:
            return True

        if result.relevance_score >= self._min_observation_score:
            return True

        if not self._enable_early_observation:
            return False

        analysis = result.result.analysis

        if analysis is None:
            return False

        return self._early_observation_evaluator.is_relevant(
            analysis.evidence
        )
