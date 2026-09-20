from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.access.access_api_config import (
    AccessApiConfig,
)
from app.access.access_entitlements_config import (
    AccessEntitlementsConfig,
)
from app.access.access_entitlements_resolver import (
    AccessEntitlementsResolver,
)
from app.access.access_plan_resolver import (
    AccessPlanResolver,
)
from app.access.access_policy import (
    AccessPolicy,
)
from app.access.access_service import (
    AccessService,
)
from app.access.postgresql_access_plan_store import (
    PostgreSQLAccessPlanStore,
)


class AccessEntitlementsResponse(
    BaseModel
):
    plan: str
    monitored_asset_limit: int
    automatic_market_alerts: bool
    futures_enabled: bool


def get_access_entitlements(
    installation_id: str,
    *,
    config: Optional[
        AccessApiConfig
    ] = None,
    service: Optional[
        AccessService
    ] = None,
) -> AccessEntitlementsResponse:
    effective_config = (
        config
        if config is not None
        else AccessApiConfig
        .from_environment()
    )

    if not effective_config.enabled:
        raise HTTPException(
            status_code=503,
            detail=(
                "O controle de acesso "
                "esta desabilitado."
            ),
        )

    effective_service = service

    if effective_service is None:
        store = PostgreSQLAccessPlanStore(
            database_url=(
                effective_config.database_url
                or ""
            ),
            scope_key=(
                effective_config.scope_key
                or ""
            ),
        )

        plan_resolver = (
            AccessPlanResolver(
                store=store,
            )
        )

        entitlements_config = (
            AccessEntitlementsConfig
            .from_environment()
        )

        entitlements_resolver = (
            AccessEntitlementsResolver(
                plan_resolver=plan_resolver,
                free_entitlements=(
                    entitlements_config.free
                ),
                pro_entitlements=(
                    entitlements_config.pro
                ),
            )
        )

        effective_service = AccessService(
            entitlements_resolver=(
                entitlements_resolver
            ),
            policy=AccessPolicy(),
        )

    try:
        entitlements = (
            effective_service
            .entitlements_for(
                installation_id,
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(
                error,
            ),
        ) from error

    return AccessEntitlementsResponse(
        plan=entitlements.plan,
        monitored_asset_limit=(
            entitlements.monitored_asset_limit
        ),
        automatic_market_alerts=(
            entitlements.automatic_market_alerts
        ),
        futures_enabled=(
            entitlements.futures_enabled
        ),
    )