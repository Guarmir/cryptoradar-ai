from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.radar_ai_router import (
    create_radar_ai_router,
)
from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
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
from app.services.routes.push_router import (
    create_push_router,
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

app.include_router(
    create_push_router()
)


@app.get("/")
def home():
    return {
        "status": "CryptoRadar AI online",
        "version": "2.1.0",
    }