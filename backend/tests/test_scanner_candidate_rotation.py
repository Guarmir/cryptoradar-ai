
import pytest

from app.early_movement.scanner.scanner_candidate_rotation import (
    EarlyMovementScannerCandidateRotation,
)


def test_rotation_preserves_priority_candidate():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    candidates = tuple(range(1, 9))

    first = rotation.arrange(
        candidates,
        acquisition_budget=4,
    )

    second = rotation.arrange(
        candidates,
        acquisition_budget=4,
    )

    assert first[:4] == (1, 2, 3, 4)
    assert second[:4] == (1, 5, 6, 7)


def test_rotation_preserves_all_candidates():
    rotation = EarlyMovementScannerCandidateRotation()

    candidates = tuple(range(1, 21))

    result = rotation.arrange(
        candidates,
        acquisition_budget=4,
    )

    assert len(result) == 20
    assert set(result) == set(candidates)


def test_rotation_handles_empty_candidates():
    rotation = EarlyMovementScannerCandidateRotation()

    assert rotation.arrange(
        (),
        acquisition_budget=4,
    ) == ()


def test_rotation_rejects_invalid_budget():
    rotation = EarlyMovementScannerCandidateRotation()

    with pytest.raises(ValueError):
        rotation.arrange(
            (1, 2),
            acquisition_budget=0,
        )


def test_rotation_rejects_negative_priority_slots():
    with pytest.raises(ValueError):
        EarlyMovementScannerCandidateRotation(
            priority_slots=-1,
        )
