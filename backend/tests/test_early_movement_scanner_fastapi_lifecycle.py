from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.early_movement.scanner.scanner_fastapi_lifecycle import (
    early_movement_scanner_lifespan,
)


def test_lifecycle_keeps_runtime_disabled_by_default() -> None:
    app = FastAPI(
        lifespan=(
            early_movement_scanner_lifespan
        ),
    )

    @app.get("/runtime-status")
    def runtime_status():
        runtime = getattr(
            app.state,
            "early_movement_scanner_runtime",
            None,
        )

        return {
            "runtime_available": (
                runtime is not None
            ),
        }

    with TestClient(app) as client:
        response = client.get(
            "/runtime-status"
        )

        assert response.status_code == 200

        assert response.json() == {
            "runtime_available": False,
        }

    assert (
        app.state
        .early_movement_scanner_runtime
        is None
    )