from typing import Any, Callable, Mapping, Optional

import requests

from app.monitoring.monitoring_market_data_provider import (
    MonitoringMarketDataProvider,
)
from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringMarketDataError(RuntimeError):
    pass


class CoinGeckoMonitoringMarketDataProvider(
    MonitoringMarketDataProvider
):
    SEARCH_URL = "https://api.coingecko.com/api/v3/search"
    MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
    }

    def __init__(
        self,
        *,
        timeout: int = 10,
        request_get: Optional[Callable[..., Any]] = None,
    ):
        if timeout <= 0:
            raise ValueError(
                "O timeout deve ser maior que zero."
            )

        self._timeout = timeout
        self._request_get = request_get or requests.get
        self._resolved_coin_ids: dict[str, str] = {}

    def fetch_market_data(
        self,
        target: MonitoringTarget,
    ) -> Mapping[str, Any]:
        coin_id = self._coin_id_for_target(
            target,
        )

        response = self._request_get(
            self.MARKETS_URL,
            params={
                "vs_currency": "usd",
                "ids": coin_id,
                "price_change_percentage": "24h",
            },
            headers=self.DEFAULT_HEADERS,
            timeout=self._timeout,
        )

        self._validate_response(
            response,
            operation="buscar dados de mercado",
        )

        payload = response.json()

        if not isinstance(payload, list) or not payload:
            raise MonitoringMarketDataError(
                f"Dados de mercado indisponíveis para "
                f"{target.symbol}."
            )

        market_data = payload[0]

        if not isinstance(market_data, dict):
            raise MonitoringMarketDataError(
                f"Resposta de mercado inválida para "
                f"{target.symbol}."
            )

        return market_data

    def _coin_id_for_target(
        self,
        target: MonitoringTarget,
    ) -> str:
        if target.coin_id:
            self._resolved_coin_ids[
                target.symbol
            ] = target.coin_id

            return target.coin_id

        cached = self._resolved_coin_ids.get(
            target.symbol,
        )

        if cached:
            return cached

        resolved = self._resolve_coin_id(
            target.symbol,
        )

        self._resolved_coin_ids[
            target.symbol
        ] = resolved

        return resolved

    def _resolve_coin_id(
        self,
        symbol: str,
    ) -> str:
        response = self._request_get(
            self.SEARCH_URL,
            params={
                "query": symbol,
            },
            headers=self.DEFAULT_HEADERS,
            timeout=self._timeout,
        )

        self._validate_response(
            response,
            operation="resolver ativo",
        )

        payload = response.json()

        if not isinstance(payload, dict):
            raise MonitoringMarketDataError(
                f"Resposta de busca inválida para {symbol}."
            )

        coins = payload.get(
            "coins",
            [],
        )

        if not isinstance(coins, list) or not coins:
            raise MonitoringMarketDataError(
                f"Ativo {symbol} não encontrado."
            )

        query = symbol.strip().lower()

        exact_id = None
        exact_symbol = None
        exact_name = None
        fallback = None

        for coin in coins:
            if not isinstance(coin, dict):
                continue

            coin_id = str(
                coin.get("id") or ""
            ).strip()

            coin_symbol = str(
                coin.get("symbol") or ""
            ).strip()

            coin_name = str(
                coin.get("name") or ""
            ).strip()

            if not coin_id:
                continue

            if fallback is None:
                fallback = coin_id

            if coin_id.lower() == query:
                exact_id = coin_id
                break

            if (
                exact_symbol is None
                and coin_symbol.lower() == query
            ):
                exact_symbol = coin_id

            if (
                exact_name is None
                and coin_name.lower() == query
            ):
                exact_name = coin_id

        resolved = (
            exact_id
            or exact_symbol
            or exact_name
            or fallback
        )

        if not resolved:
            raise MonitoringMarketDataError(
                f"Ativo {symbol} não encontrado."
            )

        return resolved

    @staticmethod
    def _validate_response(
        response: Any,
        *,
        operation: str,
    ) -> None:
        status_code = getattr(
            response,
            "status_code",
            None,
        )

        if status_code == 429:
            raise MonitoringMarketDataError(
                "Limite temporário da CoinGecko atingido."
            )

        if status_code != 200:
            raise MonitoringMarketDataError(
                f"Falha ao {operation}. "
                f"HTTP {status_code}."
            )