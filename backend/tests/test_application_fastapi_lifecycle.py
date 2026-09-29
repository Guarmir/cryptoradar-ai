from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application_fastapi_lifecycle import (
    application_lifespan,
)


def test_application_lifespan_exposes_runtimes() -> None:
    app = FastAPI(
        lifespan=application_lifespan,
    )

    @app.get("/runtime-status")
    def runtime_status():
        return {
            "monitoring_runtime_available": (
                getattr(
                    app.state,
                    "monitoring_runtime",
                    None,
                )
                is not None
            ),
            (
                "early_movement_scanner_"
                "runtime_available"
            ): (
                getattr(
                    app.state,
                    (
                        "early_movement_"
                        "scanner_runtime"
                    ),
                    None,
                )
                is not None
            ),
        }

    with TestClient(app) as client:
        response = client.get(
            "/runtime-status"
        )

        assert response.status_code == 200

        assert response.json() == {
            (
                "monitoring_runtime_"
                "available"
            ): False,
            (
                "early_movement_scanner_"
                "runtime_available"
            ): False,
        }

    assert (
        app.state.monitoring_runtime
        is None
    )

    assert (
        app.state
        .early_movement_scanner_runtime
        is None
    )