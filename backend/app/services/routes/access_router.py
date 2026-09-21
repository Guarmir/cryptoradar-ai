from fastapi import APIRouter

from app.access.access_api import (
    AccessEntitlementsResponse,
    get_access_entitlements,
)


def create_access_router() -> APIRouter:
    router = APIRouter(
        tags=["access"],
    )

    @router.get(
        "/access/entitlements/{installation_id}",
        response_model=(
            AccessEntitlementsResponse
        ),
    )
    def get_access_entitlements_endpoint(
        installation_id: str,
    ):
        return get_access_entitlements(
            installation_id,
        )

    return router