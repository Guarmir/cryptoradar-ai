from datetime import datetime, timedelta, timezone

from app.monitoring.market_event import MarketEvent
from app.monitoring.monitoring_target import MonitoringTarget
from app.push.market_event_push_cooldown import (
    MarketEventPushCooldown,
)
from app.push.market_event_push_message_builder import (
    MarketEventPushMessageBuilder,
)
from app.push.market_event_push_service import (
    MarketEventPushService,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
    PushDeliveryOutcome,
)


class _FakeDeliveryService:
    def __init__(
        self,
        result: PushDeliveryBatchResult,
    ):
        self._result = result
        self.messages = []

    def deliver(
        self,
        message,
    ) -> PushDeliveryBatchResult:
        self.messages.append(
            message,
        )

        return self._result


def _build_event(
    *,
    event_type: str = "price_move_up",
    observed_at: datetime,
) -> MarketEvent:
    if event_type == "price_move_up":
        current_price = 102.0
        change = 2.0
    else:
        current_price = 98.0
        change = -2.0

    return MarketEvent(
        target=MonitoringTarget(
            symbol="BTC",
            coin_id="bitcoin",
        ),
        event_type=event_type,
        previous_price=100.0,
        current_price=current_price,
        price_change_percent=change,
        observed_at=observed_at,
    )


def _successful_result() -> PushDeliveryBatchResult:
    return PushDeliveryBatchResult(
        outcomes=(
            PushDeliveryOutcome(
                installation_id="device-1",
                delivered=True,
            ),
        ),
    )


def _failed_result() -> PushDeliveryBatchResult:
    return PushDeliveryBatchResult(
        outcomes=(
            PushDeliveryOutcome(
                installation_id="device-1",
                delivered=False,
                error_code="test_failure",
            ),
        ),
    )


def test_successful_delivery_activates_cooldown():
    delivery_service = _FakeDeliveryService(
        _successful_result(),
    )

    service = MarketEventPushService(
        cooldown=MarketEventPushCooldown(
            cooldown_seconds=300,
        ),
        message_builder=(
            MarketEventPushMessageBuilder()
        ),
        delivery_service=delivery_service,
    )

    first_at = datetime(
        2026,
        9,
        19,
        16,
        0,
        tzinfo=timezone.utc,
    )

    first = _build_event(
        observed_at=first_at,
    )

    first_result = service.deliver(
        first,
    )

    assert first_result is not None
    assert first_result.delivered == 1
    assert len(delivery_service.messages) == 1

    repeated = _build_event(
        observed_at=first_at + timedelta(
            seconds=60,
        ),
    )

    repeated_result = service.deliver(
        repeated,
    )

    assert repeated_result is None
    assert len(delivery_service.messages) == 1


def test_failed_delivery_does_not_activate_cooldown():
    delivery_service = _FakeDeliveryService(
        _failed_result(),
    )

    service = MarketEventPushService(
        cooldown=MarketEventPushCooldown(
            cooldown_seconds=300,
        ),
        message_builder=(
            MarketEventPushMessageBuilder()
        ),
        delivery_service=delivery_service,
    )

    first_at = datetime(
        2026,
        9,
        19,
        16,
        0,
        tzinfo=timezone.utc,
    )

    first = _build_event(
        observed_at=first_at,
    )

    first_result = service.deliver(
        first,
    )

    assert first_result is not None
    assert first_result.delivered == 0

    repeated = _build_event(
        observed_at=first_at + timedelta(
            seconds=60,
        ),
    )

    repeated_result = service.deliver(
        repeated,
    )

    assert repeated_result is not None
    assert len(delivery_service.messages) == 2


def test_opposite_direction_can_be_delivered():
    delivery_service = _FakeDeliveryService(
        _successful_result(),
    )

    service = MarketEventPushService(
        cooldown=MarketEventPushCooldown(
            cooldown_seconds=300,
        ),
        message_builder=(
            MarketEventPushMessageBuilder()
        ),
        delivery_service=delivery_service,
    )

    first_at = datetime(
        2026,
        9,
        19,
        16,
        0,
        tzinfo=timezone.utc,
    )

    upward = _build_event(
        event_type="price_move_up",
        observed_at=first_at,
    )

    service.deliver(
        upward,
    )

    downward = _build_event(
        event_type="price_move_down",
        observed_at=first_at + timedelta(
            seconds=60,
        ),
    )

    result = service.deliver(
        downward,
    )

    assert result is not None
    assert result.delivered == 1
    assert len(delivery_service.messages) == 2