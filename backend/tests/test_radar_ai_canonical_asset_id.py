from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_api import (
    RadarAIQuestionRequest,
    ask_radar_ai,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrationResult,
    RadarAIOrchestrator,
)


def _asset_context() -> AssistantContext:
    return AssistantContext(
        intent=(
            AssistantIntent.ASSET_ANALYSIS
        ),
        source=(
            "cryptoradar_asset_analysis"
        ),
        source_version="v1",
        items=(
            AssistantContextItem(
                key="asset_summary",
                title="Resumo do ativo",
                content=(
                    "Cluster Protocol (CP)."
                ),
            ),
        ),
    )


def test_explicit_asset_id_forces_asset_analysis() -> None:
    provider = object()

    captured = {}

    def intent_resolver(
        question: str,
    ) -> str:
        return "unknown"

    def market_resolver(
        question: str,
    ) -> str:
        return "crypto"

    def provider_resolver(
        intent: str,
        market: str,
    ):
        captured["provider_intent"] = (
            intent
        )
        captured["provider_market"] = (
            market
        )

        return provider

    def context_builder(
        question: str,
        intent: str,
        market: str,
        received_provider,
        asset_id: str,
    ):
        captured["question"] = question
        captured["intent"] = intent
        captured["market"] = market
        captured["provider"] = (
            received_provider
        )
        captured["asset_id"] = (
            asset_id
        )

        return _asset_context()

    orchestrator = RadarAIOrchestrator(
        intent_resolver=intent_resolver,
        market_resolver=market_resolver,
        provider_resolver=(
            provider_resolver
        ),
        context_builder=context_builder,
    )

    result = orchestrator.orchestrate(
        "Como está a CP?",
        asset_id=" cluster-protocol ",
    )

    assert result.intent == (
        "asset_analysis"
    )

    assert captured["provider_intent"] == (
        "asset_analysis"
    )

    assert captured["provider_market"] == (
        "crypto"
    )

    assert captured["asset_id"] == (
        "cluster-protocol"
    )

    assert captured["provider"] is provider


def test_api_forwards_canonical_asset_id() -> None:
    provider = object()

    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
            *,
            asset_id: str,
        ):
            assert question == (
                "Como está a CP?"
            )

            assert asset_id == (
                "cluster-protocol"
            )

            return (
                RadarAIOrchestrationResult(
                    question=question,
                    intent="asset_analysis",
                    market="crypto",
                    provider=provider,
                    context=_asset_context(),
                )
            )

    class FakeAnswerComposer:
        def compose(
            self,
            context,
            question: str,
        ) -> str:
            return (
                "Cluster Protocol (CP)."
            )

    request = RadarAIQuestionRequest(
        question="Como está a CP?",
        asset_id="cluster-protocol",
    )

    response = ask_radar_ai(
        request,
        orchestrator=FakeOrchestrator(),
        answer_composer=(
            FakeAnswerComposer()
        ),
    )

    assert response.intent == (
        "asset_analysis"
    )

    assert response.market == "crypto"

    assert response.answer == (
        "Cluster Protocol (CP)."
    )


def test_api_preserves_legacy_question_only_flow() -> None:
    provider = object()

    class LegacyFakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            assert question == (
                "Como está o mercado cripto?"
            )

            return (
                RadarAIOrchestrationResult(
                    question=question,
                    intent="market_overview",
                    market="crypto",
                    provider=provider,
                    context=AssistantContext(
                        intent=(
                            AssistantIntent
                            .MARKET_OVERVIEW
                        ),
                        source="coingecko",
                        source_version=None,
                        items=(
                            AssistantContextItem(
                                key=(
                                    "market_summary"
                                ),
                                title=(
                                    "Resumo do mercado"
                                ),
                                content=(
                                    "Mercado disponível."
                                ),
                            ),
                        ),
                    ),
                )
            )

    class FakeAnswerComposer:
        def compose(
            self,
            context,
            question: str,
        ) -> str:
            return "Mercado disponível."

    request = RadarAIQuestionRequest(
        question=(
            "Como está o mercado cripto?"
        ),
    )

    response = ask_radar_ai(
        request,
        orchestrator=(
            LegacyFakeOrchestrator()
        ),
        answer_composer=(
            FakeAnswerComposer()
        ),
    )

    assert response.intent == (
        "market_overview"
    )

    assert response.answer == (
        "Mercado disponível."
    )