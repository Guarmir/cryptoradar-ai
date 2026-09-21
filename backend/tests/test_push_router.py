from fastapi import FastAPI

from app.services.routes.push_router import (
    create_push_router,
)


def test_push_router_registers_existing_route() -> None:
    app = FastAPI()

    app.include_router(
        create_push_router()
    )

    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/push/devices/register"
        )
    ]

    assert len(matches) == 1
    assert "POST" in matches[0].methods