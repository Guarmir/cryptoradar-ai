import unittest

from app.push.push_delivery_models import (
    PushNotificationMessage,
    PushSendResult,
)
from app.push.push_delivery_service import (
    PushDeliveryService,
)
from app.push.push_device import (
    PushDevice,
)
from app.push.push_device_store import (
    PushDeviceStore,
)
from app.push.push_sender import (
    PushSender,
)


class FakePushDeviceStore(
    PushDeviceStore
):
    def __init__(
        self,
        devices=(),
    ):
        self.devices = list(
            devices
        )

    def load_device(
        self,
        installation_id,
    ):
        for device in self.devices:
            if (
                device.installation_id
                == installation_id
            ):
                return device

        return None

    def load_all(
        self,
    ):
        return tuple(
            self.devices
        )

    def load_enabled(
        self,
    ):
        return tuple(
            device
            for device in self.devices
            if device.enabled
        )

    def save_device(
        self,
        device,
    ):
        self.devices.append(
            device
        )

    def delete_device(
        self,
        installation_id,
    ):
        return False

    def clear(
        self,
    ):
        self.devices.clear()


class FakePushSender(
    PushSender
):
    def __init__(
        self,
    ):
        self.tokens = []
        self.results = {}
        self.exceptions = set()

    def send(
        self,
        *,
        fcm_token,
        message,
    ):
        self.tokens.append(
            fcm_token
        )

        if fcm_token in self.exceptions:
            raise RuntimeError(
                "Falha simulada."
            )

        return self.results.get(
            fcm_token,
            PushSendResult(
                delivered=True,
            ),
        )


class PushDeliveryFoundationTest(
    unittest.TestCase
):
    def test_message_normalizes_content(
        self,
    ):
        message = PushNotificationMessage(
            title="  CryptoRadar  ",
            body="  Oportunidade detectada  ",
            data={
                " symbol ": "UNI",
            },
        )

        self.assertEqual(
            message.title,
            "CryptoRadar",
        )

        self.assertEqual(
            message.body,
            "Oportunidade detectada",
        )

        self.assertEqual(
            message.data,
            {
                "symbol": "UNI",
            },
        )

    def test_message_rejects_empty_title(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushNotificationMessage(
                title="   ",
                body="Mensagem",
            )

    def test_service_sends_only_enabled_devices(
        self,
    ):
        store = FakePushDeviceStore(
            devices=(
                PushDevice(
                    installation_id=(
                        "device-a"
                    ),
                    fcm_token="token-a",
                    enabled=True,
                ),
                PushDevice(
                    installation_id=(
                        "device-b"
                    ),
                    fcm_token="token-b",
                    enabled=False,
                ),
            )
        )

        sender = FakePushSender()

        service = PushDeliveryService(
            device_store=store,
            push_sender=sender,
        )

        result = service.deliver(
            PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            )
        )

        self.assertEqual(
            sender.tokens,
            [
                "token-a",
            ],
        )

        self.assertEqual(
            result.total,
            1,
        )

        self.assertEqual(
            result.delivered,
            1,
        )

    def test_batch_counts_failures(
        self,
    ):
        store = FakePushDeviceStore(
            devices=(
                PushDevice(
                    installation_id=(
                        "device-a"
                    ),
                    fcm_token="token-a",
                ),
                PushDevice(
                    installation_id=(
                        "device-b"
                    ),
                    fcm_token="token-b",
                ),
            )
        )

        sender = FakePushSender()

        sender.results[
            "token-b"
        ] = PushSendResult(
            delivered=False,
            error_code="temporary_error",
        )

        service = PushDeliveryService(
            device_store=store,
            push_sender=sender,
        )

        result = service.deliver(
            PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            )
        )

        self.assertEqual(
            result.total,
            2,
        )

        self.assertEqual(
            result.delivered,
            1,
        )

        self.assertEqual(
            result.failed,
            1,
        )

    def test_invalid_token_is_reported_without_token(
        self,
    ):
        store = FakePushDeviceStore(
            devices=(
                PushDevice(
                    installation_id=(
                        "device-a"
                    ),
                    fcm_token=(
                        "secret-token"
                    ),
                ),
            )
        )

        sender = FakePushSender()

        sender.results[
            "secret-token"
        ] = PushSendResult(
            delivered=False,
            invalid_token=True,
            error_code="invalid_token",
        )

        service = PushDeliveryService(
            device_store=store,
            push_sender=sender,
        )

        result = service.deliver(
            PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            )
        )

        outcome = result.outcomes[0]

        self.assertTrue(
            outcome.invalid_token
        )

        self.assertEqual(
            outcome.installation_id,
            "device-a",
        )

        self.assertNotIn(
            "secret-token",
            repr(
                outcome
            ),
        )

    def test_sender_exception_does_not_stop_batch(
        self,
    ):
        store = FakePushDeviceStore(
            devices=(
                PushDevice(
                    installation_id=(
                        "device-a"
                    ),
                    fcm_token="token-a",
                ),
                PushDevice(
                    installation_id=(
                        "device-b"
                    ),
                    fcm_token="token-b",
                ),
            )
        )

        sender = FakePushSender()

        sender.exceptions.add(
            "token-a"
        )

        service = PushDeliveryService(
            device_store=store,
            push_sender=sender,
        )

        result = service.deliver(
            PushNotificationMessage(
                title="CryptoRadar",
                body="Teste",
            )
        )

        self.assertEqual(
            result.total,
            2,
        )

        self.assertEqual(
            result.delivered,
            1,
        )

        self.assertEqual(
            result.failed,
            1,
        )

        self.assertEqual(
            sender.tokens,
            [
                "token-a",
                "token-b",
            ],
        )


if __name__ == "__main__":
    unittest.main()