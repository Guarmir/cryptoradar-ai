from typing import Optional

from app.ai.assistant_context import (
    AssistantContext,
)
from app.ai.coingecko_market_overview_provider import (
    CoinGeckoMarketOverviewProvider,
)
from app.ai.market_overview_context_builder import (
    build_market_overview_context,
)


class MarketOverviewContextService:
    def __init__(
        self,
        *,
        provider: Optional[
            CoinGeckoMarketOverviewProvider
        ] = None,
    ):
        self._provider = (
            provider
            if provider is not None
            else CoinGeckoMarketOverviewProvider()
        )

    def build_context(
        self,
    ) -> AssistantContext:
        snapshot = (
            self._provider.fetch()
        )

        return (
            build_market_overview_context(
                snapshot,
            )
        )