from dataclasses import dataclass

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_push_message_builder import (
    EarlyMovementScannerPushMessageBuilder,
)
from app.early_movement.scanner.scanner_push_service import (
    EarlyMovementScannerPushService,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
    PushDeliveryOutcome,
)


@dataclass(frozen=True)
class FakeRankedResult:
    rank: int
    relevance_score: float
    coin_id: str
    symbol: str
    name: str
    state: EarlyMovementState


class FakeCooldown:
    def __init__(
        self,
        *,
        can_deliver: bool = True,
    ) -> None:
        self.allowed = can_deliver
        self.marked = []

    def can_deliver(
        self,
        result,
    ) -> bool:
        return self.allowed

    def mark_delivered(
        self,
        result,
    ) -> None:
        self.marked.append(
            result
        )


class FakeDeliveryService:
    def __init__(
        self,
        *,
        delivered: bool = True,
    ) -> None:
        self.messages = []
        self.delivered = delivered

    def deliver(
        self,
        message,
    ) -> PushDeliveryBatchResult:
        self.messages.append(
            message
        )

        return PushDeliveryBatchResult(
            outcomes=(
                PushDeliveryOutcome(
                    installation_id="test-device",
                    delivered=self.delivered,
                ),
            ),
        )


def make_signal() -> FakeRankedResult:
    return FakeRankedResult(
        rank=1,
        relevance_score=87.5,
        coin_id="bitcoin",
        symbol="btc",
        name="Bitcoin",
        state=EarlyMovementState.EARLY_MOVEMENT,
    )


def make_service(
    *,
    cooldown,
    delivery_service,
) -> EarlyMovementScannerPushService:
    return EarlyMovementScannerPushService(
        cooldown=cooldown,
        message_builder=(
            EarlyMovementScannerPushMessageBuilder()
        ),
        delivery_service=delivery_service,
    )


def test_push_message_builder_builds_scanner_message() -> None:
    builder = (
        EarlyMovementScannerPushMessageBuilder()
    )

    message = builder.build(
        make_signal()
    )

    assert "BTC" in message.title
    assert "Bitcoin" in message.body

    assert (
        message.data["type"]
        == "early_movement"
    )

    assert (
        message.data["coin_id"]
        == "bitcoin"
    )

    assert (
        message.data["rank"]
        == "1"
    )

    assert (
        message.data["relevance_score"]
        == "87.5"
    )


def test_push_service_does_not_deliver_without_alert() -> None:
    cooldown = FakeCooldown()

    delivery_service = (
        FakeDeliveryService()
    )

    service = make_service(
        cooldown=cooldown,
        delivery_service=delivery_service,
    )

    decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )
    )

    results = service.deliver(
        decision
    )

    assert results == ()
    assert delivery_service.messages == []
    assert cooldown.marked == []


def test_push_service_delivers_and_marks_cooldown() -> None:
    cooldown = FakeCooldown()

    delivery_service = (
        FakeDeliveryService(
            delivered=True,
        )
    )

    service = make_service(
        cooldown=cooldown,
        delivery_service=delivery_service,
    )

    signal = make_signal()

    decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(signal,),
        )
    )

    results = service.deliver(
        decision
    )

    assert len(results) == 1
    assert len(delivery_service.messages) == 1
    assert cooldown.marked == [signal]


def test_push_service_respects_cooldown() -> None:
    cooldown = FakeCooldown(
        can_deliver=False,
    )

    delivery_service = (
        FakeDeliveryService()
    )

    service = make_service(
        cooldown=cooldown,
        delivery_service=delivery_service,
    )

    signal = make_signal()

    decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(signal,),
        )
    )

    results = service.deliver(
        decision
    )

    assert results == ()
    assert delivery_service.messages == []
    assert cooldown.marked == []


def test_push_service_does_not_mark_failed_delivery() -> None:
    cooldown = FakeCooldown()

    delivery_service = (
        FakeDeliveryService(
            delivered=False,
        )
    )

    service = make_service(
        cooldown=cooldown,
        delivery_service=delivery_service,
    )

    signal = make_signal()

    decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(signal,),
        )
    )

    results = service.deliver(
        decision
    )

    assert len(results) == 1
    assert len(delivery_service.messages) == 1
    assert cooldown.marked == []