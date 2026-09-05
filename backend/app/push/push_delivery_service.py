from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
    PushDeliveryOutcome,
    PushNotificationMessage,
)
from app.push.push_device_store import (
    PushDeviceStore,
)
from app.push.push_sender import (
    PushSender,
)


class PushDeliveryService:
    def __init__(
        self,
        *,
        device_store: PushDeviceStore,
        push_sender: PushSender,
    ):
        self._device_store = device_store
        self._push_sender = push_sender

    def deliver(
        self,
        message: PushNotificationMessage,
    ) -> PushDeliveryBatchResult:
        devices = (
            self._device_store.load_enabled()
        )

        outcomes = []

        for device in devices:
            if not device.can_receive_push:
                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=(
                            device.installation_id
                        ),
                        delivered=False,
                        error_code=(
                            "device_not_receivable"
                        ),
                    )
                )

                continue

            try:
                send_result = (
                    self._push_sender.send(
                        fcm_token=(
                            device.fcm_token
                        ),
                        message=message,
                    )
                )

                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=(
                            device.installation_id
                        ),
                        delivered=(
                            send_result.delivered
                        ),
                        invalid_token=(
                            send_result.invalid_token
                        ),
                        error_code=(
                            send_result.error_code
                        ),
                    )
                )

            except Exception:
                outcomes.append(
                    PushDeliveryOutcome(
                        installation_id=(
                            device.installation_id
                        ),
                        delivered=False,
                        error_code=(
                            "sender_exception"
                        ),
                    )
                )

        return PushDeliveryBatchResult(
            outcomes=tuple(
                outcomes,
            ),
        )