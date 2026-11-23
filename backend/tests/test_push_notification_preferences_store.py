import unittest

from app.push.push_notification_preferences import PushNotificationPreferences
from app.push.postgresql_push_notification_preferences_store import (
    PostgreSQLPushNotificationPreferencesStore,
)


class FakeCursor:
    def __init__(self, db):
        self.db = db
        self.result = None

    def execute(self, sql, params):
        if "SELECT" in sql:
            self.result = self.db.rows.get((params[0], params[1]))
        elif "INSERT" in sql:
            self.db.rows[(params[0], params[1])] = tuple(params[2:5])
        else:
            raise AssertionError("SQL inesperado")

    def fetchone(self):
        return self.result

    def close(self):
        pass


class FakeConnection:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class FakeDatabase:
    def __init__(self):
        self.rows = {}

    def connect(self, _url):
        return FakeConnection(self)


class PushNotificationPreferencesStoreTest(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.store = PostgreSQLPushNotificationPreferencesStore(
            database_url="postgresql://fake/db",
            scope_key="scanner",
            connection_factory=self.db.connect,
        )

    def test_legacy_installation_defaults_to_all_enabled(self):
        preferences = self.store.load("legacy-device")
        self.assertTrue(preferences.allows_state("observation"))
        self.assertTrue(preferences.allows_state("early_movement"))
        self.assertTrue(preferences.allows_state("confirmed_movement"))

    def test_save_then_load_isolated_by_installation(self):
        self.store.save(
            "device-a",
            PushNotificationPreferences(
                observation_enabled=False,
                early_movement_enabled=True,
                confirmed_movement_enabled=False,
            ),
        )
        selected = self.store.load("device-a")
        untouched = self.store.load("device-b")
        self.assertFalse(selected.observation_enabled)
        self.assertTrue(selected.early_movement_enabled)
        self.assertFalse(selected.confirmed_movement_enabled)
        self.assertTrue(untouched.observation_enabled)

    def test_isolated_by_push_scope(self):
        self.store.save("device-a", PushNotificationPreferences(observation_enabled=False))
        another_scope = PostgreSQLPushNotificationPreferencesStore(
            database_url="postgresql://fake/db",
            scope_key="other-scanner",
            connection_factory=self.db.connect,
        )
        self.assertTrue(another_scope.load("device-a").observation_enabled)

    def test_save_overwrites_preference_without_reset(self):
        preferences = PushNotificationPreferences(observation_enabled=False)
        self.store.save("device-a", preferences)
        self.store.save("device-a", preferences)
        self.assertFalse(self.store.load("device-a").observation_enabled)

    def test_unknown_event_preserves_prior_behavior(self):
        preferences = PushNotificationPreferences(observation_enabled=False)
        self.assertTrue(preferences.allows_state("unrecognized"))

    def test_blank_installation_rejected(self):
        with self.assertRaises(ValueError):
            self.store.load("   ")


if __name__ == "__main__":
    unittest.main()
