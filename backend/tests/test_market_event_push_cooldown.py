from datetime import datetime, timedelta, timezone

import pytest

from app.monitoring.market_event import MarketEvent
from app.monitoring.monitoring_target import MonitoringTarget
from app.push.market_event_push_cooldown import (
    MarketEventPushCooldown,
)


def _build_event(
    *,
    symbol: str = "BTC",
    event_type: str = "price_move_up",
    observed_at: datetime,
) -> MarketEvent:
    if event_type == "price_move_up":
        previous_price = 100.0
        current_price = 102.0
        price_change_percent = 2.0
    else:
        previous_price = 100.0
        current_price = 98.0
        price_change_percent = -2.0

    return MarketEvent(
        target=MonitoringTarget(
            symbol=symbol,
            coin_id="bitcoin",
        ),
        event_type=event_type,
        previous_price=previous_price,
        current_price=current_price,
        price_change_percent=price_change_percent,
        observed_at=observed_at,
    )


def test_rejects_non_positive_cooldown():
    for value in (0, -1):
        with pytest.raises(ValueError):
            MarketEventPushCooldown(
                cooldown_seconds=value,
            )


def test_first_event_can_be_delivered():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
    )

    event = _build_event(
        observed_at=datetime(
            2026,
            9,
            19,
            16,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert cooldown.can_deliver(event)


def test_same_event_direction_is_blocked_during_cooldown():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
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

    cooldown.mark_delivered(first)

    repeated = _build_event(
        observed_at=first_at + timedelta(
            seconds=120,
        ),
    )

    assert not cooldown.can_deliver(
        repeated,
    )


def test_same_event_direction_is_allowed_after_cooldown():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
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

    cooldown.mark_delivered(first)

    later = _build_event(
        observed_at=first_at + timedelta(
            seconds=300,
        ),
    )

    assert cooldown.can_deliver(
        later,
    )


def test_opposite_direction_has_independent_cooldown():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
    )

    observed_at = datetime(
        2026,
        9,
        19,
        16,
        0,
        tzinfo=timezone.utc,
    )

    upward = _build_event(
        event_type="price_move_up",
        observed_at=observed_at,
    )

    cooldown.mark_delivered(
        upward,
    )

    downward = _build_event(
        event_type="price_move_down",
        observed_at=observed_at + timedelta(
            seconds=60,
        ),
    )

    assert cooldown.can_deliver(
        downward,
    )


def test_different_assets_have_independent_cooldowns():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
    )

    observed_at = datetime(
        2026,
        9,
        19,
        16,
        0,
        tzinfo=timezone.utc,
    )

    btc = _build_event(
        symbol="BTC",
        observed_at=observed_at,
    )

    cooldown.mark_delivered(
        btc,
    )

    eth = _build_event(
        symbol="ETH",
        observed_at=observed_at + timedelta(
            seconds=60,
        ),
    )

    assert cooldown.can_deliver(
        eth,
    )


def test_older_event_is_not_delivered_after_newer_delivery():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
    )

    delivered_at = datetime(
        2026,
        9,
        19,
        16,
        5,
        tzinfo=timezone.utc,
    )

    delivered = _build_event(
        observed_at=delivered_at,
    )

    cooldown.mark_delivered(
        delivered,
    )

    older = _build_event(
        observed_at=delivered_at - timedelta(
            seconds=60,
        ),
    )

    assert not cooldown.can_deliver(
        older,
    )


def test_clear_removes_cooldown_state():
    cooldown = MarketEventPushCooldown(
        cooldown_seconds=300,
    )

    event = _build_event(
        observed_at=datetime(
            2026,
            9,
            19,
            16,
            0,
            tzinfo=timezone.utc,
        ),
    )

    cooldown.mark_delivered(
        event,
    )

    cooldown.clear()

    repeated = _build_event(
        observed_at=event.observed_at + timedelta(
            seconds=60,
        ),
    )

    assert cooldown.can_deliver(
        repeated,
    )