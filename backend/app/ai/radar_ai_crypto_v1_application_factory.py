from typing import Any, Optional

from app.ai.crypto_asset_analysis_provider import (
    CryptoAssetAnalysisProvider,
)
from app.ai.radar_ai_asset_context_service import (
    RadarAIAssetContextService,
)
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.ai.radar_ai_crypto_context_builder import (
    RadarAICryptoContextBuilder,
)
from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)
from app.ai.radar_ai_market_overview_context_service_adapter import (
    RadarAIMarketOverviewContextServiceAdapter,
)
from app.ai.radar_ai_market_resolver import (
    RadarAIMarketResolver,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)
from app.ai.radar_ai_provider_resolver import (
    RadarAIProviderResolver,
)


class RadarAICryptoV1ApplicationFactory:
    @staticmethod
    def create(
        *,
        crypto_market_overview_provider: Any,
        crypto_asset_analysis_provider: Optional[
            Any
        ] = None,
        asset_resolver: Optional[
            RadarAIAssetResolver
        ] = None,
    ) -> RadarAIOrchestrator:
        effective_asset_resolver = (
            asset_resolver
            or RadarAIAssetResolver()
        )

        intent_resolver = (
            RadarAIIntentResolver(
                asset_resolver=(
                    effective_asset_resolver
                ),
            )
        )

        market_resolver = (
            RadarAIMarketResolver()
        )

        effective_asset_provider = (
            crypto_asset_analysis_provider
            or CryptoAssetAnalysisProvider()
        )

        provider_resolver = (
            RadarAIProviderResolver(
                crypto_market_overview_provider=(
                    crypto_market_overview_provider
                ),
                crypto_asset_analysis_provider=(
                    effective_asset_provider
                ),
            )
        )

        market_overview_adapter = (
            RadarAIMarketOverviewContextServiceAdapter()
        )

        def build_asset_analysis_context(
            question: str,
            provider: Any,
        ):
            service = (
                RadarAIAssetContextService(
                    provider=provider,
                    asset_resolver=(
                        effective_asset_resolver
                    ),
                )
            )

            return service.build_context(
                question
            )

        context_builder = (
            RadarAICryptoContextBuilder(
                build_market_overview_context=(
                    market_overview_adapter
                ),
                build_asset_analysis_context=(
                    build_asset_analysis_context
                ),
            )
        )

        def resolve_market(
            question: str,
        ) -> str:
            market = market_resolver.resolve(
                question
            )

            if (
                market
                == RadarAIMarketResolver.UNKNOWN
            ):
                return (
                    RadarAIMarketResolver.CRYPTO
                )

            return market

        return RadarAIOrchestrator(
            intent_resolver=intent_resolver,
            market_resolver=resolve_market,
            provider_resolver=provider_resolver,
            context_builder=context_builder,
        )