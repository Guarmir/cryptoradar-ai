
from typing import Callable, Optional

from app.early_movement.scanner.coingecko_scanner_market_provider import (
    CoinGeckoEarlyMovementScannerMarketProvider,
    EarlyMovementScannerDataError,
)
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

import requests


class ExtremeMovementMarketProvider:
    DEFAULT_START_PAGE = 2
    DEFAULT_PAGE_COUNT = 2
    MAX_PAGE_COUNT = 4
    ASSETS_PER_PAGE = 250

    def __init__(
        self,
        *,
        start_page: int = DEFAULT_START_PAGE,
        page_count: int = DEFAULT_PAGE_COUNT,
        timeout: int = 10,
        request_get: Optional[Callable] = None,
        request_config: Optional[CoinGeckoRequestConfig] = None,
    ) -> None:
        if start_page < 2:
            raise ValueError(
                "A descoberta complementar deve começar na página 2."
            )

        if not 1 <= page_count <= self.MAX_PAGE_COUNT:
            raise ValueError(
                "A quantidade de páginas deve ficar entre 1 e 4."
            )

        if timeout <= 0:
            raise ValueError(
                "O timeout deve ser maior que zero."
            )

        self._start_page = start_page
        self._page_count = page_count
        self._timeout = timeout
        self._request_get = (
            request_get if request_get is not None else requests.get
        )
        self._request_config = (
            request_config
            if request_config is not None
            else CoinGeckoRequestConfig.from_environment()
        )

    def fetch(self) -> tuple[EarlyMovementScannerMarketAsset, ...]:
        assets_by_id: dict[str, EarlyMovementScannerMarketAsset] = {}

        for page in range(
            self._start_page,
            self._start_page + self._page_count,
        ):
            try:
                response = coingecko_request_coordinator.execute(
                    lambda page=page: self._request_get(
                        CoinGeckoEarlyMovementScannerMarketProvider.MARKETS_URL,
                        params={
                            "vs_currency": "usd",
                            "order": "market_cap_desc",
                            "per_page": self.ASSETS_PER_PAGE,
                            "page": page,
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

            CoinGeckoEarlyMovementScannerMarketProvider._validate_response(
                response
            )

            payload = response.json()

            if not isinstance(payload, list):
                raise EarlyMovementScannerDataError(
                    "Resposta complementar de mercado inválida."
                )

            for item in payload:
                asset = (
                    CoinGeckoEarlyMovementScannerMarketProvider._build_asset(
                        item
                    )
                )

                if asset is not None:
                    assets_by_id.setdefault(asset.coin_id, asset)

        return tuple(assets_by_id.values())
