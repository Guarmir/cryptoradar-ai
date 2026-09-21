from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.radar_ai_router import (
    create_radar_ai_router,
)
from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
)
from app.push.push_registration_api import (
    PushDeviceRegistrationRequest,
    PushDeviceRegistrationResponse,
    register_push_device,
)
from app.services.routes.access_router import (
    create_access_router,
)
from app.services.routes.alert_router import (
    create_alert_router,
)
from app.services.routes.asset_router import (
    create_asset_router,
)


app = FastAPI(
    title="CryptoRadar AI",
    version="2.1.0",
    lifespan=monitoring_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    create_radar_ai_router()
)

app.include_router(
    create_asset_router()
)

app.include_router(
    create_alert_router()
)

app.include_router(
    create_access_router()
)


@app.post(
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


@app.get("/")
def home():
    return {
        "status": "CryptoRadar AI online",
        "version": "2.1.0",
    }