from typing import Any, Callable


class RadarAICryptoContextBuilder:
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    CRYPTO = "crypto"

    def __init__(
        self,
        *,
        build_market_overview_context: Callable[
            [str, Any],
            Any,
        ],
        build_asset_analysis_context: Callable[
            [str, Any],
            Any,
        ],
    ) -> None:
        self._build_market_overview_context = (
            build_market_overview_context
        )

        self._build_asset_analysis_context = (
            build_asset_analysis_context
        )

    def __call__(
        self,
        question: str,
        intent: str,
        market: str,
        provider: Any,
    ) -> Any:
        if market != self.CRYPTO:
            raise ValueError(
                f"unsupported market: {market}"
            )

        if intent == self.MARKET_OVERVIEW:
            return (
                self._build_market_overview_context(
                    question,
                    provider,
                )
            )

        if intent == self.ASSET_ANALYSIS:
            return (
                self._build_asset_analysis_context(
                    question,
                    provider,
                )
            )

        raise ValueError(
            f"unsupported intent: {intent}"
        )