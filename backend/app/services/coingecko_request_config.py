import os
from typing import Mapping, Optional


COINGECKO_DEMO_API_KEY_ENV = (
    "COINGECKO_DEMO_API_KEY"
)


class CoinGeckoRequestConfig:
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
    }

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
    ) -> None:
        normalized_api_key = (
            api_key.strip()
            if api_key
            else ""
        )

        self._api_key = (
            normalized_api_key
            or None
        )

    @property
    def api_key(
        self,
    ) -> Optional[str]:
        return self._api_key

    @property
    def headers(
        self,
    ) -> Mapping[str, str]:
        headers = dict(
            self.DEFAULT_HEADERS
        )

        if self._api_key:
            headers[
                "x-cg-demo-api-key"
            ] = self._api_key

        return headers

    @classmethod
    def from_environment(
        cls,
        environment: Optional[
            Mapping[str, str]
        ] = None,
    ) -> "CoinGeckoRequestConfig":
        source = (
            environment
            if environment is not None
            else os.environ
        )

        api_key = source.get(
            COINGECKO_DEMO_API_KEY_ENV
        )

        return cls(
            api_key=api_key,
        )