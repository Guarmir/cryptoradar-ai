
import time
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
)
from typing import Any, Optional

from app.early_movement.early_movement_analyzer import (
    EarlyMovementAnalyzer,
)
from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)
from app.services.market_data_service import (
    get_chart_data,
)


ChartLoader = Callable[
    [str, int],
    Mapping[str, Any],
]

Clock = Callable[[], float]


class EarlyMovementScannerDeepAnalyzer:
    DEFAULT_CHART_DAYS = 7
    DEFAULT_MAX_CHART_AGE_SECONDS = 2 * 60 * 60

    def __init__(
        self,
        *,
        analyzer: Optional[
            EarlyMovementAnalyzer
        ] = None,
        chart_loader: Optional[
            ChartLoader
        ] = None,
        chart_days: int = DEFAULT_CHART_DAYS,
        max_chart_age_seconds: Optional[
            float
        ] = None,
        clock: Optional[Clock] = None,
    ) -> None:
        if chart_days < 1:
            raise ValueError(
                "O período do gráfico deve ser "
                "maior que zero."
            )

        if (
            max_chart_age_seconds is not None
            and max_chart_age_seconds <= 0
        ):
            raise ValueError(
                "A idade máxima do gráfico deve "
                "ser maior que zero."
            )

        self._analyzer = (
            analyzer
            or EarlyMovementAnalyzer()
        )

        self._chart_loader = (
            chart_loader
            or get_chart_data
        )

        self._chart_days = chart_days
        self._max_chart_age_seconds = (
            max_chart_age_seconds
        )
        self._clock = clock or time.time

    def analyze_candidates(
        self,
        candidates: Iterable[
            EarlyMovementScannerCandidate
        ],
    ) -> tuple[
        EarlyMovementScannerAnalysisResult,
        ...,
    ]:
        results: list[
            EarlyMovementScannerAnalysisResult
        ] = []

        for candidate in candidates:
            results.append(
                self._analyze_candidate(
                    candidate,
                )
            )

        return tuple(
            results,
        )

    def _analyze_candidate(
        self,
        candidate: EarlyMovementScannerCandidate,
    ) -> EarlyMovementScannerAnalysisResult:
        try:
            chart_data = self._chart_loader(
                candidate.coin_id,
                self._chart_days,
            )
        except Exception:
            return EarlyMovementScannerAnalysisResult(
                candidate=candidate,
                error="chart_load_failed",
            )

        if not isinstance(
            chart_data,
            Mapping,
        ):
            return EarlyMovementScannerAnalysisResult(
                candidate=candidate,
                error="invalid_chart_data",
            )

        if not self._has_prices(
            chart_data,
        ):
            return EarlyMovementScannerAnalysisResult(
                candidate=candidate,
                error="chart_data_unavailable",
            )

        if (
            self._max_chart_age_seconds is not None
            and not self._is_chart_fresh(
                chart_data,
            )
        ):
            return EarlyMovementScannerAnalysisResult(
                candidate=candidate,
                error="chart_data_stale",
            )

        try:
            analysis = self._analyzer.analyze(
                chart_data,
                liquidity_score=(
                    candidate.liquidity.score
                ),
            )
        except Exception:
            return EarlyMovementScannerAnalysisResult(
                candidate=candidate,
                chart_available=True,
                error="analysis_failed",
            )

        return EarlyMovementScannerAnalysisResult(
            candidate=candidate,
            analysis=analysis,
            chart_available=True,
        )

    def _is_chart_fresh(
        self,
        chart_data: Mapping[str, Any],
    ) -> bool:
        prices = chart_data.get("prices")

        if not isinstance(
            prices,
            (list, tuple),
        ):
            return False

        timestamps = []

        for point in prices:
            if not isinstance(
                point,
                (list, tuple),
            ):
                continue

            if len(point) < 2:
                continue

            timestamp = point[0]

            if (
                isinstance(timestamp, bool)
                or not isinstance(
                    timestamp,
                    (int, float),
                )
            ):
                continue

            timestamps.append(
                float(timestamp),
            )

        if not timestamps:
            return False

        latest_timestamp_seconds = (
            max(timestamps) / 1000.0
        )

        age_seconds = (
            self._clock()
            - latest_timestamp_seconds
        )

        return (
            0 <= age_seconds
            <= self._max_chart_age_seconds
        )

    @staticmethod
    def _has_prices(
        chart_data: Mapping[
            str,
            Any,
        ],
    ) -> bool:
        prices = chart_data.get(
            "prices",
        )

        return (
            isinstance(
                prices,
                (list, tuple),
            )
            and len(prices) > 0
        )
