import unittest

from app.push.firebase_admin_push_sender import (
    FirebaseAdminPushSender,
)
from app.push.push_delivery_models import (
    PushNotificationMessage,
)
from app.push.push_device import (
    PushDevice,
)


class _FakeNotification:
    def __init__(
        self,
        **kwargs,
    ):
        self.kwargs = kwargs


class _FakeMessage:
    def __init__(
        self,
        **kwargs,
    ):
        self.kwargs = kwargs


class UnregisteredError(
    Exception
):
    pass


class _FakeMessaging:
    Notification = _FakeNotification
    Message = _FakeMessage

    def __init__(
        self,
    ):
        self.sent_messages = []
        self.error = None

    def send(
        self,
        message,
    ):
        if self.error is not None:
            raise self.error

        self.sent_messages.append(
            message
        )

        return "message-id"


class FirebaseAdminPushSenderTest(
    unittest.TestCase
):
    def test_prefers_fid_when_available(
        self,
    ):
        messaging = _FakeMessaging()

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=lambda: None,
        )

        result = sender.send(
            device=PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-a"
                ),
            ),
            message=PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            ),
        )

        self.assertTrue(
            result.delivered
        )

        sent = (
            messaging
            .sent_messages[0]
            .kwargs
        )

        self.assertEqual(
            sent["fid"],
            "firebase-a",
        )

        self.assertNotIn(
            "token",
            sent,
        )

    def test_falls_back_to_token_without_fid(
        self,
    ):
        messaging = _FakeMessaging()

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=lambda: None,
        )

        result = sender.send(
            device=PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            ),
            message=PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            ),
        )

        self.assertTrue(
            result.delivered
        )

        sent = (
            messaging
            .sent_messages[0]
            .kwargs
        )

        self.assertEqual(
            sent["token"],
            "token-a",
        )

        self.assertNotIn(
            "fid",
            sent,
        )

    def test_builds_notification_and_data(
        self,
    ):
        messaging = _FakeMessaging()

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=lambda: None,
        )

        sender.send(
            device=PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-a"
                ),
            ),
            message=PushNotificationMessage(
                title="CryptoRadar",
                body="UNI em observação",
                data={
                    "symbol": "UNI",
                    "type": "validation",
                },
            ),
        )

        sent = (
            messaging
            .sent_messages[0]
            .kwargs
        )

        notification = sent[
            "notification"
        ]

        self.assertEqual(
            notification.kwargs[
                "title"
            ],
            "CryptoRadar",
        )

        self.assertEqual(
            notification.kwargs[
                "body"
            ],
            "UNI em observação",
        )

        self.assertEqual(
            sent["data"],
            {
                "symbol": "UNI",
                "type": "validation",
            },
        )

    def test_initializes_firebase_only_once(
        self,
    ):
        messaging = _FakeMessaging()

        initialize_count = 0

        def initialize():
            nonlocal initialize_count
            initialize_count += 1

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=initialize,
        )

        device = PushDevice(
            installation_id="device-a",
            fcm_token="token-a",
            firebase_installation_id=(
                "firebase-a"
            ),
        )

        message = PushNotificationMessage(
            title="CryptoRadar",
            body="Teste",
        )

        sender.send(
            device=device,
            message=message,
        )

        sender.send(
            device=device,
            message=message,
        )

        self.assertEqual(
            initialize_count,
            1,
        )

    def test_unregistered_destination_is_reported(
        self,
    ):
        messaging = _FakeMessaging()

        messaging.error = (
            UnregisteredError()
        )

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=lambda: None,
        )

        result = sender.send(
            device=PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-a"
                ),
            ),
            message=PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            ),
        )

        self.assertFalse(
            result.delivered
        )

        self.assertTrue(
            result.invalid_token
        )

        self.assertEqual(
            result.error_code,
            "invalid_destination",
        )

    def test_generic_error_does_not_expose_destination(
        self,
    ):
        messaging = _FakeMessaging()

        messaging.error = RuntimeError(
            "firebase-a token-a"
        )

        sender = FirebaseAdminPushSender(
            messaging_module=messaging,
            app_initializer=lambda: None,
        )

        result = sender.send(
            device=PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-a"
                ),
            ),
            message=PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            ),
        )

        self.assertFalse(
            result.delivered
        )

        self.assertEqual(
            result.error_code,
            "firebase_send_error",
        )

        self.assertNotIn(
            "firebase-a",
            repr(
                result
            ),
        )

        self.assertNotIn(
            "token-a",
            repr(
                result
            ),
        )


if __name__ == "__main__":
    unittest.main()