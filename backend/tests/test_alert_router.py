from fastapi import FastAPI

from app.services.routes.alert_router import (
    create_alert_router,
)


def test_alert_router_registers_existing_route() -> None:
    app = FastAPI()

    app.include_router(
        create_alert_router()
    )

    matches = [
        route
        for route in app.routes
        if (
            route.path
            == "/alert/{coin}/{price}"
        )
    ]

    assert len(matches) == 1
    assert "GET" in matches[0].methods