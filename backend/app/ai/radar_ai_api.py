from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.ai.coingecko_market_overview_provider import (
    CoinGeckoMarketOverviewProvider,
    MarketOverviewDataError,
)
from app.ai.radar_ai_crypto_v1_application_factory import (
    RadarAICryptoV1ApplicationFactory,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)


class RadarAIQuestionRequest(
    BaseModel
):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


class RadarAIContextItemResponse(
    BaseModel
):
    key: str
    title: str
    content: str


class RadarAIQuestionResponse(
    BaseModel
):
    question: str
    intent: str
    market: str
    supported: bool
    source: str
    source_version: Optional[str]
    items: list[
        RadarAIContextItemResponse
    ]


def ask_radar_ai(
    request: RadarAIQuestionRequest,
    *,
    orchestrator: Optional[
        RadarAIOrchestrator
    ] = None,
) -> RadarAIQuestionResponse:
    effective_orchestrator = orchestrator

    if effective_orchestrator is None:
        provider = (
            CoinGeckoMarketOverviewProvider()
        )

        effective_orchestrator = (
            RadarAICryptoV1ApplicationFactory
            .create(
                crypto_market_overview_provider=(
                    provider
                ),
            )
        )

    try:
        result = (
            effective_orchestrator
            .orchestrate(
                request.question,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except MarketOverviewDataError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    context = result.context

    return RadarAIQuestionResponse(
        question=result.question,
        intent=result.intent,
        market=result.market,
        supported=context.is_supported,
        source=context.source,
        source_version=(
            context.source_version
        ),
        items=[
            RadarAIContextItemResponse(
                key=item.key,
                title=item.title,
                content=item.content,
            )
            for item in context.items
        ],
    )