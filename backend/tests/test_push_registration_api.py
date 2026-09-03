import unittest

from fastapi import HTTPException

from app.push.push_device_store import (
    PushDeviceStore,
)
from app.push.push_registration_api import (
    PushDeviceRegistrationRequest,
    register_push_device,
)
from app.push.push_registration_config import (
    PushRegistrationConfig,
)


class _FakePushDeviceStore(
    PushDeviceStore
):
    def __init__(
        self,
    ):
        self.devices = {}

    def load_device(
        self,
        installation_id,
    ):
        return self.devices.get(
            installation_id,
        )

    def load_all(
        self,
    ):
        return tuple(
            self.devices.values()
        )

    def load_enabled(
        self,
    ):
        return tuple(
            device
            for device
            in self.devices.values()
            if device.enabled
        )

    def save_device(
        self,
        device,
    ):
        self.devices[
            device.installation_id
        ] = device

    def delete_device(
        self,
        installation_id,
    ):
        if installation_id not in self.devices:
            return False

        del self.devices[
            installation_id
        ]

        return True

    def clear(
        self,
    ):
        self.devices.clear()


def _enabled_config():
    return PushRegistrationConfig(
        enabled=True,
        database_url=(
            "postgresql://test"
        ),
        scope_key="push-test",
    )


class PushRegistrationApiTest(
    unittest.TestCase
):
    def test_disabled_registration_returns_503(
        self,
    ):
        request = (
            PushDeviceRegistrationRequest(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        with self.assertRaises(
            HTTPException,
        ) as context:
            register_push_device(
                request,
                config=(
                    PushRegistrationConfig(
                        enabled=False,
                    )
                ),
                store=_FakePushDeviceStore(),
            )

        self.assertEqual(
            context.exception.status_code,
            503,
        )

    def test_registers_device(
        self,
    ):
        store = _FakePushDeviceStore()

        request = (
            PushDeviceRegistrationRequest(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        response = register_push_device(
            request,
            config=_enabled_config(),
            store=store,
        )

        self.assertEqual(
            response.status,
            "registered",
        )

        self.assertEqual(
            response.installation_id,
            "device-a",
        )

        self.assertEqual(
            response.platform,
            "android",
        )

        self.assertTrue(
            response.enabled,
        )

        stored = store.load_device(
            "device-a",
        )

        self.assertIsNotNone(
            stored,
        )

        self.assertEqual(
            stored.fcm_token,
            "token-a",
        )

    def test_response_does_not_expose_fcm_token(
        self,
    ):
        response = register_push_device(
            PushDeviceRegistrationRequest(
                installation_id="device-a",
                fcm_token="token-secret",
            ),
            config=_enabled_config(),
            store=_FakePushDeviceStore(),
        )

        self.assertFalse(
            hasattr(
                response,
                "fcm_token",
            )
        )

    def test_blank_token_returns_422(
        self,
    ):
        request = (
            PushDeviceRegistrationRequest(
                installation_id="device-a",
                fcm_token="   ",
            )
        )

        with self.assertRaises(
            HTTPException,
        ) as context:
            register_push_device(
                request,
                config=_enabled_config(),
                store=_FakePushDeviceStore(),
            )

        self.assertEqual(
            context.exception.status_code,
            422,
        )


if __name__ == "__main__":
    unittest.main()