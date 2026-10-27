
from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationCycle,
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_service import (
    ExtremeMovementPersistenceService,
)


class ExtremeMovementObservationCoordinator:
    def __init__(
        self,
        *,
        observation_store: ExtremeMovementObservationStore,
        persistence_service: ExtremeMovementPersistenceService | None = None,
    ) -> None:
        self._observation_store = observation_store
        self._persistence_service = persistence_service
        self._restore_attempted = False
        self._persistence_available = (
            persistence_service is not None
        )

    @property
    def observation_store(self) -> ExtremeMovementObservationStore:
        return self._observation_store

    def update(
        self,
        entries: tuple[ExtremeMovementAnalysisEntry, ...],
    ) -> ExtremeMovementObservationCycle:
        if (
            self._persistence_available
            and not self._restore_attempted
        ):
            self._restore_attempted = True

            try:
                self._persistence_service.restore()
            except Exception:
                self._persistence_available = False

        cycle = self._observation_store.update(entries)

        if self._persistence_available:
            try:
                self._persistence_service.persist(cycle)
            except Exception:
                self._persistence_available = False

        return cycle
