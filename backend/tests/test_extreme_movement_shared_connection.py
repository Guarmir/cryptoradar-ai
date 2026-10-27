
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
from app.early_movement.extreme_movement.extreme_movement_observation_record import (
    ExtremeMovementObservationRecord,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    ExtremeMovementActiveRecord,
    PostgreSQLExtremeMovementActiveStore,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_observation_store import (
    PostgreSQLExtremeMovementObservationStore,
)


TIMESTAMP = datetime(
    2026, 10, 25, 10, 0, tzinfo=timezone.utc
)


def make_entry():
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction="up",
            relevance_score=30.0,
            supporting_evidence_count=1,
        ),
        maturity=ExtremeMovementMaturity(
            level="developing",
            evidence_count=1,
            relevance_score=30.0,
        ),
    )


def make_history_record():
    return ExtremeMovementObservationRecord(
        observed_at=TIMESTAMP,
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        state="movement_pressure",
        direction="up",
        relevance_score=30.0,
        supporting_evidence_count=1,
        maturity_level="developing",
        observation_change="new_observation",
    )


def make_active_record():
    return ExtremeMovementActiveRecord(
        entry=make_entry(),
        missed_cycles=0,
        first_observed_at=TIMESTAMP,
        last_observed_at=TIMESTAMP,
    )


def make_history_store():
    return PostgreSQLExtremeMovementObservationStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=MagicMock(
            side_effect=AssertionError(
                "Nao deveria abrir outra conexao."
            )
        ),
    )


def make_active_store():
    return PostgreSQLExtremeMovementActiveStore(
        database_url="postgresql://test",
        scope_key="extreme-movement-shadow",
        connection_factory=MagicMock(
            side_effect=AssertionError(
                "Nao deveria abrir outra conexao."
            )
        ),
    )


@pytest.mark.parametrize(
    "store,record",
    [
        (make_history_store(), make_history_record()),
        (make_active_store(), make_active_record()),
    ],
)
def test_shared_connection_does_not_manage_transaction(
    store,
    record,
):
    connection = MagicMock()

    store.save(record, connection=connection)

    connection.cursor.return_value.execute.assert_called_once()
    connection.cursor.return_value.close.assert_called_once()

    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    connection.close.assert_not_called()


@pytest.mark.parametrize(
    "store,record",
    [
        (make_history_store(), make_history_record()),
        (make_active_store(), make_active_record()),
    ],
)
def test_shared_connection_failure_is_propagated(
    store,
    record,
):
    connection = MagicMock()
    connection.cursor.return_value.execute.side_effect = (
        RuntimeError("database failure")
    )

    with pytest.raises(RuntimeError):
        store.save(record, connection=connection)

    connection.rollback.assert_not_called()
    connection.commit.assert_not_called()
    connection.close.assert_not_called()
    connection.cursor.return_value.close.assert_called_once()
