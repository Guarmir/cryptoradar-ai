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
        # Evaluate all aliases before sending, so an opt-out cannot be bypassed
        # by another enabled registration of the same FCM destination.
        preference_errors = {}
        if (
            self._notification_preferences_store is not None
            and message.data.get("type") == "early_movement"
            and message.data.get("state")
            in ("observation", "early_movement", "confirmed_movement")
        ):
            for device in devices:
                if not device.can_receive_push:
                    continue
                try:
                    preferences = self._notification_preferences_store.load(
                        device.installation_id
                    )
                    if not preferences.allows_state(message.data["state"]):
                        preference_errors[device.fcm_token] = "notification_preference_disabled"
                except Exception:
                    preference_errors[device.fcm_token] = "notification_preferences_unavailable"

        attempted = set()
        for device in devices:
            error = None
            if not device.can_receive_push:
                error = "device_not_receivable"
            elif device.fcm_token in preference_errors:
                error = preference_errors[device.fcm_token]
            elif device.fcm_token in attempted:
                error = "duplicate_destination"
            if error is not None:
                outcomes.append(PushDeliveryOutcome(
                    installation_id=device.installation_id,
                    delivered=False, error_code=error,
                ))
                continue
            # Even a failed/ambiguous send must not trigger a second alias send.
            attempted.add(device.fcm_token)

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
