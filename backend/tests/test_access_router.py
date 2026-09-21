from fastapi import FastAPI

from app.services.routes.access_router import (
    create_access_router,
)


def test_access_router_registers_existing_route() -> None:
    app = FastAPI()

    app.include_router(
        create_access_router()
    )

    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/access/entitlements/{installation_id}"
        )
    ]

    assert len(matches) == 1
    assert "GET" in matches[0].methods