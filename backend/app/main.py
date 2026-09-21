import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.access.access_api import (
    AccessEntitlementsResponse,
    get_access_entitlements,
)
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
from app.services.market_data_service import (
    resolve_coin_id,
)
from app.services.price_alert import (
    monitor_price,
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


@app.get(
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


@app.get(
    "/alert/{coin}/{price}"
)
def start_alert(
    coin: str,
    price: float,
):
    coin_id = resolve_coin_id(
        coin
    )

    if not coin_id:
        return {
            "error": (
                "Moeda não encontrada"
            )
        }

    thread = threading.Thread(
        target=monitor_price,
        args=(
            coin_id,
            price,
        ),
        daemon=True,
    )

    thread.start()

    return {
        "status": "Alerta iniciado",
        "coin": coin.upper(),
        "coin_id": coin_id,
        "target_price": price,
    }