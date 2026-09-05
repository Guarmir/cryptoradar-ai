import unittest

from app.push.push_device import PushDevice
from app.push.push_device_store import (
    PushDeviceStore,
)


class PushDeviceTest(
    unittest.TestCase
):
    def test_creates_android_device_by_default(
        self,
    ):
        device = PushDevice(
            installation_id="installation-a",
            fcm_token="token-a",
        )

        self.assertEqual(
            device.installation_id,
            "installation-a",
        )

        self.assertEqual(
            device.fcm_token,
            "token-a",
        )

        self.assertIsNone(
            device.firebase_installation_id,
        )

        self.assertEqual(
            device.platform,
            "android",
        )

        self.assertTrue(
            device.enabled,
        )

        self.assertTrue(
            device.can_receive_push,
        )

    def test_normalizes_values(
        self,
    ):
        device = PushDevice(
            installation_id="  installation-a  ",
            fcm_token="  token-a  ",
            platform="  ANDROID  ",
        )

        self.assertEqual(
            device.installation_id,
            "installation-a",
        )

        self.assertEqual(
            device.fcm_token,
            "token-a",
        )

        self.assertEqual(
            device.platform,
            "android",
        )

    def test_normalizes_firebase_installation_id(
        self,
    ):
        device = PushDevice(
            installation_id="installation-a",
            fcm_token="token-a",
            firebase_installation_id=(
                "  firebase-installation-a  "
            ),
        )

        self.assertEqual(
            device.firebase_installation_id,
            "firebase-installation-a",
        )

    def test_empty_firebase_installation_id_becomes_none(
        self,
    ):
        device = PushDevice(
            installation_id="installation-a",
            fcm_token="token-a",
            firebase_installation_id="   ",
        )

        self.assertIsNone(
            device.firebase_installation_id,
        )

    def test_disabled_device_cannot_receive_push(
        self,
    ):
        device = PushDevice(
            installation_id="installation-a",
            fcm_token="token-a",
            enabled=False,
        )

        self.assertFalse(
            device.can_receive_push,
        )

    def test_rejects_empty_installation_id(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushDevice(
                installation_id=" ",
                fcm_token="token-a",
            )

    def test_rejects_empty_fcm_token(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushDevice(
                installation_id="installation-a",
                fcm_token=" ",
            )

    def test_rejects_empty_platform(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PushDevice(
                installation_id="installation-a",
                fcm_token="token-a",
                platform=" ",
            )

    def test_store_is_abstract(
        self,
    ):
        with self.assertRaises(
            TypeError,
        ):
            PushDeviceStore()


if __name__ == "__main__":
    unittest.main()