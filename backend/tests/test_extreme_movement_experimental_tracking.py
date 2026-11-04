
from datetime import datetime, timedelta, timezone

import pytest

from app.early_movement.extreme_movement.extreme_movement_experimental_tracking import (
    ExtremeMovementExperimentalTrackingEvaluator,
)


BASE_TIME = datetime(2026, 11, 3, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def evaluator():
    return ExtremeMovementExperimentalTrackingEvaluator()


@pytest.fixture
def tracking(evaluator):
    return evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )


def test_start_records_initial_signal(tracking):
    assert tracking.coin_id == "irys"
    assert tracking.initial_price == 1.0
    assert tracking.latest_price == 1.0
    assert tracking.initial_direction == "up"
    assert tracking.latest_direction == "up"
    assert tracking.initial_score == 65.0
    assert tracking.observation_count == 1
    assert tracking.status == "active"
    assert tracking.price_change_pct == 0.0


def test_update_tracks_price_and_score(evaluator, tracking):
    updated = evaluator.update(
        tracking,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.05,
        direction="up",
        score=80.0,
        evidence_count=3,
        state="priority",
    )

    assert updated.latest_price == 1.05
    assert updated.latest_score == 80.0
    assert updated.price_change_pct == pytest.approx(5.0)
    assert updated.maximum_rise_pct == pytest.approx(5.0)
    assert updated.observation_count == 2

    # O registro anterior permanece imutavel.
    assert tracking.latest_price == 1.0


def test_tracks_reversal_and_drawdown(evaluator, tracking):
    rising = evaluator.update(
        tracking,
        observed_at=BASE_TIME + timedelta(minutes=20),
        price=1.06,
        direction="up",
        score=85.0,
        evidence_count=3,
        state="priority",
    )

    falling = evaluator.update(
        rising,
        observed_at=BASE_TIME + timedelta(minutes=40),
        price=0.97,
        direction="down",
        score=35.0,
        evidence_count=2,
        state="strengthening",
    )

    assert falling.latest_direction == "down"
    assert falling.price_change_pct == pytest.approx(-3.0)
    assert falling.maximum_rise_pct == pytest.approx(6.0)
    assert falling.maximum_fall_pct == pytest.approx(-3.0)
    assert falling.observation_count == 3


def test_close_preserves_final_result(evaluator, tracking):
    closed = evaluator.close(
        tracking,
        closed_at=BASE_TIME + timedelta(minutes=60),
        reason="movement_invalidated",
    )

    assert closed.status == "closed"
    assert closed.close_reason == "movement_invalidated"
    assert closed.closed_at == BASE_TIME + timedelta(minutes=60)
    assert closed.initial_price == 1.0

    with pytest.raises(ValueError, match="encerrado"):
        evaluator.update(
            closed,
            observed_at=BASE_TIME + timedelta(minutes=80),
            price=1.10,
            direction="up",
            score=90.0,
            evidence_count=3,
            state="priority",
        )


@pytest.mark.parametrize(
    "invalid_price",
    [0.0, -1.0, float("nan"), float("inf")],
)
def test_rejects_invalid_prices(evaluator, invalid_price):
    with pytest.raises(ValueError, match="Preco invalido"):
        evaluator.start(
            coin_id="irys",
            observed_at=BASE_TIME,
            price=invalid_price,
            direction="up",
            score=50.0,
            evidence_count=2,
            state="priority",
        )


def test_rejects_out_of_order_observations(evaluator, tracking):
    with pytest.raises(ValueError, match="fora de ordem"):
        evaluator.update(
            tracking,
            observed_at=BASE_TIME,
            price=1.02,
            direction="up",
            score=60.0,
            evidence_count=2,
            state="priority",
        )


def test_rejects_invalid_score(evaluator):
    with pytest.raises(ValueError, match="Score invalido"):
        evaluator.start(
            coin_id="irys",
            observed_at=BASE_TIME,
            price=1.0,
            direction="up",
            score=101.0,
            evidence_count=2,
            state="priority",
        )


def test_rejects_naive_datetime(evaluator):
    with pytest.raises(ValueError, match="fuso"):
        evaluator.start(
            coin_id="irys",
            observed_at=datetime(2026, 11, 3, 10, 0),
            price=1.0,
            direction="up",
            score=50.0,
            evidence_count=2,
            state="priority",
        )
