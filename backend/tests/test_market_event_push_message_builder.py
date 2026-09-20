from datetime import datetime, timezone

from app.monitoring.market_event import MarketEvent
from app.monitoring.monitoring_target import MonitoringTarget
from app.push.market_event_push_message_builder import (
    MarketEventPushMessageBuilder,
)


def _build_event(
    *,
    event_type: str,
    previous_price: float,
    current_price: float,
    price_change_percent: float,
) -> MarketEvent:
    return MarketEvent(
        target=MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        ),
        event_type=event_type,
        previous_price=previous_price,
        current_price=current_price,
        price_change_percent=price_change_percent,
        observed_at=datetime(
            2026,
            9,
            19,
            16,
            0,
            tzinfo=timezone.utc,
        ),
    )


def test_builds_upward_market_event_push_message():
    event = _build_event(
        event_type="price_move_up",
        previous_price=100.0,
        current_price=102.0,
        price_change_percent=2.0,
    )

    builder = MarketEventPushMessageBuilder()

    message = builder.build(event)

    assert message.title == "BTC: movimento de alta"

    assert (
        message.body
        == "O preço variou 2.00% desde a última observação."
    )

    assert message.data["type"] == "market_event"
    assert message.data["event_type"] == "price_move_up"
    assert message.data["symbol"] == "BTC"
    assert message.data["previous_price"] == "100.0"
    assert message.data["current_price"] == "102.0"
    assert message.data["price_change_percent"] == "2.0"

    assert (
        message.data["observed_at"]
        == "2026-09-19T16:00:00+00:00"
    )


def test_builds_downward_market_event_push_message():
    event = _build_event(
        event_type="price_move_down",
        previous_price=100.0,
        current_price=97.5,
        price_change_percent=-2.5,
    )

    builder = MarketEventPushMessageBuilder()

    message = builder.build(event)

    assert message.title == "BTC: movimento de queda"

    assert (
        message.body
        == "O preço variou 2.50% desde a última observação."
    )

    assert message.data["event_type"] == "price_move_down"
    assert message.data["price_change_percent"] == "-2.5"