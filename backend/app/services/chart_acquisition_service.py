import time
from collections.abc import Callable, Mapping
from typing import Any

from app.services.chart_request_pacer import (
    ChartRequestPacer,
)

ChartFetcher = Callable[
    [str, int],
    Mapping[str, Any],
]

Sleeper = Callable[
    [float],
    None,
]


class ChartAcquisitionService:
    def __init__(
        self,
        *,
        chart_fetcher: ChartFetcher,
        pacer: ChartRequestPacer | None = None,
        sleeper: Sleeper = time.sleep,
        request_budget: int | None = None,
    ) -> None:
        if (
            request_budget is not None
            and request_budget < 1
        ):
            raise ValueError(
                "O orçamento de requisições deve ser "
                "maior que zero."
            )

        self._chart_fetcher = chart_fetcher
        self._pacer = (
            pacer
            or ChartRequestPacer()
        )
        self._sleeper = sleeper
        self._request_budget = request_budget
        self._request_count = 0

    def fetch(
        self,
        coin_id: str,
        days: int,
    ) -> Mapping[str, Any]:
        if (
            self._request_budget is not None
            and self._request_count
            >= self._request_budget
        ):
            return {
                "prices": [],
            }

        self._wait_until_allowed()

        self._request_count += 1

        try:
            return self._chart_fetcher(
                coin_id,
                days,
            )
        finally:
            self._pacer.record_request()

    def reset_budget(
        self,
    ) -> None:
        self._request_count = 0

    def _wait_until_allowed(
        self,
    ) -> None:
        while not self._pacer.can_request():
            self._sleeper(0.1)