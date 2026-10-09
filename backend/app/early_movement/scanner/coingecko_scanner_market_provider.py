import math
from typing import Any, Callable, Optional

import requests

from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)

from app.services.coingecko_request_config import (
    CoinGeckoRequestConfig,
)

from app.services.coingecko_request_coordinator import (
    CoinGeckoRequestBlocked,
)
from app.services.coingecko_request_runtime import (
    coingecko_request_coordinator,
)


class EarlyMovementScannerDataError(
    RuntimeError
):
    pass


class CoinGeckoEarlyMovementScannerMarketProvider:
    MARKETS_URL = (
        "https://api.coingecko.com/api/v3/coins/markets"
    )

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
    }

    MAX_ASSET_LIMIT = 250

    def __init__(
        self,
        *,
        timeout: int = 10,
        asset_limit: int = 100,
        request_get: Optional[
            Callable[..., Any]
        ] = None,
        request_config: Optional[
            CoinGeckoRequestConfig
        ] = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError(
                "O timeout deve ser maior que zero."
            )

        if not (
            1
            <= asset_limit
            <= self.MAX_ASSET_LIMIT
        ):
            raise ValueError(
                "O limite de ativos deve ficar "
                "entre 1 e 250."
            )

        self._timeout = timeout
        self._asset_limit = asset_limit
        self._request_get = (
            request_get
            or requests.get
        )

        self._request_config = (
            request_config
            or CoinGeckoRequestConfig.from_environment()
        )

    def fetch(
        self,
    ) -> tuple[
        EarlyMovementScannerMarketAsset,
        ...,
    ]:
        try:
            response = coingecko_request_coordinator.execute(
                lambda: self._request_get(
                    self.MARKETS_URL,
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": self._asset_limit,
                        "page": 1,
                        "sparkline": "false",
                        "price_change_percentage": "24h",
                    },
                    headers=self._request_config.headers,
                    timeout=self._timeout,
                )
            )
        except CoinGeckoRequestBlocked as error:
            raise EarlyMovementScannerDataError(
                "Limite temporário da CoinGecko atingido."
            ) from error

        self._validate_response(
            response,
        )

        payload = response.json()

        if not isinstance(
            payload,
            list,
        ):
            raise EarlyMovementScannerDataError(
                "Resposta de mercado inválida."
            )

        assets: list[
            EarlyMovementScannerMarketAsset
        ] = []

        for item in payload:
            asset = self._build_asset(
                item,
            )

            if asset is not None:
                assets.append(
                    asset,
                )

        if not assets:
            raise EarlyMovementScannerDataError(
                "Nenhum ativo válido foi recebido."
            )

        return tuple(
            assets,
        )

    @staticmethod
    def _build_asset(
        item: Any,
    ) -> Optional[
        EarlyMovementScannerMarketAsset
    ]:
        if not isinstance(
            item,
            dict,
        ):
            return None

        coin_id = str(
            item.get("id")
            or ""
        ).strip()

        symbol = str(
            item.get("symbol")
            or ""
        ).strip()

        name = str(
            item.get("name")
            or ""
        ).strip()

        current_price = _positive_float(
            item.get(
                "current_price",
            )
        )

        if (
            not coin_id
            or not symbol
            or not name
            or current_price is None
        ):
            return None

        return EarlyMovementScannerMarketAsset(
            coin_id=coin_id,
            symbol=symbol,
            name=name,
            current_price=current_price,
            total_volume=(
                _positive_float(
                    item.get(
                        "total_volume",
                    )
                )
            ),
            market_cap=(
                _positive_float(
                    item.get(
                        "market_cap",
                    )
                )
            ),
            price_change_percentage_24h=(
                _optional_float(
                    item.get(
                        "price_change_percentage_24h"
                    )
                )
            ),
            market_cap_rank=(
                _positive_int(
                    item.get(
                        "market_cap_rank",
                    )
                )
            ),
        )

    @staticmethod
    def _validate_response(
        response: Any,
    ) -> None:
        status_code = getattr(
            response,
            "status_code",
            None,
        )

        if status_code == 429:
            raise EarlyMovementScannerDataError(
                "Limite temporário da CoinGecko atingido."
            )

        if status_code != 200:
            raise EarlyMovementScannerDataError(
                "Falha ao buscar universo de mercado. "
                f"HTTP {status_code}."
            )


def _positive_float(
    value: Any,
) -> Optional[float]:
    parsed = _optional_float(
        value,
    )

    if (
        parsed is None
        or parsed <= 0
    ):
        return None

    return parsed


def _optional_float(
    value: Any,
) -> Optional[float]:
    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        parsed = float(
            value,
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(
        parsed,
    ):
        return None

    return parsed


def _positive_int(
    value: Any,
) -> Optional[int]:
    if isinstance(
        value,
        bool,
    ):
        return None

    try:
        parsed = int(
            value,
        )
    except (
        TypeError,
        ValueError,
    ):
        return None

    if parsed <= 0:
        return None

    return parsed