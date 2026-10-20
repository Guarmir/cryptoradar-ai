
from collections.abc import Callable, Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True)
class ScannerChartLoaderStats:
    cache_hits: int
    acquisition_attempts: int
    budget_exhausted: int
    empty_results: int


class EarlyMovementScannerChartLoader:
    DEFAULT_REQUEST_BUDGET = 4

    def __init__(
        self,
        *,
        chart_loader: ChartLoader = get_chart_data,
        cache_loader: CacheLoader = get_cached_chart_data,
        request_budget: int = DEFAULT_REQUEST_BUDGET,
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
        self._cache_hits = 0
        self._budget_exhausted = 0
        self._empty_results = 0

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
            self._cache_hits += 1
            return cached

        if self._request_count >= self._request_budget:
            self._budget_exhausted += 1
            return {"prices": []}

        self._request_count += 1

        result = self._chart_loader(
            coin_id,
            days,
        )

        prices = result.get("prices")

        if not isinstance(prices, list) or not prices:
            self._empty_results += 1

        return result

    @property
    def stats(self) -> ScannerChartLoaderStats:
        return ScannerChartLoaderStats(
            cache_hits=self._cache_hits,
            acquisition_attempts=self._request_count,
            budget_exhausted=self._budget_exhausted,
            empty_results=self._empty_results,
        )

    def reset_budget(self) -> None:
        self._request_count = 0
        self._cache_hits = 0
        self._budget_exhausted = 0
        self._empty_results = 0
