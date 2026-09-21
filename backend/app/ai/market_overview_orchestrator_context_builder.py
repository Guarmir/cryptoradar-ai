from typing import Any, Callable


class MarketOverviewOrchestratorContextBuilder:
    def __init__(
        self,
        *,
        build_market_overview_context: Callable[
            [str, Any],
            Any,
        ],
    ) -> None:
        self._build_market_overview_context = (
            build_market_overview_context
        )

    def __call__(
        self,
        question: str,
        intent: str,
        market: str,
        provider: Any,
    ) -> Any:
        if intent != "market_overview":
            raise ValueError(
                f"unsupported intent: {intent}"
            )

        return self._build_market_overview_context(
            question,
            provider,
        )