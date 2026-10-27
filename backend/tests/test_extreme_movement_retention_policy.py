
import pytest

from app.early_movement.extreme_movement.extreme_movement_retention_policy import (
    ExtremeMovementRetentionPolicy,
)


def test_default_limit_is_12_cycles():
    policy = ExtremeMovementRetentionPolicy()

    assert policy.should_close(
        missed_cycles=11,
        collection_healthy=True,
    ) is False

    assert policy.should_close(
        missed_cycles=12,
        collection_healthy=True,
    ) is True


def test_does_not_close_when_collection_is_unhealthy():
    policy = ExtremeMovementRetentionPolicy()

    assert policy.should_close(
        missed_cycles=20,
        collection_healthy=False,
    ) is False


def test_custom_limit():
    policy = ExtremeMovementRetentionPolicy(
        max_missed_cycles=5,
    )

    assert policy.should_close(
        missed_cycles=4,
        collection_healthy=True,
    ) is False

    assert policy.should_close(
        missed_cycles=5,
        collection_healthy=True,
    ) is True


def test_zero_missed_cycles():
    policy = ExtremeMovementRetentionPolicy()

    assert policy.should_close(
        missed_cycles=0,
        collection_healthy=True,
    ) is False


def test_invalid_limit():
    with pytest.raises(ValueError):
        ExtremeMovementRetentionPolicy(
            max_missed_cycles=0,
        )


def test_negative_missed_cycles():
    policy = ExtremeMovementRetentionPolicy()

    with pytest.raises(ValueError):
        policy.should_close(
            missed_cycles=-1,
            collection_healthy=True,
        )


def test_unhealthy_collection_never_closes():
    policy = ExtremeMovementRetentionPolicy(
        max_missed_cycles=3,
    )

    for missed_cycles in (3, 10, 100):
        assert policy.should_close(
            missed_cycles=missed_cycles,
            collection_healthy=False,
        ) is False
