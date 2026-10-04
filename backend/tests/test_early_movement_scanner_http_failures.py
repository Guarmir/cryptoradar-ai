from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.early_movement.scanner import (
    EarlyMovementScanner,
)
from app.main import app


def _fake_scan_with_analysis_failures(
    self,
):
    successful_candidate = SimpleNamespace(
        coin_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
    )

    failed_candidate_one = SimpleNamespace(
        coin_id="cardano",
        symbol="ADA",
        name="Cardano",
    )

    failed_candidate_two = SimpleNamespace(
        coin_id="dogecoin",
        symbol="DOGE",
        name="Dogecoin",
    )

    successful_result = SimpleNamespace(
        candidate=successful_candidate,
        analysis=SimpleNamespace(),
        chart_available=True,
        error=None,
    )

    failed_result_one = SimpleNamespace(
        candidate=failed_candidate_one,
        analysis=None,
        chart_available=False,
        error="chart_data_unavailable",
    )

    failed_result_two = SimpleNamespace(
        candidate=failed_candidate_two,
        analysis=None,
        chart_available=False,
        error="chart_load_failed",
    )

    return SimpleNamespace(
        universe_size=100,
        candidate_count=3,
        analyzed_count=3,
        successful_analysis_count=1,
        analysis_results=(
            successful_result,
            failed_result_one,
            failed_result_two,
        ),
        ranked_results=(),
    )


def test_scan_exposes_analysis_failures(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        EarlyMovementScanner,
        "scan",
        _fake_scan_with_analysis_failures,
    )

    client = TestClient(
        app,
    )

    response = client.get(
        "/early-movement/scan",
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["analysis_failure_count"]
        == 2
    )

    assert body["analysis_failures"] == [
        {
            "coin_id": "cardano",
            "symbol": "ADA",
            "name": "Cardano",
            "chart_available": False,
            "error": "chart_data_unavailable",
        },
        {
            "coin_id": "dogecoin",
            "symbol": "DOGE",
            "name": "Dogecoin",
            "chart_available": False,
            "error": "chart_load_failed",
        },
    ]