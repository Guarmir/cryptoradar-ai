import unittest

from app.push.push_device import PushDevice
from app.push.push_device_registration_service import (
    PushDeviceRegistrationService,
)
from app.push.push_device_store import (
    PushDeviceStore,
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


class PushRegistrationConfigTest(
    unittest.TestCase
):
    def test_registration_is_disabled_by_default(
        self,
    ):
        config = (
            PushRegistrationConfig
            .from_environment(
                {},
            )
        )

        self.assertFalse(
            config.enabled,
        )

        self.assertIsNone(
            config.database_url,
        )

        self.assertIsNone(
            config.scope_key,
        )

    def test_enabled_configuration_reads_environment(
        self,
    ):
        config = (
            PushRegistrationConfig
            .from_environment(
                {
                    (
                        "CRYPTORADAR_"
                        "PUSH_REGISTRATION_ENABLED"
                    ): "true",
                    (
                        "CRYPTORADAR_"
                        "DATABASE_URL"
                    ): "postgresql://test",
                    (
                        "CRYPTORADAR_"
                        "PUSH_SCOPE"
                    ): "push-test",
                },
            )
        )

        self.assertTrue(
            config.enabled,
        )

        self.assertEqual(
            config.database_url,
            "postgresql://test",
        )

        self.assertEqual(
            config.scope_key,
            "push-test",
        )

    def test_enabled_configuration_requires_database_url(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushRegistrationConfig(
                enabled=True,
                scope_key="push-test",
            )

    def test_enabled_configuration_requires_scope(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushRegistrationConfig(
                enabled=True,
                database_url=(
                    "postgresql://test"
                ),
            )


class PushDeviceRegistrationServiceTest(
    unittest.TestCase
):
    def test_registers_device(
        self,
    ):
        store = _FakePushDeviceStore()

        service = (
            PushDeviceRegistrationService(
                store=store,
            )
        )

        device = service.register(
            installation_id="device-a",
            fcm_token="token-a",
        )

        self.assertEqual(
            device.installation_id,
            "device-a",
        )

        self.assertEqual(
            device.fcm_token,
            "token-a",
        )

        self.assertEqual(
            device.platform,
            "android",
        )

        self.assertTrue(
            device.enabled,
        )

        restored = store.load_device(
            "device-a",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.fcm_token,
            "token-a",
        )

    def test_registration_normalizes_values(
        self,
    ):
        store = _FakePushDeviceStore()

        service = (
            PushDeviceRegistrationService(
                store=store,
            )
        )

        device = service.register(
            installation_id="  device-a  ",
            fcm_token="  token-a  ",
            platform="  ANDROID  ",
        )

        self.assertEqual(
            device.installation_id,
            "device-a",
        )

        self.assertEqual(
            device.fcm_token,
            "token-a",
        )

        self.assertEqual(
            device.platform,
            "android",
        )

    def test_registering_same_installation_updates_device(
        self,
    ):
        store = _FakePushDeviceStore()

        service = (
            PushDeviceRegistrationService(
                store=store,
            )
        )

        service.register(
            installation_id="device-a",
            fcm_token="token-old",
        )

        service.register(
            installation_id="device-a",
            fcm_token="token-new",
        )

        devices = store.load_all()

        self.assertEqual(
            len(devices),
            1,
        )

        self.assertEqual(
            devices[0].fcm_token,
            "token-new",
        )

    def test_registration_rejects_empty_token(
        self,
    ):
        store = _FakePushDeviceStore()

        service = (
            PushDeviceRegistrationService(
                store=store,
            )
        )

        with self.assertRaises(
            ValueError,
        ):
            service.register(
                installation_id="device-a",
                fcm_token=" ",
            )


if __name__ == "__main__":
    unittest.main()