import pytest

from app.early_movement.extreme_movement.extreme_movement_shadow_config import (
    ExtremeMovementShadowConfig,
)


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        ExtremeMovementShadowConfig.ENV_NAME,
        raising=False,
    )

    assert ExtremeMovementShadowConfig.is_enabled() is False


@pytest.mark.parametrize(
    "value",
    ["1", "true", "TRUE", "yes", "on"],
)
def test_enabled_values(monkeypatch, value):
    monkeypatch.setenv(
        ExtremeMovementShadowConfig.ENV_NAME,
        value,
    )

    assert ExtremeMovementShadowConfig.is_enabled() is True


@pytest.mark.parametrize(
    "value",
    ["0", "false", "no", "off", ""],
)
def test_disabled_values(monkeypatch, value):
    monkeypatch.setenv(
        ExtremeMovementShadowConfig.ENV_NAME,
        value,
    )

    assert ExtremeMovementShadowConfig.is_enabled() is False