from collections.abc import Iterable

from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)
from app.early_movement.scanner.scanner_ranked_result import (
    EarlyMovementScannerRankedResult,
)


class EarlyMovementScannerResultRanker:
    DEFAULT_RESULT_LIMIT = 5

    _STATE_BASE_SCORE = {
        EarlyMovementState.NORMAL: 0.0,
        EarlyMovementState.OBSERVATION: 35.0,
        EarlyMovementState.EARLY_MOVEMENT: 60.0,
        EarlyMovementState.CONFIRMED_MOVEMENT: 55.0,
        EarlyMovementState.EXHAUSTION_OR_POSSIBLE_REVERSAL: 40.0,
    }

    def rank(
        self,
        results: Iterable[
            EarlyMovementScannerAnalysisResult
        ],
        *,
        limit: int = DEFAULT_RESULT_LIMIT,
    ) -> tuple[
        EarlyMovementScannerRankedResult,
        ...,
    ]:
        if limit < 1:
            raise ValueError(
                "O limite de resultados deve ser "
                "maior que zero."
            )

        scored: list[
            tuple[
                float,
                EarlyMovementScannerAnalysisResult,
            ]
        ] = []

        for result in results:
            analysis = result.analysis

            if analysis is None:
                continue

            evidence = analysis.evidence

            if (
                evidence.state
                == EarlyMovementState.NORMAL
            ):
                continue

            score = self._score(
                result,
                evidence,
            )

            scored.append(
                (
                    score,
                    result,
                )
            )

        scored.sort(
            key=self._sort_key,
        )

        ranked: list[
            EarlyMovementScannerRankedResult
        ] = []

        for index, (
            score,
            result,
        ) in enumerate(
            scored[:limit],
            start=1,
        ):
            ranked.append(
                EarlyMovementScannerRankedResult(
                    rank=index,
                    relevance_score=round(
                        score,
                        2,
                    ),
                    result=result,
                )
            )

        return tuple(
            ranked,
        )

    def _score(
        self,
        result: EarlyMovementScannerAnalysisResult,
        evidence: EarlyMovementEvidence,
    ) -> float:
        score = self._STATE_BASE_SCORE.get(
            evidence.state,
            0.0,
        )

        liquidity_score = (
            evidence.liquidity_score
        )

        if liquidity_score is None:
            liquidity_score = (
                result
                .candidate
                .liquidity
                .score
            )

        score += (
            self._normalized_score(
                liquidity_score,
                maximum_points=10.0,
            )
        )

        score += (
            self._normalized_score(
                evidence.persistence_score,
                maximum_points=10.0,
            )
        )

        score += (
            self._abnormal_volume_points(
                evidence.abnormal_volume_ratio,
            )
        )

        if evidence.retest_confirmed:
            score += 8.0

        if (
            evidence.support_break
            or evidence.resistance_break
        ):
            score += 5.0

        score -= (
            self._false_breakout_penalty(
                evidence.false_breakout_risk,
            )
        )

        return self._clamp(
            score,
        )

    @staticmethod
    def _normalized_score(
        value: float | None,
        *,
        maximum_points: float,
    ) -> float:
        if value is None:
            return 0.0

        normalized = max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

        return (
            normalized
            / 100.0
            * maximum_points
        )

    @staticmethod
    def _abnormal_volume_points(
        ratio: float | None,
    ) -> float:
        if ratio is None:
            return 0.0

        if ratio <= 1.0:
            return 0.0

        capped_ratio = min(
            ratio,
            3.0,
        )

        return (
            (
                capped_ratio
                - 1.0
            )
            / 2.0
            * 10.0
        )

    @staticmethod
    def _false_breakout_penalty(
        risk: float | None,
    ) -> float:
        if risk is None:
            return 0.0

        normalized = max(
            0.0,
            min(
                100.0,
                risk,
            ),
        )

        return (
            normalized
            / 100.0
            * 15.0
        )

    @staticmethod
    def _sort_key(
        item: tuple[
            float,
            EarlyMovementScannerAnalysisResult,
        ],
    ) -> tuple[
        float,
        int,
        str,
    ]:
        score, result = item

        market_cap_rank = (
            result
            .candidate
            .asset
            .market_cap_rank
        )

        if market_cap_rank is None:
            market_cap_rank = 1_000_000

        return (
            -score,
            market_cap_rank,
            result.coin_id,
        )

    @staticmethod
    def _clamp(
        score: float,
    ) -> float:
        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )