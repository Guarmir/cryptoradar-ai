from typing import Optional

from app.monitoring.market_event import MarketEvent
from app.push.market_event_push_cooldown import (
    MarketEventPushCooldown,
)
from app.push.market_event_push_message_builder import (
    MarketEventPushMessageBuilder,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
)


class MarketEventPushService:
    def __init__(
        self,
        *,
        cooldown: MarketEventPushCooldown,
        message_builder: MarketEventPushMessageBuilder,
        delivery_service: PushDeliveryService,
    ):
        self._cooldown = cooldown
        self._message_builder = message_builder
        self._delivery_service = delivery_service

    def deliver(
        self,
        event: MarketEvent,
    ) -> Optional[PushDeliveryBatchResult]:
        if not self._cooldown.can_deliver(
            event,
        ):
            return None

        message = self._message_builder.build(
            event,
        )

        result = self._delivery_service.deliver(
            message,
        )

        if result.delivered > 0:
            self._cooldown.mark_delivered(
                event,
            )

        return result