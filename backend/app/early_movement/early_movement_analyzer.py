from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.early_movement.early_movement_breakout_confirmation import (
    EarlyMovementBreakoutConfirmation,
)
from app.early_movement.early_movement_breakout_confirmation_detector import (
    EarlyMovementBreakoutConfirmationDetector,
)
from app.early_movement.early_movement_evaluator import EarlyMovementEvaluator
from app.early_movement.early_movement_evidence import EarlyMovementEvidence
from app.early_movement.early_movement_metric_extractor import (
    EarlyMovementMetricExtractor,
)
from app.early_movement.early_movement_metrics import EarlyMovementMetrics
from app.early_movement.early_movement_price_structure import (
    EarlyMovementPriceStructure,
)
from app.early_movement.early_movement_price_structure_detector import (
    EarlyMovementPriceStructureDetector,
)


@dataclass(frozen=True)
class EarlyMovementAnalysis:
    metrics: EarlyMovementMetrics
    price_structure: EarlyMovementPriceStructure
    breakout_confirmation: EarlyMovementBreakoutConfirmation
    evidence: EarlyMovementEvidence


class EarlyMovementAnalyzer:
    def __init__(
        self,
        *,
        metric_extractor: Optional[
            EarlyMovementMetricExtractor
        ] = None,
        price_structure_detector: Optional[
            EarlyMovementPriceStructureDetector
        ] = None,
        breakout_confirmation_detector: Optional[
            EarlyMovementBreakoutConfirmationDetector
        ] = None,
        evaluator: Optional[
            EarlyMovementEvaluator
        ] = None,
    ) -> None:
        self._metric_extractor = (
            metric_extractor
            or EarlyMovementMetricExtractor()
        )

        self._price_structure_detector = (
            price_structure_detector
            or EarlyMovementPriceStructureDetector()
        )

        self._breakout_confirmation_detector = (
            breakout_confirmation_detector
            or EarlyMovementBreakoutConfirmationDetector()
        )

        self._evaluator = (
            evaluator
            or EarlyMovementEvaluator()
        )

    def analyze(
        self,
        chart_data: Mapping[str, Any],
        *,
        liquidity_score: Optional[float] = None,
        support_break: Optional[bool] = None,
        resistance_break: Optional[bool] = None,
        retest_confirmed: Optional[bool] = None,
        false_breakout_risk: Optional[float] = None,
    ) -> EarlyMovementAnalysis:
        metrics = self._metric_extractor.extract(
            chart_data,
        )

        price_structure = (
            self._price_structure_detector.detect(
                chart_data,
            )
        )

        breakout_confirmation = (
            self._breakout_confirmation_detector.detect(
                chart_data,
            )
        )

        automatic_support_break = (
            price_structure.support_break
            or (
                breakout_confirmation.retest_confirmed
                and breakout_confirmation.breakout_direction
                == "down"
            )
        )

        automatic_resistance_break = (
            price_structure.resistance_break
            or (
                breakout_confirmation.retest_confirmed
                and breakout_confirmation.breakout_direction
                == "up"
            )
        )

        resolved_support_break = (
            automatic_support_break
            if support_break is None
            else support_break
        )

        resolved_resistance_break = (
            automatic_resistance_break
            if resistance_break is None
            else resistance_break
        )

        resolved_retest_confirmed = (
            breakout_confirmation.retest_confirmed
            if retest_confirmed is None
            else retest_confirmed
        )

        evidence = self._evaluator.evaluate(
            price_acceleration=(
                metrics.price_acceleration
            ),
            abnormal_volume_ratio=(
                metrics.abnormal_volume_ratio
            ),
            liquidity_score=liquidity_score,
            volatility_expansion=(
                metrics.volatility_expansion
            ),
            support_break=(
                resolved_support_break
            ),
            resistance_break=(
                resolved_resistance_break
            ),
            retest_confirmed=(
                resolved_retest_confirmed
            ),
            persistence_score=(
                metrics.persistence_score
            ),
            false_breakout_risk=(
                false_breakout_risk
            ),
        )

        return EarlyMovementAnalysis(
            metrics=metrics,
            price_structure=price_structure,
            breakout_confirmation=(
                breakout_confirmation
            ),
            evidence=evidence,
        )