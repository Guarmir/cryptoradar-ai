import unicodedata
from typing import Optional

from app.ai.radar_ai_asset_comparison_resolver import (
    RadarAIAssetComparisonResolver,
)
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)


class RadarAIIntentResolver:
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    ASSET_COMPARISON = "asset_comparison"
    UNKNOWN = "unknown"

    _MARKET_OVERVIEW_TERMS = (
        "mercado",
        "market",
        "mercado cripto",
        "crypto market",
        "mercado crypto",
        "panorama",
        "cenario",
        "visao geral",
    )

    def __init__(
        self,
        *,
        asset_resolver: Optional[
            RadarAIAssetResolver
        ] = None,
        asset_comparison_resolver: Optional[
            RadarAIAssetComparisonResolver
        ] = None,
    ) -> None:
        self._asset_resolver = (
            asset_resolver
            or RadarAIAssetResolver()
        )

        self._asset_comparison_resolver = (
            asset_comparison_resolver
            or RadarAIAssetComparisonResolver()
        )

    def resolve(
        self,
        question: str,
    ) -> str:
        normalized_question = (
            self._normalize(
                question
            )
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        comparison_assets = (
            self._asset_comparison_resolver.resolve(
                question
            )
        )

        if len(comparison_assets) >= 2:
            return self.ASSET_COMPARISON

        asset_id = (
            self._asset_resolver.resolve(
                question
            )
        )

        if asset_id is not None:
            return self.ASSET_ANALYSIS

        if any(
            term in normalized_question
            for term in self._MARKET_OVERVIEW_TERMS
        ):
            return self.MARKET_OVERVIEW

        return self.UNKNOWN

    def __call__(
        self,
        question: str,
    ) -> str:
        return self.resolve(
            question
        )

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value.strip().lower(),
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )