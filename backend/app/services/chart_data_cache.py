import time
from typing import Any


DEFAULT_CHART_TTL = 60 * 5


class ChartDataCache:
    def __init__(
        self,
        *,
        ttl: int = DEFAULT_CHART_TTL,
    ) -> None:
        if ttl <= 0:
            raise ValueError(
                "O TTL deve ser maior que zero."
            )

        self._ttl = ttl
        self._cache: dict[
            str,
            dict[str, Any],
        ] = {}

    @property
    def storage(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:
        return self._cache

    def get(
        self,
        coin_id: str,
        days: int,
    ):
        cache_key = self._cache_key(
            coin_id,
            days,
        )

        item = self._cache.get(
            cache_key,
        )

        if not item:
            return None

        if (
            time.time()
            - item["timestamp"]
            > self._ttl
        ):
            return None

        return item["data"]

    def get_stale(
        self,
        coin_id: str,
        days: int,
    ):
        cache_key = self._cache_key(
            coin_id,
            days,
        )

        item = self._cache.get(
            cache_key,
        )

        if not item:
            return None

        return item.get(
            "data",
        )

    def set(
        self,
        coin_id: str,
        days: int,
        data: Any,
    ) -> None:
        if not isinstance(data, dict):
            return

        prices = data.get("prices")

        if not isinstance(prices, list):
            return

        if not prices:
            return

        cache_key = self._cache_key(
            coin_id,
            days,
        )

        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time(),
        }

        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time(),
        }

    @staticmethod
    def _cache_key(
        coin_id: str,
        days: int,
    ) -> str:
        return f"{coin_id}_{days}"