
from unittest.mock import patch

from app.early_movement.extreme_movement.extreme_movement_observation_coordinator import (
    ExtremeMovementObservationCoordinator,
)
from app.early_movement.extreme_movement.extreme_movement_runtime_bridge import (
    build_extreme_movement_observation_coordinator,
)


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        raising=False,
    )
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        raising=False,
    )

    result = build_extreme_movement_observation_coordinator(
        database_url="postgresql://test",
    )

    assert result is None


def test_shadow_disabled(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "false",
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        "true",
    )

    result = build_extreme_movement_observation_coordinator(
        database_url="postgresql://test",
    )

    assert result is None


def test_persistence_disabled(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        "false",
    )

    result = build_extreme_movement_observation_coordinator(
        database_url="postgresql://test",
    )

    assert result is None


def test_missing_database_url(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        "true",
    )

    assert build_extreme_movement_observation_coordinator(
        database_url=None,
    ) is None

    assert build_extreme_movement_observation_coordinator(
        database_url="   ",
    ) is None


def test_enabled_configuration_builds_coordinator(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        "true",
    )

    result = build_extreme_movement_observation_coordinator(
        database_url="postgresql://test",
    )

    assert isinstance(
        result,
        ExtremeMovementObservationCoordinator,
    )
    assert result.observation_store is not None


def test_creation_does_not_open_database_connection(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        "true",
    )

    with patch("psycopg.connect") as connect:
        result = build_extreme_movement_observation_coordinator(
            database_url="postgresql://test",
        )

    assert result is not None
    connect.assert_not_called()
