from dataclasses import dataclass
from collections.abc import Iterable

from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_evaluator import (
    ExtremeMovementEvaluator,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
    ExtremeMovementMaturityEvaluator,
)
from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)


@dataclass(frozen=True)
class ExtremeMovementAnalysisEntry:
    coin_id: str
    symbol: str
    name: str
    assessment: ExtremeMovementAssessment
    maturity: ExtremeMovementMaturity | None = None


class ExtremeMovementAnalysisAdapter:
    def __init__(
        self,
        *,
        evaluator: ExtremeMovementEvaluator | None = None,
        maturity_evaluator: ExtremeMovementMaturityEvaluator | None = None,
    ) -> None:
        self._evaluator = (
            evaluator
            if evaluator is not None
            else ExtremeMovementEvaluator()
        )

        self._maturity_evaluator = (
            maturity_evaluator
            if maturity_evaluator is not None
            else ExtremeMovementMaturityEvaluator()
        )

    def adapt(
        self,
        results: Iterable[
            EarlyMovementScannerAnalysisResult
        ],
    ) -> tuple[ExtremeMovementAnalysisEntry, ...]:
        entries: list[ExtremeMovementAnalysisEntry] = []

        for result in results:
            if result.analysis is None:
                continue

            assessment = self._evaluator.evaluate(
                result.analysis.metrics
            )

            maturity = self._maturity_evaluator.evaluate(
                assessment
            )

            entries.append(
                ExtremeMovementAnalysisEntry(
                    coin_id=result.coin_id,
                    symbol=result.symbol,
                    name=result.name,
                    assessment=assessment,
                    maturity=maturity,
                )
            )

        return tuple(entries)