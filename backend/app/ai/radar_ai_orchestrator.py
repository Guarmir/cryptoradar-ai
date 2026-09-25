from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class RadarAIOrchestrationResult:
    question: str
    intent: str
    market: str
    provider: Any
    context: Any


class RadarAIOrchestrator:
    ASSET_ANALYSIS = "asset_analysis"

    def __init__(
        self,
        *,
        intent_resolver: Callable[[str], str],
        market_resolver: Callable[[str], str],
        provider_resolver: Callable[
            [str, str],
            Any,
        ],
        context_builder: Callable,
    ) -> None:
        self._intent_resolver = (
            intent_resolver
        )

        self._market_resolver = (
            market_resolver
        )

        self._provider_resolver = (
            provider_resolver
        )

        self._context_builder = (
            context_builder
        )

    def orchestrate(
        self,
        question: str,
        *,
        asset_id: Optional[str] = None,
    ) -> RadarAIOrchestrationResult:
        normalized_question = (
            question.strip()
        )

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        normalized_asset_id = None

        if asset_id is not None:
            normalized_asset_id = (
                asset_id.strip()
            )

            if not normalized_asset_id:
                raise ValueError(
                    "asset_id must not be empty"
                )

        if normalized_asset_id is None:
            intent = self._intent_resolver(
                normalized_question
            )
        else:
            intent = self.ASSET_ANALYSIS

        market = self._market_resolver(
            normalized_question
        )

        provider = self._provider_resolver(
            intent,
            market,
        )

        if normalized_asset_id is None:
            context = self._context_builder(
                normalized_question,
                intent,
                market,
                provider,
            )
        else:
            context = self._context_builder(
                normalized_question,
                intent,
                market,
                provider,
                normalized_asset_id,
            )

        return RadarAIOrchestrationResult(
            question=normalized_question,
            intent=intent,
            market=market,
            provider=provider,
            context=context,
        )