import pytest

from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)


def test_orchestrator_coordinates_request() -> None:
    provider = object()

    received = {}

    def intent_resolver(
        question: str,
    ) -> str:
        received["intent_question"] = question
        return "market_overview"

    def market_resolver(
        question: str,
    ) -> str:
        received["market_question"] = question
        return "crypto"

    def provider_resolver(
        intent: str,
        market: str,
    ):
        received["provider_intent"] = intent
        received["provider_market"] = market
        return provider

    def context_builder(
        question: str,
        intent: str,
        market: str,
        selected_provider,
    ):
        received["context_question"] = question
        received["context_intent"] = intent
        received["context_market"] = market
        received["context_provider"] = (
            selected_provider
        )

        return {
            "market": market,
            "status": "ready",
        }

    orchestrator = RadarAIOrchestrator(
        intent_resolver=intent_resolver,
        market_resolver=market_resolver,
        provider_resolver=provider_resolver,
        context_builder=context_builder,
    )

    result = orchestrator.orchestrate(
        "  Como está o mercado agora?  "
    )

    assert result.question == (
        "Como está o mercado agora?"
    )
    assert result.intent == "market_overview"
    assert result.market == "crypto"
    assert result.provider is provider
    assert result.context == {
        "market": "crypto",
        "status": "ready",
    }

    assert received == {
        "intent_question": (
            "Como está o mercado agora?"
        ),
        "market_question": (
            "Como está o mercado agora?"
        ),
        "provider_intent": "market_overview",
        "provider_market": "crypto",
        "context_question": (
            "Como está o mercado agora?"
        ),
        "context_intent": "market_overview",
        "context_market": "crypto",
        "context_provider": provider,
    }


def test_orchestrator_rejects_empty_question() -> None:
    orchestrator = RadarAIOrchestrator(
        intent_resolver=lambda question: (
            "market_overview"
        ),
        market_resolver=lambda question: (
            "crypto"
        ),
        provider_resolver=(
            lambda intent, market: object()
        ),
        context_builder=(
            lambda question,
            intent,
            market,
            provider: {}
        ),
    )

    with pytest.raises(
        ValueError,
        match="question must not be empty",
    ):
        orchestrator.orchestrate("   ")