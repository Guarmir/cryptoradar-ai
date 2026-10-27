
import pytest

from app.early_movement.extreme_movement.extreme_movement_persistence_config import (
    ExtremeMovementPersistenceConfig,
)


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        raising=False,
    )

    assert ExtremeMovementPersistenceConfig.is_enabled() is False


@pytest.mark.parametrize(
    "value",
    ["true", "TRUE", "1", "yes", "on", " true "],
)
def test_enabled_values(monkeypatch, value):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        value,
    )

    assert ExtremeMovementPersistenceConfig.is_enabled() is True


@pytest.mark.parametrize(
    "value",
    ["false", "0", "no", "off", "", "invalid"],
)
def test_disabled_values(monkeypatch, value):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_PERSISTENCE_ENABLED",
        value,
    )

    assert ExtremeMovementPersistenceConfig.is_enabled() is False
