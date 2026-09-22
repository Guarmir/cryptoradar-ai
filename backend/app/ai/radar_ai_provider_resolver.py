from typing import Any, Optional


class RadarAIProviderResolver:
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    ASSET_COMPARISON = "asset_comparison"

    CRYPTO = "crypto"

    def __init__(
        self,
        *,
        crypto_market_overview_provider: Any,
        crypto_asset_analysis_provider: Optional[
            Any
        ] = None,
    ) -> None:
        self._crypto_market_overview_provider = (
            crypto_market_overview_provider
        )

        self._crypto_asset_analysis_provider = (
            crypto_asset_analysis_provider
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
            return (
                self._crypto_market_overview_provider
            )

        if (
            intent
            in (
                self.ASSET_ANALYSIS,
                self.ASSET_COMPARISON,
            )
            and market == self.CRYPTO
            and (
                self._crypto_asset_analysis_provider
                is not None
            )
        ):
            return (
                self._crypto_asset_analysis_provider
            )

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