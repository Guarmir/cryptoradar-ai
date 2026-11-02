
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.routes.extreme_movement_router import (
    create_extreme_movement_router,
)


def build_client():
    app = FastAPI()
    app.include_router(create_extreme_movement_router())
    return TestClient(app)


def make_record(
    *,
    discovery_price=None,
    discovery_price_at=None,
    latest_price=None,
    latest_price_at=None,
):
    now = datetime(2026, 10, 30, tzinfo=timezone.utc)

    return SimpleNamespace(
        entry=SimpleNamespace(
            coin_id="bitcoin",
            symbol="BTC",
            name="Bitcoin",
            assessment=SimpleNamespace(
                state="supported",
                direction="up",
                relevance_score=85.0,
                supporting_evidence_count=3,
            ),
            maturity=SimpleNamespace(
                level="developing",
            ),
        ),
        observation_status="active",
        missed_cycles=0,
        first_observed_at=now,
        last_observed_at=now,
        discovery_price=discovery_price,
        discovery_price_at=discovery_price_at,
        latest_price=latest_price,
        latest_price_at=latest_price_at,
    )


def get_response(records):
    with patch(
        "app.services.routes.extreme_movement_router."
        "EarlyMovementScannerRuntimeConfig.from_environment"
    ) as config_mock, patch(
        "app.services.routes.extreme_movement_router."
        "PostgreSQLExtremeMovementActiveStore"
    ) as store_mock:
        config_mock.return_value.database_url = "postgresql://test"
        store_mock.return_value.load_active.return_value = records

        return build_client().get("/extreme-movement/active")


def test_extreme_movement_active_returns_observations():
    response = get_response((make_record(),))

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["count"] == 1
    assert data["observations"][0]["coin_id"] == "bitcoin"
    assert data["observations"][0]["direction"] == "up"
    assert data["observations"][0]["relevance_score"] == 85.0


def test_extreme_movement_active_returns_prices():
    first = datetime(
        2026, 10, 30, 10, 0, tzinfo=timezone.utc
    )
    latest = datetime(
        2026, 10, 30, 10, 2, tzinfo=timezone.utc
    )

    response = get_response((
        make_record(
            discovery_price=0.0295,
            discovery_price_at=first,
            latest_price=0.0288,
            latest_price_at=latest,
        ),
    ))

    assert response.status_code == 200

    observation = response.json()["observations"][0]

    assert observation["discovery_price"] == 0.0295
    assert observation["discovery_price_at"] == first.isoformat()
    assert observation["latest_price"] == 0.0288
    assert observation["latest_price_at"] == latest.isoformat()


def test_extreme_movement_active_legacy_without_prices():
    response = get_response((make_record(),))

    assert response.status_code == 200

    observation = response.json()["observations"][0]

    assert observation["discovery_price"] is None
    assert observation["discovery_price_at"] is None
    assert observation["latest_price"] is None
    assert observation["latest_price_at"] is None


def test_extreme_movement_active_without_database():
    with patch(
        "app.services.routes.extreme_movement_router."
        "EarlyMovementScannerRuntimeConfig.from_environment"
    ) as config_mock:
        config_mock.return_value.database_url = None

        response = build_client().get("/extreme-movement/active")

    assert response.status_code == 503


def test_extreme_movement_active_database_failure():
    with patch(
        "app.services.routes.extreme_movement_router."
        "EarlyMovementScannerRuntimeConfig.from_environment"
    ) as config_mock, patch(
        "app.services.routes.extreme_movement_router."
        "PostgreSQLExtremeMovementActiveStore"
    ) as store_mock:
        config_mock.return_value.database_url = "postgresql://test"
        store_mock.return_value.load_active.side_effect = RuntimeError(
            "Database unavailable"
        )

        response = build_client().get("/extreme-movement/active")

    assert response.status_code == 503
