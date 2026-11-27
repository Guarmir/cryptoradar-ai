from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from app.monitoring.individual_monitoring_api import create_individual_monitoring_service


class AddMonitoringAssetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    coin_id: str = Field(min_length=1, max_length=200)


class MonitoringIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Literal["opportunity", "position"]
    side: Literal["long", "short"] | None = None


def create_individual_monitoring_router(service_factory=None):
    router = APIRouter(prefix='/monitoring/individual', tags=['individual-monitoring'])

    def invoke(operation, **kwargs):
        try:
            service = (service_factory or create_individual_monitoring_service)()
            return getattr(service, operation)(**kwargs)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(503, 'Monitoramento temporariamente indisponivel.') from None

    @router.get('/{installation_id}/assets')
    def list_assets(installation_id: str, response: Response,
                    authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return invoke('list_assets', authorization=authorization, installation_id=installation_id)

    @router.post('/{installation_id}/assets')
    def add_asset(installation_id: str, request: AddMonitoringAssetRequest, response: Response,
                  authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return invoke('add_asset', authorization=authorization, installation_id=installation_id,
                      coin_id=request.coin_id)

    @router.delete('/{installation_id}/assets/{coin_id}')
    def remove_asset(installation_id: str, coin_id: str, response: Response,
                     authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return invoke('remove_asset', authorization=authorization, installation_id=installation_id,
                      coin_id=coin_id)

    @router.get('/{installation_id}/assets/{coin_id}/intent')
    def get_intent(installation_id: str, coin_id: str, response: Response,
                   authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return invoke('get_intent', authorization=authorization,
                      installation_id=installation_id, coin_id=coin_id)

    @router.put('/{installation_id}/assets/{coin_id}/intent')
    def set_intent(installation_id: str, coin_id: str, request: MonitoringIntentRequest,
                   response: Response, authorization: str | None = Header(default=None)):
        response.headers['Cache-Control'] = 'no-store'
        return invoke('set_intent', authorization=authorization,
                      installation_id=installation_id, coin_id=coin_id,
                      intent=request.intent, side=request.side)

    return router
