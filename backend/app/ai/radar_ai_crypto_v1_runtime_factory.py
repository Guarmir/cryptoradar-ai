from typing import Any, Callable

from app.ai.radar_ai_crypto_v1_factory import (
    RadarAICryptoV1Factory,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)
from app.ai.radar_ai_provider_resolver import (
    RadarAIProviderResolver,
)


class RadarAICryptoV1RuntimeFactory:
    @staticmethod
    def create(
        *,
        crypto_market_overview_provider: Any,
        build_market_overview_context: Callable[
            [str, Any],
            Any,
        ],
    ) -> RadarAIOrchestrator:
        provider_resolver = RadarAIProviderResolver(
            crypto_market_overview_provider=(
                crypto_market_overview_provider
            ),
        )

        return RadarAICryptoV1Factory.create(
            provider_resolver=provider_resolver,
            build_market_overview_context=(
                build_market_overview_context
            ),
        )