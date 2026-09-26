from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.services.routes.asset_router as asset_router_module
from app.services.routes.asset_router import (
    create_asset_router,
)


def _build_client() -> TestClient:
    app = FastAPI()

    app.include_router(
        create_asset_router()
    )

    return TestClient(app)


def _market_data() -> dict:
    return {
        "id": "cluster-protocol",
        "symbol": "cp",
        "name": "Cluster Protocol",
        "current_price": 0.01408755,
        "market_cap": 19_275_052,
        "total_volume": 23_689_212,
        "price_change_percentage_24h": (
            7.53933
        ),
        "image": None,
        "last_updated": (
            "2026-09-26T00:00:00Z"
        ),
    }


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


def test_score_route_uses_ai_score_engine(
    monkeypatch,
) -> None:
    market = _market_data()

    monkeypatch.setattr(
        asset_router_module,
        "resolve_coin_id",
        lambda coin: "cluster-protocol",
    )

    monkeypatch.setattr(
        asset_router_module,
        "get_market_data",
        lambda coin_id: market,
    )

    monkeypatch.setattr(
        asset_router_module,
        "calculate_ai_score",
        lambda change_24h, volume, market_cap: 57,
    )

    monkeypatch.setattr(
        asset_router_module,
        "get_ai_signal",
        lambda score: "neutral",
    )

    client = _build_client()

    response = client.get(
        "/score/cluster-protocol"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["coin_id"] == (
        "cluster-protocol"
    )
    assert payload["name"] == (
        "Cluster Protocol"
    )
    assert payload["score"] == 57
    assert payload["signal"] == "neutral"


def test_asset_route_uses_ai_score_engine(
    monkeypatch,
) -> None:
    market = _market_data()

    monkeypatch.setattr(
        asset_router_module,
        "resolve_coin_id",
        lambda coin: "cluster-protocol",
    )

    monkeypatch.setattr(
        asset_router_module,
        "get_market_data",
        lambda coin_id: market,
    )

    monkeypatch.setattr(
        asset_router_module,
        "get_chart_data",
        lambda coin_id, days: {
            "prices": [],
        },
    )

    monkeypatch.setattr(
        asset_router_module,
        "calculate_ai_score",
        lambda change_24h, volume, market_cap: 57,
    )

    monkeypatch.setattr(
        asset_router_module,
        "get_ai_signal",
        lambda score: "neutral",
    )

    client = _build_client()

    response = client.get(
        "/asset/cluster-protocol"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["coin_id"] == (
        "cluster-protocol"
    )
    assert payload["name"] == (
        "Cluster Protocol"
    )
    assert payload["score"] == 57
    assert payload["signal"] == "neutral"
    assert payload["days"] == 1