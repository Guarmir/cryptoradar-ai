import pytest
from fastapi import HTTPException

from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.coingecko_market_overview_provider import (
    MarketOverviewDataError,
)
from app.ai.crypto_asset_analysis_provider import (
    AssetAnalysisDataError,
)
from app.ai.radar_ai_api import (
    RadarAIQuestionRequest,
    ask_radar_ai,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrationResult,
)


def _context() -> AssistantContext:
    return AssistantContext(
        intent=(
            AssistantIntent.MARKET_OVERVIEW
        ),
        source="coingecko",
        source_version=None,
        items=(
            AssistantContextItem(
                key="market_summary",
                title="Resumo do mercado",
                content=(
                    "Mercado cripto disponível."
                ),
            ),
        ),
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
                    "Uniswap (UNI): "
                    "cenário de mercado disponível."
                ),
            ),
        ),
    )


def test_api_returns_orchestrated_context() -> None:
    provider = object()

    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            return (
                RadarAIOrchestrationResult(
                    question=question,
                    intent="market_overview",
                    market="crypto",
                    provider=provider,
                    context=_context(),
                )
            )

    response = ask_radar_ai(
        RadarAIQuestionRequest(
            question=(
                "Como está o mercado cripto?"
            ),
        ),
        orchestrator=FakeOrchestrator(),
    )

    assert response.question == (
        "Como está o mercado cripto?"
    )
    assert response.intent == (
        "market_overview"
    )
    assert response.market == "crypto"
    assert response.supported is True
    assert response.source == "coingecko"
    assert response.source_version is None

    assert response.answer == (
        "Mercado cripto disponível."
    )

    assert len(response.items) == 1

    assert response.items[0].key == (
        "market_summary"
    )


def test_api_returns_asset_analysis() -> None:
    provider = object()

    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            return (
                RadarAIOrchestrationResult(
                    question=question,
                    intent="asset_analysis",
                    market="crypto",
                    provider=provider,
                    context=_asset_context(),
                )
            )

    response = ask_radar_ai(
        RadarAIQuestionRequest(
            question="Como está a UNI?",
        ),
        orchestrator=FakeOrchestrator(),
    )

    assert response.question == (
        "Como está a UNI?"
    )

    assert response.intent == (
        "asset_analysis"
    )

    assert response.market == "crypto"

    assert response.source == (
        "cryptoradar_asset_analysis"
    )

    assert response.source_version == "v1"

    assert "Uniswap" in response.answer

    assert response.items[0].key == (
        "asset_summary"
    )


def test_api_maps_invalid_request_to_422() -> None:
    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            raise ValueError(
                "unsupported Radar AI route"
            )

    with pytest.raises(
        HTTPException,
    ) as captured:
        ask_radar_ai(
            RadarAIQuestionRequest(
                question="Pergunta inválida",
            ),
            orchestrator=(
                FakeOrchestrator()
            ),
        )

    assert (
        captured.value.status_code
        == 422
    )

    assert captured.value.detail == (
        "unsupported Radar AI route"
    )


def test_api_maps_unknown_crypto_route_to_safe_message() -> None:
    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            raise ValueError(
                "unsupported Radar AI provider route: "
                "intent=unknown, market=crypto"
            )

    with pytest.raises(
        HTTPException,
    ) as captured:
        ask_radar_ai(
            RadarAIQuestionRequest(
                question="Como está SI?",
            ),
            orchestrator=(
                FakeOrchestrator()
            ),
        )

    assert (
        captured.value.status_code
        == 422
    )

    assert captured.value.detail == (
        "Não foi possível identificar com segurança "
        "o ativo ou o tipo de análise solicitado. "
        "Se você informou apenas um símbolo, "
        "use o nome completo do ativo."
    )

    assert (
        "unsupported Radar AI provider route"
        not in captured.value.detail
    )


def test_api_maps_market_error_to_503() -> None:
    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            raise MarketOverviewDataError(
                "Dados indisponíveis."
            )

    with pytest.raises(
        HTTPException,
    ) as captured:
        ask_radar_ai(
            RadarAIQuestionRequest(
                question=(
                    "Como está o mercado?"
                ),
            ),
            orchestrator=(
                FakeOrchestrator()
            ),
        )

    assert (
        captured.value.status_code
        == 503
    )


def test_api_maps_asset_error_to_503() -> None:
    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            raise AssetAnalysisDataError(
                "Dados do ativo indisponíveis."
            )

    with pytest.raises(
        HTTPException,
    ) as captured:
        ask_radar_ai(
            RadarAIQuestionRequest(
                question="Como está a UNI?",
            ),
            orchestrator=(
                FakeOrchestrator()
            ),
        )

    assert (
        captured.value.status_code
        == 503
    )


def test_api_returns_focused_asset_answer() -> None:
    provider = object()

    context = AssistantContext(
        intent=(
            AssistantIntent.ASSET_ANALYSIS
        ),
        source=(
            "cryptoradar_asset_analysis"
        ),
        source_version="v1",
        items=(
            AssistantContextItem(
                key="asset_price",
                title="Preço",
                content=(
                    "Uniswap está cotado "
                    "em US$ 12.50."
                ),
            ),
            AssistantContextItem(
                key="asset_score",
                title="Score",
                content=(
                    "O score atual de "
                    "Uniswap é 77/100."
                ),
            ),
        ),
    )

    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            return (
                RadarAIOrchestrationResult(
                    question=question,
                    intent="asset_analysis",
                    market="crypto",
                    provider=provider,
                    context=context,
                )
            )

    response = ask_radar_ai(
        RadarAIQuestionRequest(
            question=(
                "Qual o score da UNI?"
            ),
        ),
        orchestrator=(
            FakeOrchestrator()
        ),
    )

    assert "77/100" in response.answer

    assert "US$ 12.50" not in (
        response.answer
    )