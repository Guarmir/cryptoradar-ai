from typing import Any, Callable, Optional

import requests

from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)


class MarketOverviewDataError(
    RuntimeError
):
    pass


class CoinGeckoMarketOverviewProvider:
    GLOBAL_URL = (
        "https://api.coingecko.com/api/v3/global"
    )

    MARKETS_URL = (
        "https://api.coingecko.com/api/v3/coins/markets"
    )

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
    }

    def __init__(
        self,
        *,
        timeout: int = 10,
        asset_limit: int = 20,
        request_get: Optional[
            Callable[..., Any]
        ] = None,
    ):
        if timeout <= 0:
            raise ValueError(
                "O timeout deve ser maior que zero."
            )

        if asset_limit < 1:
            raise ValueError(
                "O limite de ativos deve ser maior que zero."
            )

        self._timeout = timeout
        self._asset_limit = asset_limit
        self._request_get = (
            request_get
            or requests.get
        )

    def fetch(
        self,
    ) -> MarketOverviewSnapshot:
        global_data = (
            self._fetch_global_data()
        )

        assets = (
            self._fetch_market_assets()
        )

        total_market_cap = (
            global_data
            .get(
                "total_market_cap",
                {},
            )
            .get(
                "usd",
            )
        )

        total_volume = (
            global_data
            .get(
                "total_volume",
                {},
            )
            .get(
                "usd",
            )
        )

        market_cap_change = (
            global_data.get(
                "market_cap_change_percentage_24h_usd"
            )
        )

        dominance = global_data.get(
            "market_cap_percentage",
            {},
        )

        btc_dominance = (
            dominance.get(
                "btc",
            )
        )

        eth_dominance = (
            dominance.get(
                "eth",
            )
        )

        required_values = (
            total_market_cap,
            total_volume,
            market_cap_change,
            btc_dominance,
        )

        if any(
            value is None
            for value in required_values
        ):
            raise MarketOverviewDataError(
                "Dados globais de mercado incompletos."
            )

        return MarketOverviewSnapshot(
            total_market_cap_usd=float(
                total_market_cap,
            ),
            total_volume_24h_usd=float(
                total_volume,
            ),
            market_cap_change_24h_percent=float(
                market_cap_change,
            ),
            btc_dominance_percent=float(
                btc_dominance,
            ),
            eth_dominance_percent=(
                float(
                    eth_dominance,
                )
                if eth_dominance is not None
                else None
            ),
            assets=assets,
        )

    def _fetch_global_data(
        self,
    ) -> dict:
        response = self._request_get(
            self.GLOBAL_URL,
            headers=self.DEFAULT_HEADERS,
            timeout=self._timeout,
        )

        self._validate_response(
            response,
            operation=(
                "buscar dados globais"
            ),
        )

        payload = response.json()

        if not isinstance(
            payload,
            dict,
        ):
            raise MarketOverviewDataError(
                "Resposta global invalida."
            )

        data = payload.get(
            "data",
        )

        if not isinstance(
            data,
            dict,
        ):
            raise MarketOverviewDataError(
                "Dados globais indisponiveis."
            )

        return data

    def _fetch_market_assets(
        self,
    ) -> tuple[
        MarketOverviewAsset,
        ...,
    ]:
        response = self._request_get(
            self.MARKETS_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": self._asset_limit,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
            headers=self.DEFAULT_HEADERS,
            timeout=self._timeout,
        )

        self._validate_response(
            response,
            operation=(
                "buscar principais ativos"
            ),
        )

        payload = response.json()

        if not isinstance(
            payload,
            list,
        ):
            raise MarketOverviewDataError(
                "Resposta de ativos invalida."
            )

        assets = []

        for item in payload:
            if not isinstance(
                item,
                dict,
            ):
                continue

            symbol = str(
                item.get(
                    "symbol",
                )
                or ""
            ).strip()

            name = str(
                item.get(
                    "name",
                )
                or ""
            ).strip()

            price = item.get(
                "current_price",
            )

            if (
                not symbol
                or not name
                or price is None
                or price <= 0
            ):
                continue

            assets.append(
                MarketOverviewAsset(
                    symbol=symbol,
                    name=name,
                    price_usd=float(
                        price,
                    ),
                    change_24h_percent=(
                        _optional_float(
                            item.get(
                                "price_change_percentage_24h"
                            )
                        )
                    ),
                    market_cap_usd=(
                        _optional_float(
                            item.get(
                                "market_cap"
                            )
                        )
                    ),
                    volume_24h_usd=(
                        _optional_float(
                            item.get(
                                "total_volume"
                            )
                        )
                    ),
                )
            )

        if not assets:
            raise MarketOverviewDataError(
                "Nenhum ativo valido foi recebido."
            )

        return tuple(
            assets,
        )

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
            raise MarketOverviewDataError(
                "Limite temporario da CoinGecko atingido."
            )

        if status_code != 200:
            raise MarketOverviewDataError(
                f"Falha ao {operation}. "
                f"HTTP {status_code}."
            )


def _optional_float(
    value,
):
    if value is None:
        return None

    return float(
        value,
    )