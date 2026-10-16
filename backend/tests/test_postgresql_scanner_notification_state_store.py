
from datetime import datetime, timezone

import pytest

from app.early_movement.scanner.postgresql_scanner_notification_state_store import (
    PostgreSQLEarlyMovementScannerNotificationStateStore,
)
from app.early_movement.scanner.scanner_notification_state_store import (
    EarlyMovementScannerNotificationState,
)


class FakeDatabase:
    def __init__(self):
        self.rows = {}


class FakeConnectionFactory:
    def __init__(self, database):
        self.database = database
        self.connections = []

    def __call__(self, database_url):
        connection = FakeConnection(self.database)
        self.connections.append(connection)
        return connection


class FakeConnection:
    def __init__(self, database):
        self.database = database
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self.database)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


class FakeCursor:
    def __init__(self, database):
        self.database = database
        self.row = None
        self.closed = False

    def execute(self, query, params):
        normalized = " ".join(query.split()).lower()

        if normalized.startswith("insert into"):
            scope_key, coin_id, state, notified_at = params

            self.database.rows[(scope_key, coin_id)] = (
                coin_id,
                state,
                notified_at,
            )
            return

        if normalized.startswith("select coin_id"):
            scope_key, coin_id = params
            self.row = self.database.rows.get(
                (scope_key, coin_id)
            )
            return

        raise AssertionError(
            f"SQL não reconhecido: {normalized}"
        )

    def fetchone(self):
        return self.row

    def close(self):
        self.closed = True


def make_state(
    *,
    coin_id="uniswap",
    state="observation",
):
    return EarlyMovementScannerNotificationState(
        coin_id=coin_id,
        last_notified_state=state,
        last_notified_at=datetime(
            2026, 10, 16, 12, 0,
            tzinfo=timezone.utc,
        ),
    )


def make_store(database, scope_key="test-scope"):
    factory = FakeConnectionFactory(database)

    return PostgreSQLEarlyMovementScannerNotificationStateStore(
        database_url="postgresql://test",
        scope_key=scope_key,
        connection_factory=factory,
    )


def test_rejects_empty_database_url():
    with pytest.raises(ValueError):
        PostgreSQLEarlyMovementScannerNotificationStateStore(
            database_url=" ",
            scope_key="test",
        )


def test_rejects_empty_scope():
    with pytest.raises(ValueError):
        PostgreSQLEarlyMovementScannerNotificationStateStore(
            database_url="postgresql://test",
            scope_key=" ",
        )


def test_load_returns_none_when_missing():
    store = make_store(FakeDatabase())

    assert store.load("bitcoin") is None


def test_saves_and_loads_notification_state():
    store = make_store(FakeDatabase())

    store.save(make_state())

    saved = store.load("uniswap")

    assert saved is not None
    assert saved.coin_id == "uniswap"
    assert saved.last_notified_state == "observation"
    assert saved.last_notified_at.tzinfo is not None


def test_updates_existing_notification_state():
    store = make_store(FakeDatabase())

    store.save(make_state(state="observation"))
    store.save(make_state(state="early_movement"))

    saved = store.load("uniswap")

    assert saved.last_notified_state == "early_movement"


def test_isolates_scope():
    database = FakeDatabase()

    store_a = make_store(database, "scope-a")
    store_b = make_store(database, "scope-b")

    store_a.save(make_state(state="observation"))
    store_b.save(make_state(state="confirmed_movement"))

    assert (
        store_a.load("uniswap").last_notified_state
        == "observation"
    )

    assert (
        store_b.load("uniswap").last_notified_state
        == "confirmed_movement"
    )


def test_save_commits_transaction():
    database = FakeDatabase()
    factory = FakeConnectionFactory(database)

    store = PostgreSQLEarlyMovementScannerNotificationStateStore(
        database_url="postgresql://test",
        scope_key="test",
        connection_factory=factory,
    )

    store.save(make_state())

    assert factory.connections[0].commit_count == 1
    assert factory.connections[0].closed is True
