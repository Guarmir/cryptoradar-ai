from fastapi import APIRouter

from app.push.push_registration_api import (
    PushDeviceRegistrationRequest,
    PushDeviceRegistrationResponse,
    register_push_device,
)


def create_push_router() -> APIRouter:
    router = APIRouter(
        tags=["push"],
    )

    @router.post(
        "/push/devices/register",
        response_model=(
            PushDeviceRegistrationResponse
        ),
    )
    def register_push_device_endpoint(
        request: PushDeviceRegistrationRequest,
    ):
        return register_push_device(
            request,
        )

    return router