from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.ai.coingecko_market_overview_provider import (
    CoinGeckoMarketOverviewProvider,
    MarketOverviewDataError,
)
from app.ai.crypto_asset_analysis_provider import (
    AssetAnalysisDataError,
    CryptoAssetAnalysisProvider,
)
from app.ai.radar_ai_answer_composer import (
    RadarAIAnswerComposer,
)
from app.ai.radar_ai_crypto_v1_application_factory import (
    RadarAICryptoV1ApplicationFactory,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)


_UNKNOWN_CRYPTO_ROUTE_ERROR = (
    "unsupported Radar AI provider route: "
    "intent=unknown, market=crypto"
)

_UNKNOWN_CRYPTO_ROUTE_MESSAGE = (
    "Não foi possível identificar com segurança "
    "o ativo ou o tipo de análise solicitado. "
    "Se você informou apenas um símbolo, "
    "use o nome completo do ativo."
)


class RadarAIQuestionRequest(
    BaseModel
):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    asset_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
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
    answer: str
    items: list[
        RadarAIContextItemResponse
    ]


def _value_error_detail(
    error: ValueError,
) -> str:
    detail = str(error)

    if detail == _UNKNOWN_CRYPTO_ROUTE_ERROR:
        return (
            _UNKNOWN_CRYPTO_ROUTE_MESSAGE
        )

    return detail


def ask_radar_ai(
    request: RadarAIQuestionRequest,
    *,
    orchestrator: Optional[
        RadarAIOrchestrator
    ] = None,
    answer_composer: Optional[
        RadarAIAnswerComposer
    ] = None,
) -> RadarAIQuestionResponse:
    effective_orchestrator = orchestrator

    if effective_orchestrator is None:
        market_overview_provider = (
            CoinGeckoMarketOverviewProvider()
        )

        asset_analysis_provider = (
            CryptoAssetAnalysisProvider()
        )

        effective_orchestrator = (
            RadarAICryptoV1ApplicationFactory
            .create(
                crypto_market_overview_provider=(
                    market_overview_provider
                ),
                crypto_asset_analysis_provider=(
                    asset_analysis_provider
                ),
            )
        )

    effective_answer_composer = (
        answer_composer
        or RadarAIAnswerComposer()
    )

    try:
        if request.asset_id is None:
            result = (
                effective_orchestrator
                .orchestrate(
                    request.question,
                )
            )
        else:
            result = (
                effective_orchestrator
                .orchestrate(
                    request.question,
                    asset_id=(
                        request.asset_id
                    ),
                )
            )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=_value_error_detail(
                error
            ),
        ) from error

    except (
        MarketOverviewDataError,
        AssetAnalysisDataError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    context = result.context

    answer = (
        effective_answer_composer.compose(
            context,
            result.question,
        )
    )

    return RadarAIQuestionResponse(
        question=result.question,
        intent=result.intent,
        market=result.market,
        supported=context.is_supported,
        source=context.source,
        source_version=(
            context.source_version
        ),
        answer=answer,
        items=[
            RadarAIContextItemResponse(
                key=item.key,
                title=item.title,
                content=item.content,
            )
            for item in context.items
        ],
    )