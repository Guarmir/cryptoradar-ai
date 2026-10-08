import logging
from collections.abc import Callable, Mapping
from typing import Any

import requests

logger = logging.getLogger(__name__)

RequestGet = Callable[..., Any]


class CoinGeckoChartClient:
    def __init__(
        self,
        *,
        api_base_url: str,
        request_get: RequestGet = requests.get,
        timeout: int = 20,
    ) -> None:
        self._api_base_url = api_base_url
        self._request_get = request_get
        self._timeout = timeout

    def fetch(
        self,
        coin_id: str,
        days: int,
    ) -> Mapping[str, Any]:
        url = (
            f"{self._api_base_url}"
            f"/coins/{coin_id}/market_chart"
        )

        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": (
                "hourly"
                if days <= 7
                else "daily"
            ),
        }

        response = self._request_get(
            url,
            params=params,
            timeout=self._timeout,
        )

        if response.status_code != 200:
            raise CoinGeckoChartRequestError(
                coin_id=coin_id,
                days=days,
                status_code=response.status_code,
            )

        return response.json()


class CoinGeckoChartRequestError(Exception):
    def __init__(
        self,
        *,
        coin_id: str,
        days: int,
        status_code: int,
    ) -> None:
        self.coin_id = coin_id
        self.days = days
        self.status_code = status_code

        super().__init__(
            "CoinGecko chart request failed: "
            f"coin_id={coin_id} "
            f"days={days} "
            f"status_code={status_code}"
        )