from typing import Optional

from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_push_cooldown import (
    EarlyMovementScannerPushCooldown,
)
from app.early_movement.scanner.scanner_push_evolution_guard import (
    EarlyMovementScannerPushEvolutionGuard,
)
from app.early_movement.scanner.scanner_push_message_builder import (
    EarlyMovementScannerPushMessageBuilder,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
)


class EarlyMovementScannerPushService:
    def __init__(
        self,
        *,
        cooldown: EarlyMovementScannerPushCooldown,
        message_builder: EarlyMovementScannerPushMessageBuilder,
        delivery_service: PushDeliveryService,
        evolution_guard: Optional[
            EarlyMovementScannerPushEvolutionGuard
        ] = None,
    ) -> None:
        self._cooldown = cooldown
        self._message_builder = message_builder
        self._delivery_service = delivery_service
        self._evolution_guard = (
            evolution_guard
            if evolution_guard is not None
            else EarlyMovementScannerPushEvolutionGuard()
        )

    def deliver(
        self,
        decision: EarlyMovementScannerAlertDecision,
    ) -> tuple[
        PushDeliveryBatchResult,
        ...,
    ]:
        if not decision.should_alert:
            return ()

        delivery_results = []

        for result in decision.results:
            if not self._evolution_guard.should_notify(result):
                continue

            if not self._cooldown.can_deliver(result):
                continue

            message = self._message_builder.build(result)
            delivery_result = self._delivery_service.deliver(message)

            delivery_results.append(delivery_result)

            if delivery_result.delivered > 0:
                self._cooldown.mark_delivered(result)
                self._evolution_guard.mark_notified(result)

        return tuple(delivery_results)