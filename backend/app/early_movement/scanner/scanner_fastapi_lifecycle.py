from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.scanner.scanner_runtime_factory import (
    build_early_movement_scanner_runtime,
)


@asynccontextmanager
async def early_movement_scanner_lifespan(
    app: FastAPI,
):
    config = (
        EarlyMovementScannerRuntimeConfig
        .from_environment()
    )

    runtime = (
        build_early_movement_scanner_runtime(
            config,
        )
    )

    if runtime is not None:
        runtime.start()

    app.state.early_movement_scanner_runtime = (
        runtime
    )

    try:
        yield

    finally:
        if runtime is not None:
            runtime.stop()

        app.state.early_movement_scanner_runtime = (
            None
        )