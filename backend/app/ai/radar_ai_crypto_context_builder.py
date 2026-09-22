from typing import Any, Callable, Optional


class RadarAICryptoContextBuilder:
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    ASSET_COMPARISON = "asset_comparison"

    CRYPTO = "crypto"

    def __init__(
        self,
        *,
        build_market_overview_context: Callable,
        build_asset_analysis_context: Callable,
        build_asset_comparison_context: Optional[
            Callable
        ] = None,
    ) -> None:
        self._build_market_overview_context = (
            build_market_overview_context
        )

        self._build_asset_analysis_context = (
            build_asset_analysis_context
        )

        self._build_asset_comparison_context = (
            build_asset_comparison_context
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
                self
                ._build_market_overview_context(
                    question,
                    provider,
                )
            )

        if intent == self.ASSET_ANALYSIS:
            return (
                self
                ._build_asset_analysis_context(
                    question,
                    provider,
                )
            )

        if intent == self.ASSET_COMPARISON:
            if (
                self
                ._build_asset_comparison_context
                is None
            ):
                raise ValueError(
                    "asset comparison context "
                    "builder is not configured"
                )

            return (
                self
                ._build_asset_comparison_context(
                    question,
                    provider,
                )
            )

        raise ValueError(
            f"unsupported intent: {intent}"
        )