from dataclasses import dataclass
from typing import Any, Mapping, Optional

from app.early_movement.early_movement_evaluator import EarlyMovementEvaluator
from app.early_movement.early_movement_evidence import EarlyMovementEvidence
from app.early_movement.early_movement_metric_extractor import (
    EarlyMovementMetricExtractor,
)
from app.early_movement.early_movement_metrics import EarlyMovementMetrics


@dataclass(frozen=True)
class EarlyMovementAnalysis:
    metrics: EarlyMovementMetrics
    evidence: EarlyMovementEvidence


class EarlyMovementAnalyzer:
    def __init__(
        self,
        *,
        metric_extractor: Optional[
            EarlyMovementMetricExtractor
        ] = None,
        evaluator: Optional[
            EarlyMovementEvaluator
        ] = None,
    ) -> None:
        self._metric_extractor = (
            metric_extractor
            or EarlyMovementMetricExtractor()
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
        support_break: bool = False,
        resistance_break: bool = False,
        retest_confirmed: bool = False,
        false_breakout_risk: Optional[float] = None,
    ) -> EarlyMovementAnalysis:
        metrics = self._metric_extractor.extract(
            chart_data,
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
            support_break=support_break,
            resistance_break=resistance_break,
            retest_confirmed=retest_confirmed,
            persistence_score=(
                metrics.persistence_score
            ),
            false_breakout_risk=(
                false_breakout_risk
            ),
        )

        return EarlyMovementAnalysis(
            metrics=metrics,
            evidence=evidence,
        )