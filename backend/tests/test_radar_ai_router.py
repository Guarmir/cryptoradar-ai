from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai.assistant_context import (
    AssistantContext,
    AssistantContextItem,
)
from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrationResult,
)
from app.ai.radar_ai_router import (
    create_radar_ai_router,
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


def test_post_radar_ai_ask_endpoint() -> None:
    provider = object()

    class FakeOrchestrator:
        def orchestrate(
            self,
            question: str,
        ):
            return RadarAIOrchestrationResult(
                question=question,
                intent="market_overview",
                market="crypto",
                provider=provider,
                context=_context(),
            )

    app = FastAPI()

    app.include_router(
        create_radar_ai_router(
            orchestrator=FakeOrchestrator(),
        )
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": (
                "Como está o mercado cripto?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Como está o mercado cripto?"
    )
    assert body["intent"] == (
        "market_overview"
    )
    assert body["market"] == "crypto"
    assert body["supported"] is True
    assert body["source"] == "coingecko"

    assert len(body["items"]) == 1

    assert body["items"][0]["key"] == (
        "market_summary"
    )


def test_radar_ai_endpoint_validates_question() -> None:
    app = FastAPI()

    app.include_router(
        create_radar_ai_router()
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422