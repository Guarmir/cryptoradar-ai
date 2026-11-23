"""Testes do caminho de renovacao autenticada de token FCM."""

import unittest

from app.push.push_device import PushDevice
from app.push.push_device_registration_service import (
    ProtectedInstallationRegistrationError,
    PushDeviceRegistrationService,
)


class FakeDeviceStore:
    def __init__(self, devices=()):
        self.devices = {device.installation_id: device for device in devices}
        self.save_count = 0

    def load_device(self, installation_id):
        return self.devices.get(installation_id)

    def save_device(self, device):
        self.devices[device.installation_id] = device
        self.save_count += 1


class FakeOwnerStore:
    def __init__(self, owners=None, failure=None):
        self.owners = owners or {}
        self.failure = failure

    def load_owner_uid(self, installation_id):
        if self.failure:
            raise self.failure
        return self.owners.get(installation_id)


class AuthenticatedRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.store = FakeDeviceStore([PushDevice(
            installation_id="device-a", fcm_token="old-token"
        )])

    def service(self, owner_store):
        return PushDeviceRegistrationService(
            store=self.store, owner_store=owner_store
        )

    def test_owner_can_renew_token(self):
        service = self.service(FakeOwnerStore({"device-a": "uid-a"}))
        device = service.register_authenticated(
            installation_id="device-a", authenticated_uid="uid-a",
            fcm_token="new-token", firebase_installation_id="fid-new"
        )
        self.assertEqual(device.fcm_token, "new-token")
        self.assertEqual(device.firebase_installation_id, "fid-new")
        self.assertEqual(self.store.load_device("device-a"), device)
        self.assertEqual(self.store.save_count, 1)

    def test_different_uid_is_denied_without_modification(self):
        service = self.service(FakeOwnerStore({"device-a": "uid-a"}))
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register_authenticated(
                installation_id="device-a", authenticated_uid="uid-b",
                fcm_token="attacker-token"
            )
        self.assertEqual(self.store.load_device("device-a").fcm_token, "old-token")
        self.assertEqual(self.store.save_count, 0)

    def test_unowned_legacy_installation_cannot_be_claimed(self):
        service = self.service(FakeOwnerStore())
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register_authenticated(
                installation_id="device-a", authenticated_uid="uid-a",
                fcm_token="new-token"
            )
        self.assertEqual(self.store.save_count, 0)

    def test_no_owner_reader_fails_closed(self):
        service = self.service(None)
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register_authenticated(
                installation_id="device-a", authenticated_uid="uid-a",
                fcm_token="new-token"
            )
        self.assertEqual(self.store.save_count, 0)

    def test_blank_uid_fails_closed(self):
        service = self.service(FakeOwnerStore({"device-a": "uid-a"}))
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register_authenticated(
                installation_id="device-a", authenticated_uid="  ",
                fcm_token="new-token"
            )
        self.assertEqual(self.store.save_count, 0)

    def test_missing_device_fails_closed(self):
        service = self.service(FakeOwnerStore({"missing": "uid-a"}))
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register_authenticated(
                installation_id="missing", authenticated_uid="uid-a",
                fcm_token="new-token"
            )
        self.assertEqual(self.store.save_count, 0)

    def test_database_lookup_error_does_not_allow_renewal(self):
        service = self.service(FakeOwnerStore(failure=RuntimeError("db error")))
        with self.assertRaises(RuntimeError):
            service.register_authenticated(
                installation_id="device-a", authenticated_uid="uid-a",
                fcm_token="new-token"
            )
        self.assertEqual(self.store.save_count, 0)

    def test_preserves_disabled_device_state(self):
        self.store.devices["device-a"] = PushDevice(
            installation_id="device-a", fcm_token="old-token", enabled=False
        )
        service = self.service(FakeOwnerStore({"device-a": "uid-a"}))
        device = service.register_authenticated(
            installation_id="device-a", authenticated_uid="uid-a",
            fcm_token="new-token"
        )
        self.assertFalse(device.enabled)
        self.assertEqual(device.fcm_token, "new-token")

    def test_public_legacy_register_still_works_for_unowned(self):
        service = self.service(FakeOwnerStore())
        device = service.register(installation_id="device-a", fcm_token="new")
        self.assertEqual(device.fcm_token, "new")

    def test_public_legacy_register_still_denied_for_owned(self):
        service = self.service(FakeOwnerStore({"device-a": "uid-a"}))
        with self.assertRaises(ProtectedInstallationRegistrationError):
            service.register(installation_id="device-a", fcm_token="new")
        self.assertEqual(self.store.save_count, 0)


if __name__ == "__main__":
    unittest.main()
