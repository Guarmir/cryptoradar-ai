import time
from collections.abc import (
    Callable,
    Mapping,
)
from typing import Any

from app.services.chart_request_pacer import (
    ChartRequestPacer,
)
from app.services.market_data_service import (
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

Sleeper = Callable[
    [float],
    None,
]


class ControlledChartLoader:
    def __init__(
        self,
        *,
        chart_loader: ChartLoader = get_chart_data,
        cache_loader: CacheLoader | None = None,
        pacer: ChartRequestPacer | None = None,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        self._chart_loader = chart_loader
        self._cache_loader = cache_loader
        self._pacer = (
            pacer
            or ChartRequestPacer()
        )
        self._sleeper = sleeper

    def __call__(
        self,
        coin_id: str,
        days: int,
    ) -> Mapping[str, Any]:
        cached = self._load_cached(
            coin_id,
            days,
        )

        if cached is not None:
            return cached

        self._wait_until_allowed()

        result = self._chart_loader(
            coin_id,
            days,
        )

        self._pacer.record_request()

        return result

    def _load_cached(
        self,
        coin_id: str,
        days: int,
    ) -> Mapping[str, Any] | None:
        if self._cache_loader is None:
            return None

        return self._cache_loader(
            coin_id,
            days,
        )

    def _wait_until_allowed(
        self,
    ) -> None:
        while not self._pacer.can_request():
            self._sleeper(
                0.1,
            )