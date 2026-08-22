import json
import unittest

from app.monitoring.monitoring_observation import (
    MonitoringObservation,
)
from app.monitoring.monitoring_state import (
    MonitoringState,
)
from app.monitoring.postgresql_monitoring_state_store import (
    PostgreSQLMonitoringStateStore,
)
from app.monitoring.monitoring_target import (
    MonitoringTarget,
)


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
            symbol = params[1]
            encoded = params[2]

            self.database.rows[
                (
                    scope_key,
                    symbol,
                )
            ] = json.loads(
                encoded,
            )

            self.rowcount = 1
            return

        if normalized.startswith(
            "select state_data"
        ):
            scope_key = params[0]

            if "and symbol = %s" in normalized:
                symbol = params[1]

                value = self.database.rows.get(
                    (
                        scope_key,
                        symbol,
                    )
                )

                if value is not None:
                    self._rows = [
                        (
                            value,
                        )
                    ]

                return

            matching = [
                (
                    symbol,
                    value,
                )
                for (
                    current_scope,
                    symbol,
                ),
                value
                in self.database.rows.items()
                if current_scope
                == scope_key
            ]

            matching.sort(
                key=lambda item: item[0]
            )

            self._rows = [
                (
                    value,
                )
                for _, value
                in matching
            ]

            return

        if normalized.startswith(
            "delete from"
        ):
            scope_key = params[0]

            if "and symbol = %s" in normalized:
                symbol = params[1]

                key = (
                    scope_key,
                    symbol,
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


def _build_state(
    *,
    symbol="PIPPIN",
    price=0.4285,
    side="long",
):
    target = MonitoringTarget(
        symbol=symbol,
        coin_id=symbol.lower(),
        trading_mode="futures",
        has_open_position=True,
        position_side=side,
        entry_price=price,
        leverage=10,
    )

    state = MonitoringState(
        target=target,
    )

    return state.observe(
        MonitoringObservation(
            symbol=symbol,
            price=price,
            volume=150_000_000,
        )
    )


class PostgreSQLMonitoringStateStoreTest(
    unittest.TestCase
):
    def test_rejects_empty_database_url(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            PostgreSQLMonitoringStateStore(
                database_url=" ",
                scope_key="user-a",
            )

    def test_rejects_empty_scope(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key=" ",
            )

    def test_saves_and_restores_state(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=factory,
            )
        )

        original = _build_state()

        store.save_state(
            original,
        )

        restored = store.load_state(
            "pippin",
        )

        self.assertIsNotNone(
            restored,
        )

        self.assertEqual(
            restored.target.symbol,
            "PIPPIN",
        )

        self.assertTrue(
            restored.target.is_long,
        )

        self.assertEqual(
            restored.current_price,
            0.4285,
        )

        self.assertEqual(
            restored.observation_count,
            1,
        )

    def test_updates_same_symbol_without_duplicate(
        self,
    ):
        database = _FakeDatabase()

        store = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=
                    _FakeConnectionFactory(
                        database,
                    ),
            )
        )

        first = _build_state(
            price=0.42,
        )

        store.save_state(
            first,
        )

        second = first.observe(
            MonitoringObservation(
                symbol="PIPPIN",
                price=0.43,
            )
        )

        store.save_state(
            second,
        )

        states = store.load_all()

        self.assertEqual(
            len(states),
            1,
        )

        self.assertEqual(
            states[0].observation_count,
            2,
        )

        self.assertEqual(
            states[0].current_price,
            0.43,
        )

    def test_scopes_isolate_same_symbol(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=factory,
            )
        )

        store_b = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-b",
                connection_factory=factory,
            )
        )

        store_a.save_state(
            _build_state(
                price=0.42,
                side="long",
            )
        )

        store_b.save_state(
            _build_state(
                price=0.50,
                side="short",
            )
        )

        state_a = store_a.load_state(
            "PIPPIN",
        )

        state_b = store_b.load_state(
            "PIPPIN",
        )

        self.assertEqual(
            state_a.current_price,
            0.42,
        )

        self.assertTrue(
            state_a.target.is_long,
        )

        self.assertEqual(
            state_b.current_price,
            0.50,
        )

        self.assertTrue(
            state_b.target.is_short,
        )

        self.assertEqual(
            len(database.rows),
            2,
        )

    def test_load_all_returns_only_current_scope(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=factory,
            )
        )

        store_b = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-b",
                connection_factory=factory,
            )
        )

        store_a.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        store_a.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="ETH",
                )
            )
        )

        store_b.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="PIPPIN",
                )
            )
        )

        states = store_a.load_all()

        symbols = [
            state.target.symbol
            for state in states
        ]

        self.assertEqual(
            symbols,
            [
                "BTC",
                "ETH",
            ],
        )

    def test_delete_removes_only_requested_symbol(
        self,
    ):
        database = _FakeDatabase()

        store = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=
                    _FakeConnectionFactory(
                        database,
                    ),
            )
        )

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        store.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="ETH",
                )
            )
        )

        removed = store.delete_state(
            "btc",
        )

        self.assertTrue(
            removed,
        )

        self.assertIsNone(
            store.load_state(
                "BTC",
            )
        )

        self.assertIsNotNone(
            store.load_state(
                "ETH",
            )
        )

    def test_clear_affects_only_current_scope(
        self,
    ):
        database = _FakeDatabase()

        factory = _FakeConnectionFactory(
            database,
        )

        store_a = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-a",
                connection_factory=factory,
            )
        )

        store_b = (
            PostgreSQLMonitoringStateStore(
                database_url=(
                    "postgresql://test"
                ),
                scope_key="user-b",
                connection_factory=factory,
            )
        )

        store_a.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
            )
        )

        store_b.save_state(
            MonitoringState(
                target=MonitoringTarget(
                    symbol="BTC",
                )
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