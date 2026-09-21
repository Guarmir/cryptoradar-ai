from fastapi import FastAPI

from app.services.routes.asset_router import (
    create_asset_router,
)


def test_asset_router_registers_existing_routes() -> None:
    app = FastAPI()

    app.include_router(
        create_asset_router()
    )

    routes = {
        route.path: route.methods
        for route in app.routes
    }

    assert "/analysis/{symbol}" in routes
    assert "/price/{coin}" in routes
    assert "/score/{coin}" in routes
    assert "/chart/{coin}" in routes
    assert "/asset/{coin}" in routes

    assert "GET" in routes[
        "/analysis/{symbol}"
    ]

    assert "GET" in routes[
        "/price/{coin}"
    ]

    assert "GET" in routes[
        "/score/{coin}"
    ]

    assert "GET" in routes[
        "/chart/{coin}"
    ]

    assert "GET" in routes[
        "/asset/{coin}"
    ]