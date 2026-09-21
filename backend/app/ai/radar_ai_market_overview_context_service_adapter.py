from typing import Any

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.market_overview_context_service import (
    MarketOverviewContextService,
)


class RadarAIMarketOverviewContextServiceAdapter:
    def __call__(
        self,
        question: str,
        provider: Any,
    ) -> AssistantContext:
        if not question.strip():
            raise ValueError(
                "question must not be empty"
            )

        service = MarketOverviewContextService(
            provider=provider,
        )

        return service.build_context()