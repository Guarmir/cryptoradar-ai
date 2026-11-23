"""Regressao: a rota legada nao altera instalacoes ja vinculadas."""

import unittest

from fastapi import HTTPException

from app.push.push_device_registration_service import (
    ProtectedInstallationRegistrationError,
    PushDeviceRegistrationService,
)
from app.push.push_registration_api import (
    PushDeviceRegistrationRequest,
    register_push_device,
)
from app.push.push_registration_config import PushRegistrationConfig


class FakeDeviceStore:
    def __init__(self):
        self.devices = {}
        self.saves = 0

    def save_device(self, device):
        self.devices[device.installation_id] = device
        self.saves += 1


class FakeOwnerStore:
    def __init__(self, owners=None, error=None):
        self.owners = owners or {}
        self.error = error

    def load_owner_uid(self, installation_id):
        if self.error:
            raise self.error
        return self.owners.get(installation_id)


def config():
    return PushRegistrationConfig(
        enabled=True, database_url="postgresql://test", scope_key="push-test"
    )


class ProtectedRegistrationTests(unittest.TestCase):
    def test_legacy_registers_unowned_installation(self):
        devices = FakeDeviceStore()
        service = PushDeviceRegistrationService(
            store=devices, owner_store=FakeOwnerStore()
        )
        result = service.register(installation_id="new", fcm_token="t1")
        self.assertEqual(result.fcm_token, "t1")
        self.assertEqual(devices.saves, 1)

    def test_legacy_refreshes_unowned_installation(self):
        devices = FakeDeviceStore()
        service = PushDeviceRegistrationService(
            store=devices, owner_store=FakeOwnerStore()
        )
        service.register(installation_id="existing", fcm_token="old")
        service.register(installation_id="existing", fcm_token="new")
        self.assertEqual(devices.devices["existing"].fcm_token, "new")

    def test_protected_installation_cannot_be_overwritten(self):
        devices = FakeDeviceStore()
        original = PushDeviceRegistrationService(store=devices)
        original.register(installation_id="owned", fcm_token="original")
        protected = PushDeviceRegistrationService(
            store=devices, owner_store=FakeOwnerStore({"owned": "uid-A"})
        )
        with self.assertRaises(ProtectedInstallationRegistrationError):
            protected.register(installation_id="owned", fcm_token="attacker")
        self.assertEqual(devices.devices["owned"].fcm_token, "original")
        self.assertEqual(devices.saves, 1)

    def test_protection_normalizes_installation_id(self):
        devices = FakeDeviceStore()
        service = PushDeviceRegistrationService(
            store=devices, owner_store=FakeOwnerStore({"owned": "uid-A"})
        )
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register(installation_id="  owned ", fcm_token="attacker")
        self.assertEqual(devices.saves, 0)

    def test_owner_lookup_failure_fails_closed(self):
        devices = FakeDeviceStore()
        service = PushDeviceRegistrationService(
            store=devices,
            owner_store=FakeOwnerStore(error=RuntimeError("DB unavailable")),
        )
        with self.assertRaises(RuntimeError):
            service.register(installation_id="x", fcm_token="token")
        self.assertEqual(devices.saves, 0)

    def test_http_route_returns_403_for_owned_installation(self):
        devices = FakeDeviceStore()
        with self.assertRaises(HTTPException) as context:
            register_push_device(
                PushDeviceRegistrationRequest(
                    installation_id="owned", fcm_token="attacker"
                ),
                config=config(),
                store=devices,
                owner_store=FakeOwnerStore({"owned": "uid-A"}),
            )
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(devices.saves, 0)

    def test_http_route_allows_unowned_installation(self):
        devices = FakeDeviceStore()
        response = register_push_device(
            PushDeviceRegistrationRequest(installation_id="new", fcm_token="ok"),
            config=config(),
            store=devices,
            owner_store=FakeOwnerStore(),
        )
        self.assertEqual(response.status, "registered")
        self.assertEqual(devices.saves, 1)


if __name__ == "__main__":
    unittest.main()
