import unittest

from app.push.push_device_registration_service import (
    PushDeviceRegistrationService,
)
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


class _MemoryPushDeviceStore(
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
        return (
            self.devices.pop(
                installation_id,
                None,
            )
            is not None
        )

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
        scope_key="test-scope",
    )


class PushDeviceFidRegistrationTest(
    unittest.TestCase
):
    def test_service_persists_fid(
        self,
    ):
        store = (
            _MemoryPushDeviceStore()
        )

        service = (
            PushDeviceRegistrationService(
                store=store,
            )
        )

        device = service.register(
            installation_id="device-a",
            fcm_token="token-a",
            firebase_installation_id=(
                "firebase-device-a"
            ),
        )

        self.assertEqual(
            device.firebase_installation_id,
            "firebase-device-a",
        )

        restored = store.load_device(
            "device-a",
        )

        self.assertEqual(
            restored.firebase_installation_id,
            "firebase-device-a",
        )

    def test_api_accepts_fid_without_exposing_it(
        self,
    ):
        store = (
            _MemoryPushDeviceStore()
        )

        request = (
            PushDeviceRegistrationRequest(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-device-a"
                ),
                platform="android",
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

        self.assertFalse(
            hasattr(
                response,
                "firebase_installation_id",
            )
        )

        stored = store.load_device(
            "device-a",
        )

        self.assertEqual(
            stored.firebase_installation_id,
            "firebase-device-a",
        )

    def test_api_remains_compatible_without_fid(
        self,
    ):
        store = (
            _MemoryPushDeviceStore()
        )

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

        stored = store.load_device(
            "device-a",
        )

        self.assertIsNone(
            stored.firebase_installation_id,
        )


if __name__ == "__main__":
    unittest.main()