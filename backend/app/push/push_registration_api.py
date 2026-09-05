from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.push.postgresql_push_device_store import (
    PostgreSQLPushDeviceStore,
)
from app.push.push_device_registration_service import (
    PushDeviceRegistrationService,
)
from app.push.push_device_store import (
    PushDeviceStore,
)
from app.push.push_registration_config import (
    PushRegistrationConfig,
)


class PushDeviceRegistrationRequest(
    BaseModel
):
    installation_id: str = Field(
        min_length=1,
        max_length=200,
    )

    fcm_token: str = Field(
        min_length=1,
        max_length=4096,
    )

    firebase_installation_id: Optional[
        str
    ] = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    platform: str = Field(
        default="android",
        min_length=1,
        max_length=32,
    )


class PushDeviceRegistrationResponse(
    BaseModel
):
    status: str
    installation_id: str
    platform: str
    enabled: bool


def register_push_device(
    request: PushDeviceRegistrationRequest,
    *,
    config: Optional[
        PushRegistrationConfig
    ] = None,
    store: Optional[
        PushDeviceStore
    ] = None,
) -> PushDeviceRegistrationResponse:
    effective_config = (
        config
        if config is not None
        else PushRegistrationConfig
        .from_environment()
    )

    if not effective_config.enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "O registro de dispositivos "
                "push está desabilitado."
            ),
        )

    effective_store = store

    if effective_store is None:
        effective_store = (
            PostgreSQLPushDeviceStore(
                database_url=(
                    effective_config.database_url
                    or ""
                ),
                scope_key=(
                    effective_config.scope_key
                    or ""
                ),
            )
        )

    service = (
        PushDeviceRegistrationService(
            store=effective_store,
        )
    )

    try:
        device = service.register(
            installation_id=(
                request.installation_id
            ),
            fcm_token=request.fcm_token,
            firebase_installation_id=(
                request.firebase_installation_id
            ),
            platform=request.platform,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(
                error,
            ),
        ) from error

    return PushDeviceRegistrationResponse(
        status="registered",
        installation_id=(
            device.installation_id
        ),
        platform=device.platform,
        enabled=device.enabled,
    )