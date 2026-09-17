from threading import Lock
from typing import Any, Callable, Optional

from app.push.push_delivery_models import (
    PushNotificationMessage,
    PushSendResult,
)
from app.push.push_device import (
    PushDevice,
)
from app.push.push_sender import (
    PushSender,
)


class FirebaseAdminPushSender(
    PushSender
):
    def __init__(
        self,
        *,
        messaging_module: Optional[
            Any
        ] = None,
        app_initializer: Optional[
            Callable[[], None]
        ] = None,
    ):
        self._messaging_module = (
            messaging_module
        )

        self._app_initializer = (
            app_initializer
        )

        self._initialized = False
        self._initialization_lock = Lock()

    def send(
        self,
        *,
        device: PushDevice,
        message: PushNotificationMessage,
    ) -> PushSendResult:
        try:
            self._ensure_initialized()

            messaging = (
                self._resolve_messaging()
            )

        except Exception:
            return PushSendResult(
                delivered=False,
                error_code=(
                    "firebase_initialize_error"
                ),
            )

        if device.firebase_installation_id:
            fid_result = self._send_to_destination(
                messaging=messaging,
                destination_type="fid",
                destination=(
                    device.firebase_installation_id
                ),
                message=message,
            )

            if fid_result.delivered:
                return fid_result

            if not fid_result.invalid_token:
                return fid_result

        if device.fcm_token:
            return self._send_to_destination(
                messaging=messaging,
                destination_type="token",
                destination=device.fcm_token,
                message=message,
            )

        return PushSendResult(
            delivered=False,
            invalid_token=True,
            error_code="missing_destination",
        )

    def _send_to_destination(
        self,
        *,
        messaging,
        destination_type: str,
        destination: str,
        message: PushNotificationMessage,
    ) -> PushSendResult:
        try:
            notification = (
                messaging.Notification(
                    title=message.title,
                    body=message.body,
                )
            )

            message_arguments = {
                "notification":
                    notification,
                "data":
                    dict(
                        message.data,
                    ),
                destination_type:
                    destination,
            }

            firebase_message = (
                messaging.Message(
                    **message_arguments
                )
            )

            messaging.send(
                firebase_message
            )

            return PushSendResult(
                delivered=True,
            )

        except Exception as error:
            if (
                self._is_invalid_destination_error(
                    error,
                )
            ):
                return PushSendResult(
                    delivered=False,
                    invalid_token=True,
                    error_code=(
                        "invalid_destination"
                    ),
                )

            return PushSendResult(
                delivered=False,
                error_code=(
                    "firebase_send_error"
                ),
            )

    def _ensure_initialized(
        self,
    ) -> None:
        if self._initialized:
            return

        with self._initialization_lock:
            if self._initialized:
                return

            if (
                self._app_initializer
                is not None
            ):
                self._app_initializer()

            else:
                import firebase_admin

                try:
                    firebase_admin.get_app()

                except ValueError:
                    firebase_admin.initialize_app()

            self._initialized = True

    def _resolve_messaging(
        self,
    ):
        if (
            self._messaging_module
            is not None
        ):
            return self._messaging_module

        from firebase_admin import messaging

        return messaging

    @staticmethod
    def _is_invalid_destination_error(
        error: Exception,
    ) -> bool:
        return (
            error.__class__.__name__
            == "UnregisteredError"
        )