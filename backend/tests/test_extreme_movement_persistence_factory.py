
from unittest.mock import patch

from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_factory import (
    EXTREME_MOVEMENT_SCOPE_KEY,
    build_extreme_movement_persistence_service,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_service import (
    ExtremeMovementPersistenceService,
)


def test_factory_returns_none_without_database_url():
    memory = ExtremeMovementObservationStore()

    assert build_extreme_movement_persistence_service(
        database_url=None,
        observation_store=memory,
    ) is None


def test_factory_returns_none_for_empty_database_url():
    memory = ExtremeMovementObservationStore()

    assert build_extreme_movement_persistence_service(
        database_url="   ",
        observation_store=memory,
    ) is None


def test_factory_builds_persistence_service():
    memory = ExtremeMovementObservationStore()

    service = build_extreme_movement_persistence_service(
        database_url="postgresql://test",
        observation_store=memory,
    )

    assert isinstance(
        service,
        ExtremeMovementPersistenceService,
    )

    assert service._observation_store is memory
    assert service._history_store.scope_key == (
        EXTREME_MOVEMENT_SCOPE_KEY
    )


def test_factory_uses_independent_shadow_scope():
    assert EXTREME_MOVEMENT_SCOPE_KEY == (
        "extreme-movement-shadow"
    )
    assert EXTREME_MOVEMENT_SCOPE_KEY != (
        "early-movement-production"
    )


def test_factory_prepares_shared_connection():
    memory = ExtremeMovementObservationStore()

    service = build_extreme_movement_persistence_service(
        database_url="postgresql://test",
        observation_store=memory,
    )

    with patch("psycopg.connect") as connect:
        service._connection_factory()

    connect.assert_called_once_with(
        "postgresql://test"
    )


def test_factory_does_not_connect_during_creation():
    memory = ExtremeMovementObservationStore()

    with patch("psycopg.connect") as connect:
        service = build_extreme_movement_persistence_service(
            database_url="postgresql://test",
            observation_store=memory,
        )

    assert service is not None
    connect.assert_not_called()
