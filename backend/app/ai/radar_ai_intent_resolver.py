from typing import Optional

from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)


class RadarAIIntentResolver:
    MARKET_OVERVIEW = "market_overview"
    ASSET_ANALYSIS = "asset_analysis"
    UNKNOWN = "unknown"

    _MARKET_OVERVIEW_TERMS = (
        "mercado",
        "market",
        "visão geral",
        "visao geral",
        "panorama",
        "cenário",
        "cenario",
        "como está",
        "como esta",
        "como anda",
        "situação do mercado",
        "situacao do mercado",
    )

    def __init__(
        self,
        *,
        asset_resolver: Optional[
            RadarAIAssetResolver
        ] = None,
    ) -> None:
        self._asset_resolver = (
            asset_resolver
            or RadarAIAssetResolver()
        )

    def resolve(
        self,
        question: str,
    ) -> str:
        normalized_question = (
            question.strip().lower()
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        asset_id = (
            self._asset_resolver.resolve(
                normalized_question
            )
        )

        if asset_id is not None:
            return self.ASSET_ANALYSIS

        if any(
            term in normalized_question
            for term in (
                self._MARKET_OVERVIEW_TERMS
            )
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