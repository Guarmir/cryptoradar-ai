from typing import Any, Callable

from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)
from app.ai.radar_ai_market_resolver import (
    RadarAIMarketResolver,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)
from app.ai.radar_ai_orchestrator_factory import (
    RadarAIOrchestratorFactory,
)


class RadarAICryptoV1Factory:
    @staticmethod
    def create(
        *,
        provider_resolver: Callable[[str, str], Any],
        build_market_overview_context: Callable[
            [str, Any],
            Any,
        ],
    ) -> RadarAIOrchestrator:
        intent_resolver = RadarAIIntentResolver()
        market_resolver = RadarAIMarketResolver()

        def resolve_market(question: str) -> str:
            market = market_resolver.resolve(question)

            if market == RadarAIMarketResolver.UNKNOWN:
                return RadarAIMarketResolver.CRYPTO

            return market

        return (
            RadarAIOrchestratorFactory.create_market_overview(
                intent_resolver=intent_resolver,
                market_resolver=resolve_market,
                provider_resolver=provider_resolver,
                build_market_overview_context=(
                    build_market_overview_context
                ),
            )
        )