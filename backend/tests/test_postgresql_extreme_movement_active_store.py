
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    ExtremeMovementActiveRecord,
    PostgreSQLExtremeMovementActiveStore,
)


FIRST_OBSERVED = datetime(
    2026, 10, 25, 10, 0, tzinfo=timezone.utc
)

LAST_OBSERVED = datetime(
    2026, 10, 25, 12, 0, tzinfo=timezone.utc
)


def make_record(
    *,
    status="active",
    missed_cycles=0,
):
    assessment = ExtremeMovementAssessment(
        state="movement_pressure",
        direction="up",
        relevance_score=42.5,
        supporting_evidence_count=2,
    )

    maturity = ExtremeMovementMaturity(
        level="developing",
        evidence_count=2,
        relevance_score=42.5,
    )

    entry = ExtremeMovementAnalysisEntry(
        coin_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        assessment=assessment,
        maturity=maturity,
    )

    return ExtremeMovementActiveRecord(
        entry=entry,
        missed_cycles=missed_cycles,
        first_observed_at=FIRST_OBSERVED,
        last_observed_at=LAST_OBSERVED,
        observation_status=status,
    )


def make_store():
    connection = MagicMock()
    cursor = connection.cursor.return_value

    store = PostgreSQLExtremeMovementActiveStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=lambda url: connection,
    )

    return store, connection, cursor


def make_row(record):
    entry = record.entry
    assessment = entry.assessment

    return (
        entry.coin_id,
        entry.symbol,
        entry.name,
        assessment.state,
        assessment.direction,
        assessment.relevance_score,
        assessment.supporting_evidence_count,
        entry.maturity.level,
        record.observation_status,
        record.missed_cycles,
        record.first_observed_at,
        record.last_observed_at,
    )


def test_save_active_record():
    store, connection, cursor = make_store()

    store.save(make_record())

    cursor.execute.assert_called_once()
    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO" in sql
    assert "ON CONFLICT" in sql
    assert params[0] == "extreme-movement-shadow"
    assert params[1] == "bitcoin"
    assert params[9] == "active"

    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_save_awaiting_update_record():
    store, connection, cursor = make_store()

    store.save(
        make_record(
            status="awaiting_update",
            missed_cycles=3,
        )
    )

    _, params = cursor.execute.call_args.args

    assert params[9] == "awaiting_update"
    assert params[10] == 3

    connection.commit.assert_called_once()


def test_save_rolls_back_on_error():
    store, connection, cursor = make_store()

    cursor.execute.side_effect = RuntimeError(
        "database error"
    )

    with pytest.raises(RuntimeError):
        store.save(make_record())

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    connection.close.assert_called_once()


def test_load_active_records():
    store, connection, cursor = make_store()
    record = make_record()

    cursor.fetchall.return_value = [
        make_row(record)
    ]

    results = store.load_active()

    assert results == (record,)

    sql, params = cursor.execute.call_args.args

    assert "observation_status IN" in sql
    assert params == ("extreme-movement-shadow",)

    connection.close.assert_called_once()


def test_load_awaiting_update_records():
    store, _, cursor = make_store()

    record = make_record(
        status="awaiting_update",
        missed_cycles=2,
    )

    cursor.fetchall.return_value = [
        make_row(record)
    ]

    results = store.load_active()

    assert len(results) == 1
    assert results[0] == record


def test_load_active_empty():
    store, _, cursor = make_store()

    cursor.fetchall.return_value = []

    assert store.load_active() == ()


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementActiveStore(
            database_url="",
            scope_key="shadow",
        )

    with pytest.raises(ValueError):
        PostgreSQLExtremeMovementActiveStore(
            database_url="postgresql://test",
            scope_key="",
        )


@pytest.mark.parametrize(
    "status,missed_cycles",
    [
        ("invalid", 0),
        ("active", -1),
    ],
)
def test_rejects_invalid_record(
    status,
    missed_cycles,
):
    store, connection, _ = make_store()

    with pytest.raises(ValueError):
        store.save(
            make_record(
                status=status,
                missed_cycles=missed_cycles,
            )
        )

    connection.cursor.assert_not_called()


def test_rejects_missing_maturity():
    store, connection, _ = make_store()
    record = make_record()

    entry = ExtremeMovementAnalysisEntry(
        coin_id=record.entry.coin_id,
        symbol=record.entry.symbol,
        name=record.entry.name,
        assessment=record.entry.assessment,
        maturity=None,
    )

    invalid_record = ExtremeMovementActiveRecord(
        entry=entry,
        missed_cycles=0,
        first_observed_at=FIRST_OBSERVED,
        last_observed_at=LAST_OBSERVED,
    )

    with pytest.raises(ValueError):
        store.save(invalid_record)

    connection.cursor.assert_not_called()


def test_rejects_invalid_dates():
    store, connection, _ = make_store()
    record = make_record()

    invalid_record = ExtremeMovementActiveRecord(
        entry=record.entry,
        missed_cycles=0,
        first_observed_at=LAST_OBSERVED,
        last_observed_at=FIRST_OBSERVED,
    )

    with pytest.raises(ValueError):
        store.save(invalid_record)

    connection.cursor.assert_not_called()
