from collections.abc import (
    Callable,
    Mapping,
)
from typing import Any

from app.services.market_data_service import (
    get_cached_chart_data,
    get_chart_data,
)


ChartLoader = Callable[
    [str, int],
    Mapping[str, Any],
]

CacheLoader = Callable[
    [str, int],
    Mapping[str, Any] | None,
]


class EarlyMovementScannerChartLoader:
    DEFAULT_REQUEST_BUDGET = 4

    def __init__(
        self,
        *,
        chart_loader: ChartLoader = get_chart_data,
        cache_loader: CacheLoader = (
            get_cached_chart_data
        ),
        request_budget: int = (
            DEFAULT_REQUEST_BUDGET
        ),
    ) -> None:
        if request_budget < 1:
            raise ValueError(
                "O orçamento de aquisições deve ser "
                "maior que zero."
            )

        self._chart_loader = chart_loader
        self._cache_loader = cache_loader
        self._request_budget = request_budget
        self._request_count = 0

    def __call__(
        self,
        coin_id: str,
        days: int,
    ) -> Mapping[str, Any]:
        cached = self._cache_loader(
            coin_id,
            days,
        )

        if cached is not None:
            return cached

        if (
            self._request_count
            >= self._request_budget
        ):
            return {
                "prices": [],
            }

        self._request_count += 1

        return self._chart_loader(
            coin_id,
            days,
        )

    def reset_budget(
        self,
    ) -> None:
        self._request_count = 0