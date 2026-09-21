from typing import Any, Callable

from app.ai.market_overview_orchestrator_context_builder import (
    MarketOverviewOrchestratorContextBuilder,
)
from app.ai.radar_ai_orchestrator import RadarAIOrchestrator


class RadarAIOrchestratorFactory:
    @staticmethod
    def create_market_overview(
        *,
        intent_resolver: Callable[[str], str],
        market_resolver: Callable[[str], str],
        provider_resolver: Callable[[str, str], Any],
        build_market_overview_context: Callable[
            [str, Any],
            Any,
        ],
    ) -> RadarAIOrchestrator:
        context_builder = (
            MarketOverviewOrchestratorContextBuilder(
                build_market_overview_context=(
                    build_market_overview_context
                ),
            )
        )

        return RadarAIOrchestrator(
            intent_resolver=intent_resolver,
            market_resolver=market_resolver,
            provider_resolver=provider_resolver,
            context_builder=context_builder,
        )