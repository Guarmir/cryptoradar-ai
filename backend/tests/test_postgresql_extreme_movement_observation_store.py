
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.early_movement.extreme_movement.extreme_movement_observation_record import (
    ExtremeMovementObservationRecord,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_observation_store import (
    PostgreSQLExtremeMovementObservationStore,
)


def make_record():
    return ExtremeMovementObservationRecord(
        observed_at=datetime(
            2026, 10, 25, 12, 0, tzinfo=timezone.utc
        ),
        coin_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        state="movement_pressure",
        direction="up",
        relevance_score=42.5,
        supporting_evidence_count=2,
        maturity_level="developing",
        observation_change="new_observation",
    )


def make_store():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    store = PostgreSQLExtremeMovementObservationStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=lambda url: connection,
    )

    return store, connection, cursor


def test_save_record():
    store, connection, cursor = make_store()

    store.save(make_record())

    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO" in sql
    assert params[0] == "extreme-movement-shadow"
    assert params[2] == "bitcoin"
    assert params[7] == 42.5

    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_save_rolls_back_on_error():
    store, connection, cursor = make_store()
    cursor.execute.side_effect = RuntimeError("database error")

    with pytest.raises(RuntimeError):
        store.save(make_record())

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_load_recent():
    store, connection, cursor = make_store()
    record = make_record()

    cursor.fetchall.return_value = [
        (
            record.observed_at,
            record.coin_id,
            record.symbol,
            record.name,
            record.state,
            record.direction,
            record.relevance_score,
            record.supporting_evidence_count,
            record.maturity_level,
            record.observation_change,
        )
    ]

    results = store.load_recent(limit=10)

    assert len(results) == 1
    assert results[0] == record

    sql, params = cursor.execute.call_args.args
    assert "ORDER BY observed_at DESC" in sql
    assert params == ("extreme-movement-shadow", 10)

    connection.close.assert_called_once()


def test_load_latest_for_coin():
    store, connection, cursor = make_store()
    record = make_record()

    cursor.fetchone.return_value = (
        record.observed_at,
        record.coin_id,
        record.symbol,
        record.name,
        record.state,
        record.direction,
        record.relevance_score,
        record.supporting_evidence_count,
        record.maturity_level,
        record.observation_change,
    )

    result = store.load_latest_for_coin(
        coin_id="bitcoin"
    )

    assert result == record

    sql, params = cursor.execute.call_args.args
    assert "coin_id = %s" in sql
    assert params == (
        "extreme-movement-shadow",
        "bitcoin",
    )


def test_load_latest_returns_none():
    store, _, cursor = make_store()
    cursor.fetchone.return_value = None

    result = store.load_latest_for_coin(
        coin_id="bitcoin"
    )

    assert result is None


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementObservationStore(
            database_url="",
            scope_key="shadow",
        )

    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementObservationStore(
            database_url="postgresql://test",
            scope_key="",
        )


def test_rejects_invalid_queries():
    store, connection, _ = make_store()

    with pytest.raises(ValueError):
        store.load_recent(limit=0)

    with pytest.raises(ValueError):
        store.load_latest_for_coin(coin_id=" ")

    connection.cursor.assert_not_called()
