from types import SimpleNamespace

from fastapi.testclient import (
    TestClient,
)

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner import (
    EarlyMovementScanner,
)
from app.main import app


def _fake_scan(
    self,
):
    asset = SimpleNamespace(
        coin_id="uniswap",
        symbol="UNI",
        name="Uniswap",
        current_price=12.5,
        price_change_percentage_24h=4.2,
        market_cap=7_500_000_000,
        total_volume=650_000_000,
        market_cap_rank=25,
    )

    candidate = SimpleNamespace(
        asset=asset,
    )

    evidence = SimpleNamespace(
        state=(
            EarlyMovementState.EARLY_MOVEMENT
        ),
        liquidity_score=86.0,
        price_acceleration=2.4,
        abnormal_volume_ratio=1.8,
        volatility_expansion=1.5,
        persistence_score=72.0,
        support_break=False,
        resistance_break=True,
        retest_confirmed=True,
        false_breakout_risk=18.0,
        reason=(
            "Movimento inicial com "
            "confirmações relevantes."
        ),
        invalidation_reason=(
            "Perda do nível de rompimento."
        ),
    )

    breakout_confirmation = (
        SimpleNamespace(
            breakout_direction="up",
        )
    )

    analysis = SimpleNamespace(
        evidence=evidence,
        breakout_confirmation=(
            breakout_confirmation
        ),
    )

    analysis_result = SimpleNamespace(
        candidate=candidate,
        analysis=analysis,
    )

    ranked = SimpleNamespace(
        rank=1,
        relevance_score=84.5,
        result=analysis_result,
    )

    return SimpleNamespace(
    universe_size=100,
    candidate_count=10,
    analyzed_count=10,
    successful_analysis_count=9,
    analysis_results=(
        SimpleNamespace(
            candidate=SimpleNamespace(
                coin_id="uniswap",
                symbol="UNI",
                name="Uniswap",
            ),
            analysis=analysis,
            chart_available=True,
            error=None,
        ),
    ),
    ranked_results=(
        ranked,
    ),
)


def _fake_scan_failure(
    self,
):
    raise RuntimeError(
        "temporary scanner failure"
    )


def test_early_movement_scan_reaches_http(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        EarlyMovementScanner,
        "scan",
        _fake_scan,
    )

    client = TestClient(
        app,
    )

    response = client.get(
        "/early-movement/scan",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"

    assert (
        body["universe_size"]
        == 100
    )

    assert (
        body["candidate_count"]
        == 10
    )

    assert (
        body["analyzed_count"]
        == 10
    )

    assert (
        body[
            "successful_analysis_count"
        ]
        == 9
    )

    assert (
        body["signal_count"]
        == 1
    )

    signal = body[
        "signals"
    ][0]

    assert signal["rank"] == 1

    assert (
        signal["coin_id"]
        == "uniswap"
    )

    assert (
        signal["symbol"]
        == "UNI"
    )

    assert (
        signal["state"]
        == "early_movement"
    )

    assert (
        signal["relevance_score"]
        == 84.5
    )

    assert (
        signal["liquidity_score"]
        == 86.0
    )

    assert (
        signal["resistance_break"]
        is True
    )

    assert (
        signal["retest_confirmed"]
        is True
    )

    assert (
        signal["breakout_direction"]
        == "up"
    )


def test_early_movement_scan_returns_safe_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        EarlyMovementScanner,
        "scan",
        _fake_scan_failure,
    )

    client = TestClient(
        app,
    )

    response = client.get(
        "/early-movement/scan",
    )

    assert response.status_code == 503

    body = response.json()

    assert (
        body["detail"]
        == (
            "Scanner de mercado "
            "temporariamente indisponível."
        )
    )

def test_early_movement_status_reaches_http() -> None:
    client = TestClient(
        app,
    )

    response = client.get(
        "/early-movement/status",
    )

    assert response.status_code == 200

    body = response.json()

    assert "enabled" in body
    assert "running" in body
    assert "interval_seconds" in body
    assert "last_cycle_available" in body
    assert "last_scheduler_error" in body