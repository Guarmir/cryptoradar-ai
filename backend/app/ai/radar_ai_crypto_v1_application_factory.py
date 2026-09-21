from typing import Any

from app.ai.radar_ai_crypto_v1_runtime_factory import (
    RadarAICryptoV1RuntimeFactory,
)
from app.ai.radar_ai_market_overview_context_service_adapter import (
    RadarAIMarketOverviewContextServiceAdapter,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)


class RadarAICryptoV1ApplicationFactory:
    @staticmethod
    def create(
        *,
        crypto_market_overview_provider: Any,
    ) -> RadarAIOrchestrator:
        context_adapter = (
            RadarAIMarketOverviewContextServiceAdapter()
        )

        return RadarAICryptoV1RuntimeFactory.create(
            crypto_market_overview_provider=(
                crypto_market_overview_provider
            ),
            build_market_overview_context=(
                context_adapter
            ),
        )