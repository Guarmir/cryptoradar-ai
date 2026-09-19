from datetime import datetime, timezone

import pytest

from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
)
from app.monitoring.monitoring_engine import MonitoringEngine
from app.monitoring.monitoring_observation import (
    MonitoringObservation,
)
from app.monitoring.monitoring_target import MonitoringTarget


def _create_engine() -> MonitoringEngine:
    engine = MonitoringEngine()

    engine.register_target(
        MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        )
    )

    return engine


def _observe(
    engine: MonitoringEngine,
    *,
    price: float,
    minute: int,
):
    return engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=price,
            observed_at=datetime(
                2026,
                9,
                18,
                1,
                minute,
                tzinfo=timezone.utc,
            ),
        )
    )


def test_rejects_non_positive_minimum_change():
    for invalid_value in (
        0,
        -1,
    ):
        with pytest.raises(ValueError):
            MarketEventEvaluator(
                minimum_price_change_percent=invalid_value,
            )


def test_first_observation_does_not_generate_event():
    engine = _create_engine()

    result = _observe(
        engine,
        price=100.0,
        minute=0,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    assert evaluator.evaluate(result) == ()


def test_change_below_threshold_does_not_generate_event():
    engine = _create_engine()

    _observe(
        engine,
        price=100.0,
        minute=0,
    )

    result = _observe(
        engine,
        price=100.5,
        minute=1,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    assert evaluator.evaluate(result) == ()


def test_upward_change_generates_price_move_up_event():
    engine = _create_engine()

    _observe(
        engine,
        price=100.0,
        minute=0,
    )

    result = _observe(
        engine,
        price=101.5,
        minute=1,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    events = evaluator.evaluate(result)

    assert len(events) == 1

    event = events[0]

    assert event.symbol == "BTC"
    assert event.event_type == "price_move_up"
    assert event.is_upward
    assert not event.is_downward
    assert event.previous_price == 100.0
    assert event.current_price == 101.5
    assert event.price_change_percent == pytest.approx(1.5)


def test_downward_change_generates_price_move_down_event():
    engine = _create_engine()

    _observe(
        engine,
        price=100.0,
        minute=0,
    )

    result = _observe(
        engine,
        price=98.0,
        minute=1,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    events = evaluator.evaluate(result)

    assert len(events) == 1

    event = events[0]

    assert event.symbol == "BTC"
    assert event.event_type == "price_move_down"
    assert event.is_downward
    assert not event.is_upward
    assert event.previous_price == 100.0
    assert event.current_price == 98.0
    assert event.price_change_percent == pytest.approx(-2.0)


def test_change_equal_to_threshold_generates_event():
    engine = _create_engine()

    _observe(
        engine,
        price=100.0,
        minute=0,
    )

    result = _observe(
        engine,
        price=101.0,
        minute=1,
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
    )

    events = evaluator.evaluate(result)

    assert len(events) == 1
    assert events[0].event_type == "price_move_up"
    assert events[0].price_change_percent == pytest.approx(1.0)

def test_stale_previous_observation_does_not_generate_event():
    engine = MonitoringEngine()

    engine.register_target(
        MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        )
    )

    engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=100.0,
            observed_at=datetime(
                2026,
                9,
                19,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    result = engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=110.0,
            observed_at=datetime(
                2026,
                9,
                19,
                10,
                10,
                tzinfo=timezone.utc,
            ),
        )
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
        maximum_observation_gap_seconds=180,
    )

    assert evaluator.evaluate(result) == ()


def test_recent_previous_observation_can_generate_event():
    engine = MonitoringEngine()

    engine.register_target(
        MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        )
    )

    engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=100.0,
            observed_at=datetime(
                2026,
                9,
                19,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    )

    result = engine.observe(
        MonitoringObservation(
            symbol="BTC",
            price=102.0,
            observed_at=datetime(
                2026,
                9,
                19,
                10,
                1,
                tzinfo=timezone.utc,
            ),
        )
    )

    evaluator = MarketEventEvaluator(
        minimum_price_change_percent=1.0,
        maximum_observation_gap_seconds=180,
    )

    events = evaluator.evaluate(result)

    assert len(events) == 1
    assert events[0].event_type == "price_move_up"