
from typing import Optional

from app.early_movement.extreme_movement.extreme_movement_observation_coordinator import (
    ExtremeMovementObservationCoordinator,
)
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_config import (
    ExtremeMovementPersistenceConfig,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_factory import (
    build_extreme_movement_persistence_service,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_config import (
    ExtremeMovementShadowConfig,
)


def build_extreme_movement_observation_coordinator(
    *,
    database_url: Optional[str],
) -> Optional[ExtremeMovementObservationCoordinator]:
    if not ExtremeMovementShadowConfig.is_enabled():
        return None

    if not ExtremeMovementPersistenceConfig.is_enabled():
        return None

    if database_url is None or not database_url.strip():
        return None

    observation_store = ExtremeMovementObservationStore()

    persistence_service = build_extreme_movement_persistence_service(
        database_url=database_url,
        observation_store=observation_store,
    )

    if persistence_service is None:
        return None

    return ExtremeMovementObservationCoordinator(
        observation_store=observation_store,
        persistence_service=persistence_service,
    )
