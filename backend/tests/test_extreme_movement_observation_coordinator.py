
from unittest.mock import MagicMock

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)
from app.early_movement.extreme_movement.extreme_movement_observation_coordinator import (
    ExtremeMovementObservationCoordinator,
)
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)


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


def test_memory_only_mode():
    memory = ExtremeMovementObservationStore()

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
    )

    result = coordinator.update((make_entry(),))

    assert result.observations[0].change == "new_observation"
    assert len(result.active_assets) == 1


def test_restores_before_first_update():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()

    def restore_previous():
        memory.update((make_entry(20.0),))
        return True

    persistence.restore.side_effect = restore_previous

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    result = coordinator.update((make_entry(40.0),))

    assert result.observations[0].change == "strengthening"
    persistence.restore.assert_called_once()
    persistence.persist.assert_called_once_with(result)


def test_restore_runs_only_once():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    coordinator.update((make_entry(),))
    coordinator.update((make_entry(40.0),))

    persistence.restore.assert_called_once()
    assert persistence.persist.call_count == 2


def test_restore_failure_falls_back_to_memory():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()
    persistence.restore.side_effect = RuntimeError(
        "database unavailable"
    )

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    result = coordinator.update((make_entry(),))

    assert result.observations[0].change == "new_observation"
    persistence.persist.assert_not_called()


def test_restore_failure_does_not_retry():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()
    persistence.restore.side_effect = RuntimeError(
        "database unavailable"
    )

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    coordinator.update((make_entry(),))
    coordinator.update((make_entry(40.0),))

    persistence.restore.assert_called_once()
    persistence.persist.assert_not_called()


def test_persist_failure_does_not_interrupt_tracking():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()
    persistence.persist.side_effect = RuntimeError(
        "write failure"
    )

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    first = coordinator.update((make_entry(),))
    second = coordinator.update((make_entry(40.0),))

    assert first.observations[0].change == "new_observation"
    assert second.observations[0].change == "strengthening"

    persistence.persist.assert_called_once()


def test_no_persistence_after_failure():
    memory = ExtremeMovementObservationStore()
    persistence = MagicMock()
    persistence.persist.side_effect = RuntimeError(
        "write failure"
    )

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
        persistence_service=persistence,
    )

    coordinator.update((make_entry(),))
    coordinator.update((make_entry(40.0),))

    assert persistence.persist.call_count == 1
    assert coordinator._persistence_available is False


def test_empty_cycle_without_persistence():
    memory = ExtremeMovementObservationStore()

    coordinator = ExtremeMovementObservationCoordinator(
        observation_store=memory,
    )

    result = coordinator.update(())

    assert result.observations == ()
    assert result.active_assets == ()
    assert result.missing_assets == ()
