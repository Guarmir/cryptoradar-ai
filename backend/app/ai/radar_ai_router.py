from typing import Optional

from fastapi import APIRouter

from app.ai.radar_ai_api import (
    RadarAIQuestionRequest,
    RadarAIQuestionResponse,
    ask_radar_ai,
)
from app.ai.radar_ai_orchestrator import (
    RadarAIOrchestrator,
)


def create_radar_ai_router(
    *,
    orchestrator: Optional[
        RadarAIOrchestrator
    ] = None,
) -> APIRouter:
    router = APIRouter(
        prefix="/ai/radar",
        tags=["radar-ai"],
    )

    @router.post(
        "/ask",
        response_model=RadarAIQuestionResponse,
    )
    def ask(
        request: RadarAIQuestionRequest,
    ) -> RadarAIQuestionResponse:
        return ask_radar_ai(
            request,
            orchestrator=orchestrator,
        )

    return router