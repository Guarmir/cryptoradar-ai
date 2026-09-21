from app.ai.radar_ai_orchestrator_factory import (
    RadarAIOrchestratorFactory,
)


def test_factory_wires_market_overview_flow() -> None:
    provider = object()
    received = {}

    def intent_resolver(question: str) -> str:
        received["intent_question"] = question
        return "market_overview"

    def market_resolver(question: str) -> str:
        received["market_question"] = question
        return "crypto"

    def provider_resolver(
        intent: str,
        market: str,
    ):
        received["provider_intent"] = intent
        received["provider_market"] = market
        return provider

    def build_market_overview_context(
        question: str,
        selected_provider,
    ):
        received["context_question"] = question
        received["context_provider"] = selected_provider

        return {
            "status": "ready",
            "market": "crypto",
        }

    orchestrator = (
        RadarAIOrchestratorFactory.create_market_overview(
            intent_resolver=intent_resolver,
            market_resolver=market_resolver,
            provider_resolver=provider_resolver,
            build_market_overview_context=(
                build_market_overview_context
            ),
        )
    )

    result = orchestrator.orchestrate(
        "Como está o mercado agora?"
    )

    assert result.question == (
        "Como está o mercado agora?"
    )
    assert result.intent == "market_overview"
    assert result.market == "crypto"
    assert result.provider is provider
    assert result.context == {
        "status": "ready",
        "market": "crypto",
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
        "context_provider": provider,
    }