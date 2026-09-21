from typing import Any


class RadarAIProviderResolver:
    MARKET_OVERVIEW = "market_overview"
    CRYPTO = "crypto"

    def __init__(
        self,
        *,
        crypto_market_overview_provider: Any,
    ) -> None:
        self._crypto_market_overview_provider = (
            crypto_market_overview_provider
        )

    def resolve(
        self,
        intent: str,
        market: str,
    ) -> Any:
        if (
            intent == self.MARKET_OVERVIEW
            and market == self.CRYPTO
        ):
            return self._crypto_market_overview_provider

        raise ValueError(
            "unsupported Radar AI provider route: "
            f"intent={intent}, market={market}"
        )

    def __call__(
        self,
        intent: str,
        market: str,
    ) -> Any:
        return self.resolve(
            intent,
            market,
        )