from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class RadarAIOrchestrationResult:
    question: str
    intent: str
    market: str
    provider: Any
    context: Any


class RadarAIOrchestrator:
    def __init__(
        self,
        *,
        intent_resolver: Callable[[str], str],
        market_resolver: Callable[[str], str],
        provider_resolver: Callable[[str, str], Any],
        context_builder: Callable[
            [str, str, str, Any],
            Any,
        ],
    ) -> None:
        self._intent_resolver = intent_resolver
        self._market_resolver = market_resolver
        self._provider_resolver = provider_resolver
        self._context_builder = context_builder

    def orchestrate(
        self,
        question: str,
    ) -> RadarAIOrchestrationResult:
        normalized_question = question.strip()

        if not normalized_question:
            raise ValueError(
                "question must not be empty"
            )

        intent = self._intent_resolver(
            normalized_question
        )

        market = self._market_resolver(
            normalized_question
        )

        provider = self._provider_resolver(
            intent,
            market,
        )

        context = self._context_builder(
            normalized_question,
            intent,
            market,
            provider,
        )

        return RadarAIOrchestrationResult(
            question=normalized_question,
            intent=intent,
            market=market,
            provider=provider,
            context=context,
        )