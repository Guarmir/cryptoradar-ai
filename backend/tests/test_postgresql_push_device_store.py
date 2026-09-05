import unittest

from app.push.postgresql_push_device_store import (
    PostgreSQLPushDeviceStore,
)
from app.push.push_device import PushDevice


class _FakeDatabase:
    def __init__(self):
        self.rows = {}


class _FakeConnectionFactory:
    def __init__(
        self,
        database,
    ):
        self.database = database
        self.connection_count = 0

    def __call__(
        self,
        database_url,
    ):
        self.connection_count += 1

        return _FakeConnection(
            self.database,
        )


class _FakeConnection:
    def __init__(
        self,
        database,
    ):
        self.database = database
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self):
        return _FakeCursor(
            self.database,
        )

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


class _FakeCursor:
    def __init__(
        self,
        database,
    ):
        self.database = database
        self._rows = []
        self.rowcount = 0
        self.closed = False

    def execute(
        self,
        query,
        params,
    ):
        normalized = " ".join(
            query.split()
        ).lower()

        self._rows = []
        self.rowcount = 0

        if normalized.startswith(
            "insert into"
        ):
            scope_key = params[0]
            installation_id = params[1]
            fcm_token = params[2]
            firebase_installation_id = (
                params[3]
            )
            platform = params[4]
            enabled = params[5]

            self.database.rows[
                (
                    scope_key,
                    installation_id,
                )
            ] = {
                "installation_id":
                    installation_id,
                "fcm_token":
                    fcm_token,
                "firebase_installation_id":
                    firebase_installation_id,
                "platform":
                    platform,
                "enabled":
                    enabled,
            }

            self.rowcount = 1
            return

        if normalized.startswith(
            "select installation_id"
        ):
            scope_key = params[0]

            if (
                "and installation_id = %s"
                in normalized
            ):
                installation_id = params[1]

                value = self.database.rows.get(
                    (
                        scope_key,
                        installation_id,
                    )
                )

                if value is not None:
                    self._rows = [
                        self._row_from_value(
                            value,
                        )
                    ]

                return

            enabled_only = (
                "and enabled = true"
                in normalized
            )

            matching = [
                value
                for (
                    current_scope,
                    _,
                ),
                value
                in self.database.rows.items()
                if current_scope
                == scope_key
                and (
                    not enabled_only
                    or value["enabled"]
                )
            ]

            matching.sort(
                key=lambda value:
                    value[
                        "installation_id"
                    ]
            )

            self._rows = [
                self._row_from_value(
                    value,
                )
                for value in matching
            ]

            return

        if normalized.startswith(
            "delete from"
        ):
            scope_key = params[0]

            if (
                "and installation_id = %s"
                in normalized
            ):
                installation_id = params[1]

                key = (
                    scope_key,
                    installation_id,
                )

                if key in self.database.rows:
                    del self.database.rows[
                        key
                    ]

                    self.rowcount = 1

                return

            keys = [
                key
                for key
                in self.database.rows
                if key[0] == scope_key
            ]

            for key in keys:
                del self.database.rows[
                    key
                ]

            self.rowcount = len(
                keys,
            )

            return

        raise AssertionError(
            f"SQL não reconhecido pelo fake: "
            f"{normalized}"
        )

    def fetchone(self):
        if not self._rows:
            return None

        return self._rows[0]

    def fetchall(self):
        return list(
            self._rows,
        )

    def close(self):
        self.closed = True

    @staticmethod
    def _row_from_value(
        value,
    ):
        return (
            value["installation_id"],
            value["fcm_token"],
            value[
                "firebase_installation_id"
            ],
            value["platform"],
            value["enabled"],
        )


class PostgreSQLPushDeviceStoreTest(
    unittest.TestCase
):
    def test_rejects_empty_database_url(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PostgreSQLPushDeviceStore(
                database_url=" ",
                scope_key="user-a",
            )

    def test_rejects_empty_scope(
        self,
    ):
        with self.assertRaises(
            ValueError,
        ):
            PostgreSQLPushDeviceStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key=" ",
            )

    def test_saves_and_restores_device(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        restored = store.load_device(
            "device-a",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.installation_id,
            "device-a",
        )

        self.assertEqual(
            restored.fcm_token,
            "token-a",
        )

        self.assertIsNone(
            restored.firebase_installation_id,
        )

        self.assertEqual(
            restored.platform,
            "android",
        )

        self.assertTrue(
            restored.enabled,
        )

    def test_saves_and_restores_firebase_installation_id(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-device-a"
                ),
            )
        )

        restored = store.load_device(
            "device-a",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.firebase_installation_id,
            "firebase-device-a",
        )

    def test_updates_token_without_duplicate(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-old",
            )
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-new",
            )
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

    def test_updates_fid_without_duplicate(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-old"
                ),
            )
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                firebase_installation_id=(
                    "firebase-new"
                ),
            )
        )

        devices = store.load_all()

        self.assertEqual(
            len(devices),
            1,
        )

        self.assertEqual(
            devices[
                0
            ].firebase_installation_id,
            "firebase-new",
        )

    def test_scopes_isolate_same_installation(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=factory,
        )

        store_b = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-b",
            connection_factory=factory,
        )

        store_a.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        store_b.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-b",
            )
        )

        self.assertEqual(
            store_a.load_device(
                "device-a",
            ).fcm_token,
            "token-a",
        )

        self.assertEqual(
            store_b.load_device(
                "device-a",
            ).fcm_token,
            "token-b",
        )

        self.assertEqual(
            len(database.rows),
            2,
        )

    def test_load_enabled_filters_disabled_devices(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
                enabled=True,
            )
        )

        store.save_device(
            PushDevice(
                installation_id="device-b",
                fcm_token="token-b",
                enabled=False,
            )
        )

        enabled = store.load_enabled()

        self.assertEqual(
            len(enabled),
            1,
        )

        self.assertEqual(
            enabled[0].installation_id,
            "device-a",
        )

    def test_load_all_returns_only_current_scope(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=factory,
        )

        store_b = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-b",
            connection_factory=factory,
        )

        store_a.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        store_b.save_device(
            PushDevice(
                installation_id="device-b",
                fcm_token="token-b",
            )
        )

        devices = store_a.load_all()

        self.assertEqual(
            len(devices),
            1,
        )

        self.assertEqual(
            devices[0].installation_id,
            "device-a",
        )

    def test_delete_removes_only_requested_device(
        self,
    ):
        database = _FakeDatabase()

        store = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=
                _FakeConnectionFactory(
                    database,
                ),
        )

        store.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        store.save_device(
            PushDevice(
                installation_id="device-b",
                fcm_token="token-b",
            )
        )

        removed = store.delete_device(
            " device-a ",
        )

        self.assertTrue(
            removed,
        )

        self.assertIsNone(
            store.load_device(
                "device-a",
            )
        )

        self.assertIsNotNone(
            store.load_device(
                "device-b",
            )
        )

    def test_clear_affects_only_current_scope(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-a",
            connection_factory=factory,
        )

        store_b = PostgreSQLPushDeviceStore(
            database_url="postgresql://test",
            scope_key="user-b",
            connection_factory=factory,
        )

        store_a.save_device(
            PushDevice(
                installation_id="device-a",
                fcm_token="token-a",
            )
        )

        store_b.save_device(
            PushDevice(
                installation_id="device-b",
                fcm_token="token-b",
            )
        )

        store_a.clear()

        self.assertEqual(
            store_a.load_all(),
            (),
        )

        self.assertEqual(
            len(
                store_b.load_all()
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()