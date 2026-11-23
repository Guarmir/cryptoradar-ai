from typing import Optional

from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
    PushDeliveryOutcome,
    PushNotificationMessage,
)
from app.push.push_device_store import PushDeviceStore
from app.push.push_sender import PushSender
from app.push.postgresql_push_notification_preferences_store import (
    PostgreSQLPushNotificationPreferencesStore,
)


class PushDeliveryService:
    def __init__(
        self,
        *,
        device_store: PushDeviceStore,
        push_sender: PushSender,
        notification_preferences_store: Optional[
            PostgreSQLPushNotificationPreferencesStore
        ] = None,
    ):
        self._device_store = device_store
        self._push_sender = push_sender
        self._notification_preferences_store = notification_preferences_store

    def deliver(
        self,
        message: PushNotificationMessage,
    ) -> PushDeliveryBatchResult:
        devices = self._device_store.load_enabled()
        outcomes = []

        for device in devices:
            if not device.can_receive_push:
                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=device.installation_id,
                        delivered=False,
                        error_code="device_not_receivable",
                    )
                )
                continue

            # Only the conservative scanner's three known states are scoped
            # to these preferences. Other push producers remain unchanged.
            if (
                self._notification_preferences_store is not None
                and message.data.get("type") == "early_movement"
                and message.data.get("state")
                in ("observation", "early_movement", "confirmed_movement")
            ):
                try:
                    preferences = self._notification_preferences_store.load(
                        device.installation_id
                    )
                except Exception:
                    # A database failure must not override an opt-out.
                    outcomes.append(
                        PushDeliveryOutcome(
                            installation_id=device.installation_id,
                            delivered=False,
                            error_code="notification_preferences_unavailable",
                        )
                    )
                    continue
                if not preferences.allows_state(message.data["state"]):
                    outcomes.append(
                        PushDeliveryOutcome(
                            installation_id=device.installation_id,
                            delivered=False,
                            error_code="notification_preference_disabled",
                        )
                    )
                    continue

            try:
                send_result = self._push_sender.send(
                    device=device,
                    message=message,
                )
                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=device.installation_id,
                        delivered=send_result.delivered,
                        invalid_token=send_result.invalid_token,
                        error_code=send_result.error_code,
                    )
                )
            except Exception:
                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=device.installation_id,
                        delivered=False,
                        error_code="sender_exception",
                    )
                )

        return PushDeliveryBatchResult(outcomes=tuple(outcomes))
