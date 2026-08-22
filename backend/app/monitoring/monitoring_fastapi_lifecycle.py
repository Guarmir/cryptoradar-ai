from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)
from app.monitoring.monitoring_runtime_factory import (
    build_monitoring_runtime,
)


@asynccontextmanager
async def monitoring_lifespan(
    app: FastAPI,
):
    config = (
        MonitoringRuntimeConfig
        .from_environment()
    )

    runtime = build_monitoring_runtime(
        config,
    )

    if runtime is not None:
        runtime.start()

    app.state.monitoring_runtime = runtime

    try:
        yield

    finally:
        if runtime is not None:
            runtime.stop()

        app.state.monitoring_runtime = None