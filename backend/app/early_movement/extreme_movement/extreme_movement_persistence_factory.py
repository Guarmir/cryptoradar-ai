
from typing import Optional

from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_service import (
    ExtremeMovementPersistenceService,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    PostgreSQLExtremeMovementActiveStore,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_observation_store import (
    PostgreSQLExtremeMovementObservationStore,
)


EXTREME_MOVEMENT_SCOPE_KEY = "extreme-movement-shadow"


def build_extreme_movement_persistence_service(
    *,
    database_url: Optional[str],
    observation_store: ExtremeMovementObservationStore,
) -> Optional[ExtremeMovementPersistenceService]:
    if database_url is None or not database_url.strip():
        return None

    database_url = database_url.strip()

    history_store = PostgreSQLExtremeMovementObservationStore(
        database_url=database_url,
        scope_key=EXTREME_MOVEMENT_SCOPE_KEY,
    )

    active_store = PostgreSQLExtremeMovementActiveStore(
        database_url=database_url,
        scope_key=EXTREME_MOVEMENT_SCOPE_KEY,
    )

    def connection_factory():
        import psycopg

        return psycopg.connect(database_url)

    return ExtremeMovementPersistenceService(
        observation_store=observation_store,
        history_store=history_store,
        active_store=active_store,
        connection_factory=connection_factory,
    )
