
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
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_service import (
    ExtremeMovementPersistenceService,
)


TIMESTAMP = datetime(
    2026, 10, 25, 10, 0, tzinfo=timezone.utc
)


def make_entry(coin_id="test-coin"):
    return ExtremeMovementAnalysisEntry(
        coin_id=coin_id,
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


def make_environment():
    memory = ExtremeMovementObservationStore()
    history = MagicMock()
    active = MagicMock()
    active.load_active.return_value = ()

    connection = MagicMock()
    connection_factory = MagicMock(
        return_value=connection
    )

    service = ExtremeMovementPersistenceService(
        observation_store=memory,
        history_store=history,
        active_store=active,
        connection_factory=connection_factory,
    )

    service.restore()

    return (
        service,
        memory,
        history,
        active,
        connection,
        connection_factory,
    )


def test_success_uses_single_connection_and_commit():
    service, memory, history, active, connection, factory = (
        make_environment()
    )

    cycle = memory.update((make_entry(),))
    service.persist(cycle, observed_at=TIMESTAMP)

    factory.assert_called_once_with()

    assert (
        history.save.call_args.kwargs["connection"]
        is connection
    )
    assert (
        active.save.call_args.kwargs["connection"]
        is connection
    )

    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    connection.close.assert_called_once()

    assert "test-coin" in service._active_records


def test_history_failure_rolls_back():
    service, memory, history, active, connection, _ = (
        make_environment()
    )

    history.save.side_effect = RuntimeError(
        "history failure"
    )

    cycle = memory.update((make_entry(),))

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=TIMESTAMP)

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()
    active.save.assert_not_called()

    assert service._active_records == {}


def test_active_failure_rolls_back():
    service, memory, history, active, connection, _ = (
        make_environment()
    )

    active.save.side_effect = RuntimeError(
        "active failure"
    )

    cycle = memory.update((make_entry(),))

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=TIMESTAMP)

    history.save.assert_called_once()
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    connection.close.assert_called_once()

    assert service._active_records == {}


def test_commit_failure_does_not_update_cache():
    service, memory, _, _, connection, _ = (
        make_environment()
    )

    connection.commit.side_effect = RuntimeError(
        "commit failure"
    )

    cycle = memory.update((make_entry(),))

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=TIMESTAMP)

    connection.rollback.assert_called_once()
    connection.close.assert_called_once()

    assert service._active_records == {}


def test_multiple_assets_use_one_transaction():
    service, memory, history, active, connection, factory = (
        make_environment()
    )

    cycle = memory.update(
        (
            make_entry("coin-a"),
            make_entry("coin-b"),
        )
    )

    service.persist(cycle, observed_at=TIMESTAMP)

    assert history.save.call_count == 2
    assert active.save.call_count == 2

    factory.assert_called_once()
    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_empty_cycle_does_not_open_connection():
    service, memory, history, active, connection, factory = (
        make_environment()
    )

    cycle = memory.update(())
    service.persist(cycle, observed_at=TIMESTAMP)

    factory.assert_not_called()
    history.save.assert_not_called()
    active.save.assert_not_called()
    connection.commit.assert_not_called()


def test_persist_requires_restore():
    memory = ExtremeMovementObservationStore()

    service = ExtremeMovementPersistenceService(
        observation_store=memory,
        history_store=MagicMock(),
        active_store=MagicMock(),
        connection_factory=MagicMock(),
    )

    cycle = memory.update((make_entry(),))

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=TIMESTAMP)


def test_rejects_naive_timestamp_before_connection():
    service, memory, history, active, _, factory = (
        make_environment()
    )

    cycle = memory.update((make_entry(),))

    with pytest.raises(ValueError):
        service.persist(
            cycle,
            observed_at=datetime(2026, 10, 25, 10, 0),
        )

    factory.assert_not_called()
    history.save.assert_not_called()
    active.save.assert_not_called()
