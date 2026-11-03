
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from psycopg.types.json import Jsonb

from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_discovery_trace_store import (
    PostgreSQLExtremeMovementDiscoveryTraceStore,
)


def make_trace():
    return ExtremeMovementDiscoveryTrace(
        observed_at=datetime(
            2026, 11, 2, 12, 0, tzinfo=timezone.utc
        ),
        universe_size=500,
        candidate_count=20,
        analyzed_count=2,
        excluded_count=10,
        selected_coin_ids=("coin-a", "coin-b", "coin-c"),
        submitted_coin_ids=("coin-a", "coin-b"),
        not_submitted_coin_ids=("coin-c",),
    )


def make_store(connection):
    return PostgreSQLExtremeMovementDiscoveryTraceStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=lambda url: connection,
    )


def test_saves_discovery_trace():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    make_store(connection).save(make_trace())

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO" in sql
    assert "cryptoradar_extreme_movement_discovery_trace" in sql
    assert params[0] == "extreme-movement-shadow"
    assert params[2:6] == (500, 20, 2, 10)

    assert isinstance(params[6], Jsonb)
    assert isinstance(params[7], Jsonb)
    assert isinstance(params[8], Jsonb)

    assert params[6].obj == ["coin-a", "coin-b", "coin-c"]
    assert params[7].obj == ["coin-a", "coin-b"]
    assert params[8].obj == ["coin-c"]

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_rolls_back_and_closes_on_failure():
    connection = MagicMock()
    cursor = connection.cursor.return_value
    cursor.execute.side_effect = RuntimeError("database error")

    with pytest.raises(RuntimeError, match="database error"):
        make_store(connection).save(make_trace())

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_rejects_empty_database_url():
    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementDiscoveryTraceStore(
            database_url=" ",
            scope_key="extreme-movement-shadow",
        )


def test_rejects_empty_scope():
    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementDiscoveryTraceStore(
            database_url="postgresql://test",
            scope_key=" ",
        )

        
def test_saves_experimental_comparison_fields():
    from dataclasses import replace

    connection = MagicMock()
    cursor = connection.cursor.return_value

    trace = replace(
        make_trace(),
        experimental_status="completed",
        experimental_coin_ids=("coin-a", "coin-b"),
        experimental_only_coin_ids=("coin-b",),
        common_coin_ids=("coin-a",),
        experimental_priorities=(
            {
                "coin_id": "coin-b",
                "score": 76.0,
                "state": "priority",
                "direction": "up",
                "evidence_count": 3,
            },
        ),
    )

    make_store(connection).save(trace)

    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args.args

    assert "experimental_status" in sql
    assert "experimental_coin_ids" in sql
    assert "experimental_only_coin_ids" in sql
    assert "common_coin_ids" in sql
    assert "experimental_priorities" in sql

    assert len(params) == 14
    assert params[9] == "completed"

    assert isinstance(params[10], Jsonb)
    assert params[10].obj == ["coin-a", "coin-b"]

    assert isinstance(params[11], Jsonb)
    assert params[11].obj == ["coin-b"]

    assert isinstance(params[12], Jsonb)
    assert params[12].obj == ["coin-a"]

    assert isinstance(params[13], Jsonb)
    assert params[13].obj == [
        {
            "coin_id": "coin-b",
            "score": 76.0,
            "state": "priority",
            "direction": "up",
            "evidence_count": 3,
        }
    ]

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()

