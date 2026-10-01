from datetime import datetime, timezone

import pytest

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.postgresql_scanner_signal_history_store import (
    PostgreSQLEarlyMovementScannerSignalHistoryStore,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)


class FakeDatabase:
    def __init__(
        self,
    ) -> None:
        self.rows = []
        self.next_id = 1


class FakeConnectionFactory:
    def __init__(
        self,
        database,
    ) -> None:
        self.database = database

    def __call__(
        self,
        database_url,
    ):
        return FakeConnection(
            self.database,
        )


class FakeConnection:
    def __init__(
        self,
        database,
    ) -> None:
        self.database = database
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(
        self,
    ):
        return FakeCursor(
            self.database,
        )

    def commit(
        self,
    ) -> None:
        self.commit_count += 1

    def rollback(
        self,
    ) -> None:
        self.rollback_count += 1

    def close(
        self,
    ) -> None:
        self.closed = True


class FakeCursor:
    def __init__(
        self,
        database,
    ) -> None:
        self.database = database
        self._rows = []
        self.closed = False

    def execute(
        self,
        query,
        params,
    ) -> None:
        normalized = " ".join(
            query.split()
        ).lower()

        self._rows = []

        if normalized.startswith(
            "insert into"
        ):
            row = {
                "id": self.database.next_id,
                "scope_key": params[0],
                "values": tuple(
                    params[1:]
                ),
            }

            self.database.next_id += 1

            self.database.rows.append(
                row,
            )

            return

        if normalized.startswith(
            "select observed_at"
        ):
            scope_key = params[0]
            limit = params[1]

            matching = [
                row
                for row in self.database.rows
                if row["scope_key"]
                == scope_key
            ]

            matching.sort(
                key=lambda row: (
                    row["values"][0],
                    row["id"],
                ),
                reverse=True,
            )

            self._rows = [
                row["values"]
                for row in matching[
                    :limit
                ]
            ]

            return

        raise AssertionError(
            "SQL não reconhecido pelo fake: "
            f"{normalized}"
        )

    def fetchall(
        self,
    ):
        return list(
            self._rows,
        )

    def close(
        self,
    ) -> None:
        self.closed = True


def make_record(
    *,
    coin_id: str = "uniswap",
    symbol: str = "UNI",
    observed_at: datetime | None = None,
    alertable: bool = True,
):
    return EarlyMovementScannerSignalHistoryRecord(
        observed_at=(
            observed_at
            or datetime(
                2026,
                10,
                1,
                12,
                0,
                tzinfo=timezone.utc,
            )
        ),
        coin_id=coin_id,
        symbol=symbol,
        name=symbol,
        current_price=12.5,
        state=(
            EarlyMovementState.EARLY_MOVEMENT
        ),
        relevance_score=82.0,
        price_acceleration=2.1,
        abnormal_volume_ratio=1.8,
        liquidity_score=85.0,
        volatility_expansion=1.4,
        persistence_score=72.0,
        false_breakout_risk=18.0,
        support_break=False,
        resistance_break=True,
        retest_confirmed=True,
        breakout_direction="up",
        alertable=alertable,
    )


def test_store_rejects_empty_database_url() -> None:
    with pytest.raises(
        ValueError,
    ):
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url=" ",
            scope_key="test-scope",
        )


def test_store_rejects_empty_scope() -> None:
    with pytest.raises(
        ValueError,
    ):
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key=" ",
        )


def test_store_saves_and_loads_record() -> None:
    database = FakeDatabase()

    store = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="test-scope",
            connection_factory=(
                FakeConnectionFactory(
                    database,
                )
            ),
        )
    )

    store.save(
        make_record()
    )

    records = store.load_recent()

    assert len(records) == 1

    record = records[0]

    assert record.coin_id == "uniswap"
    assert record.symbol == "UNI"

    assert (
        record.state
        == EarlyMovementState.EARLY_MOVEMENT
    )

    assert record.relevance_score == 82.0
    assert record.alertable is True
    assert record.resistance_break is True
    assert record.retest_confirmed is True

    assert (
        record.breakout_direction
        == "up"
    )


def test_store_preserves_history() -> None:
    database = FakeDatabase()

    store = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="test-scope",
            connection_factory=(
                FakeConnectionFactory(
                    database,
                )
            ),
        )
    )

    store.save(
        make_record(
            alertable=False,
        )
    )

    store.save(
        make_record(
            alertable=True,
        )
    )

    records = store.load_recent()

    assert len(records) == 2

    assert records[0].alertable is True
    assert records[1].alertable is False


def test_store_isolates_scope() -> None:
    database = FakeDatabase()

    factory = FakeConnectionFactory(
        database,
    )

    store_a = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="scope-a",
            connection_factory=factory,
        )
    )

    store_b = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="scope-b",
            connection_factory=factory,
        )
    )

    store_a.save(
        make_record(
            coin_id="bitcoin",
            symbol="BTC",
        )
    )

    store_b.save(
        make_record(
            coin_id="ethereum",
            symbol="ETH",
        )
    )

    records_a = (
        store_a.load_recent()
    )

    records_b = (
        store_b.load_recent()
    )

    assert len(records_a) == 1
    assert len(records_b) == 1

    assert (
        records_a[0].coin_id
        == "bitcoin"
    )

    assert (
        records_b[0].coin_id
        == "ethereum"
    )


def test_store_respects_recent_limit() -> None:
    database = FakeDatabase()

    store = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="test-scope",
            connection_factory=(
                FakeConnectionFactory(
                    database,
                )
            ),
        )
    )

    for index in range(5):
        store.save(
            make_record(
                coin_id=f"asset-{index}",
                symbol=f"A{index}",
            )
        )

    records = store.load_recent(
        limit=2,
    )

    assert len(records) == 2

    assert (
        records[0].coin_id
        == "asset-4"
    )

    assert (
        records[1].coin_id
        == "asset-3"
    )


def test_store_rejects_invalid_limit() -> None:
    database = FakeDatabase()

    store = (
        PostgreSQLEarlyMovementScannerSignalHistoryStore(
            database_url="postgresql://test",
            scope_key="test-scope",
            connection_factory=(
                FakeConnectionFactory(
                    database,
                )
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        store.load_recent(
            limit=0,
        )