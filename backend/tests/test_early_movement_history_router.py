
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.routes.early_movement_scanner_router import (
    create_early_movement_scanner_router,
)


def create_client():
    app = FastAPI()
    app.include_router(
        create_early_movement_scanner_router()
    )
    return TestClient(app)


def test_history_returns_saved_signals():
    client = create_client()

    expected = {
        "status": "ok",
        "signal_count": 1,
        "signals": [
            {
                "coin_id": "bitcoin",
                "symbol": "btc",
            }
        ],
    }

    with (
        patch.dict(
            "os.environ",
            {
                "CRYPTORADAR_DATABASE_URL": "postgresql://test",
            },
        ),
        patch(
            "app.services.routes.early_movement_scanner_router."
            "EarlyMovementScannerSignalHistoryQueryService"
        ) as service_class,
    ):
        service_class.return_value.load_recent.return_value = (
            expected
        )

        response = client.get(
            "/early-movement/history?limit=20"
        )

    assert response.status_code == 200
    assert response.json() == expected
    service_class.return_value.load_recent.assert_called_once_with(
        limit=20
    )


def test_history_rejects_invalid_limit():
    client = create_client()

    response = client.get(
        "/early-movement/history?limit=101"
    )

    assert response.status_code == 422


def test_history_without_database_returns_503():
    client = create_client()

    with patch.dict(
        "os.environ",
        {"CRYPTORADAR_DATABASE_URL": ""},
    ):
        response = client.get(
            "/early-movement/history"
        )

    assert response.status_code == 503
