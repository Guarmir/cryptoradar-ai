import pytest

from app.services.chart_request_cooldown import (
    ChartRequestCooldown,
)


def test_starts_unblocked() -> None:
    cooldown = ChartRequestCooldown()

    assert cooldown.is_blocked() is False


def test_blocks_after_activation() -> None:
    current_time = 100.0

    cooldown = ChartRequestCooldown(
        cooldown_seconds=60.0,
        clock=lambda: current_time,
    )

    cooldown.activate()

    assert cooldown.is_blocked() is True


def test_unblocks_after_cooldown_expires() -> None:
    current_time = 100.0

    def clock() -> float:
        return current_time

    cooldown = ChartRequestCooldown(
        cooldown_seconds=60.0,
        clock=clock,
    )

    cooldown.activate()

    assert cooldown.is_blocked() is True

    current_time = 161.0

    assert cooldown.is_blocked() is False


def test_reset_removes_block() -> None:
    cooldown = ChartRequestCooldown(
        cooldown_seconds=60.0,
        clock=lambda: 100.0,
    )

    cooldown.activate()

    assert cooldown.is_blocked() is True

    cooldown.reset()

    assert cooldown.is_blocked() is False


def test_rejects_invalid_cooldown() -> None:
    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        ChartRequestCooldown(
            cooldown_seconds=0,
        )