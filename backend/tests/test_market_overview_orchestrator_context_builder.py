import pytest

from app.ai.market_overview_orchestrator_context_builder import (
    MarketOverviewOrchestratorContextBuilder,
)


def test_builds_market_overview_context() -> None:
    provider = object()
    received = {}

    def build_market_overview_context(
        question: str,
        selected_provider,
    ):
        received["question"] = question
        received["provider"] = selected_provider

        return {
            "status": "ready",
            "market": "crypto",
        }

    builder = (
        MarketOverviewOrchestratorContextBuilder(
            build_market_overview_context=(
                build_market_overview_context
            ),
        )
    )

    context = builder(
        "Como está o mercado agora?",
        "market_overview",
        "crypto",
        provider,
    )

    assert context == {
        "status": "ready",
        "market": "crypto",
    }

    assert received == {
        "question": "Como está o mercado agora?",
        "provider": provider,
    }


def test_rejects_unsupported_intent() -> None:
    builder = (
        MarketOverviewOrchestratorContextBuilder(
            build_market_overview_context=(
                lambda question, provider: {}
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="unsupported intent: asset_analysis",
    ):
        builder(
            "Analise o Bitcoin",
            "asset_analysis",
            "crypto",
            object(),
        )