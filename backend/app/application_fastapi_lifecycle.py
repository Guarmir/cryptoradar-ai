from contextlib import (
    AsyncExitStack,
    asynccontextmanager,
)

from fastapi import FastAPI

from app.early_movement.scanner.scanner_fastapi_lifecycle import (
    early_movement_scanner_lifespan,
)
from app.monitoring.monitoring_fastapi_lifecycle import (
    monitoring_lifespan,
)


@asynccontextmanager
async def application_lifespan(
    app: FastAPI,
):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(
            monitoring_lifespan(
                app,
            )
        )

        await stack.enter_async_context(
            early_movement_scanner_lifespan(
                app,
            )
        )

        yield