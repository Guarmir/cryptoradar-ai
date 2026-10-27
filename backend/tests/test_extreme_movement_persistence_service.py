
from datetime import datetime, timedelta, timezone
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
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    ExtremeMovementActiveRecord,
)


T0 = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(minutes=5)
T2 = T1 + timedelta(minutes=5)


def make_entry(relevance=20.0):
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction="up",
            relevance_score=relevance,
            supporting_evidence_count=1,
        ),
        maturity=ExtremeMovementMaturity(
            level="early",
            evidence_count=1,
            relevance_score=relevance,
        ),
    )



def make_service(existing=()):
    memory = ExtremeMovementObservationStore()
    history_store = MagicMock()
    active_store = MagicMock()
    active_store.load_active.return_value = existing

    connection = MagicMock()
    connection_factory = MagicMock(
        return_value=connection
    )

    service = ExtremeMovementPersistenceService(
        observation_store=memory,
        history_store=history_store,
        active_store=active_store,
        connection_factory=connection_factory,
    )

    return service, memory, history_store, active_store



def test_restore_empty_and_persist_new_observation():
    service, memory, history, active = make_service()

    assert service.restore() is True

    cycle = memory.update((make_entry(),))
    service.persist(cycle, observed_at=T0)

    history.save.assert_called_once()
    active.save.assert_called_once()

    saved = active.save.call_args.args[0]
    assert saved.first_observed_at == T0
    assert saved.last_observed_at == T0
    assert saved.observation_status == "active"


def test_restore_preserves_previous_assessment():
    previous = ExtremeMovementActiveRecord(
        entry=make_entry(20.0),
        missed_cycles=2,
        first_observed_at=T0,
        last_observed_at=T1,
    )

    service, memory, history, active = make_service(
        (previous,)
    )

    service.restore()

    cycle = memory.update((make_entry(40.0),))

    assert cycle.observations[0].change == "strengthening"

    service.persist(cycle, observed_at=T2)

    saved = active.save.call_args.args[0]
    assert saved.first_observed_at == T0
    assert saved.last_observed_at == T2
    assert saved.missed_cycles == 0


def test_missing_asset_preserves_last_observation_time():
    previous = ExtremeMovementActiveRecord(
        entry=make_entry(),
        missed_cycles=0,
        first_observed_at=T0,
        last_observed_at=T1,
    )

    service, memory, history, active = make_service(
        (previous,)
    )

    service.restore()

    cycle = memory.update(())
    service.persist(cycle, observed_at=T2)

    history.save.assert_not_called()

    saved = active.save.call_args.args[0]
    assert saved.observation_status == "awaiting_update"
    assert saved.last_observed_at == T1
    assert saved.missed_cycles == 1


def test_persist_requires_restore():
    service, memory, history, active = make_service()

    cycle = memory.update((make_entry(),))

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=T0)

    history.save.assert_not_called()
    active.save.assert_not_called()


def test_restore_failure_does_not_mark_restored():
    service, _, _, active = make_service()
    active.load_active.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(RuntimeError):
        service.restore()

    assert service._restored is False


def test_restore_is_idempotent():
    service, _, _, active = make_service()

    assert service.restore() is True
    assert service.restore() is True

    active.load_active.assert_called_once()


def test_rejects_naive_timestamp():
    service, memory, history, active = make_service()
    service.restore()

    cycle = memory.update((make_entry(),))

    with pytest.raises(ValueError):
        service.persist(
            cycle,
            observed_at=datetime(2026, 10, 25, 10, 0),
        )

    history.save.assert_not_called()
    active.save.assert_not_called()


def test_history_failure_prevents_active_write():
    service, memory, history, active = make_service()
    service.restore()

    cycle = memory.update((make_entry(),))

    history.save.side_effect = RuntimeError(
        "history unavailable"
    )

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=T0)

    active.save.assert_not_called()


def test_active_failure_does_not_update_local_cache():
    service, memory, _, active = make_service()
    service.restore()

    cycle = memory.update((make_entry(),))

    active.save.side_effect = RuntimeError(
        "active store unavailable"
    )

    with pytest.raises(RuntimeError):
        service.persist(cycle, observed_at=T0)

    assert service._active_records == {}
