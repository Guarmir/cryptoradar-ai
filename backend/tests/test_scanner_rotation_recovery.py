
from app.early_movement.scanner.scanner_candidate_rotation import (
    EarlyMovementScannerCandidateRotation,
)


class FakeCandidate:
    def __init__(self, coin_id: str) -> None:
        self.coin_id = coin_id


def test_rotation_records_success():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=0,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(4)
    )

    rotation.arrange(
        candidates,
        acquisition_budget=2,
    )

    rotation.record_success("coin-0")

    assert rotation._last_successful["coin-0"] == 1


def test_rotation_records_failure():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=0,
    )

    candidates = (
        FakeCandidate("coin-a"),
        FakeCandidate("coin-b"),
    )

    rotation.arrange(
        candidates,
        acquisition_budget=1,
    )

    rotation.record_success("coin-a")
    rotation.record_failure("coin-a")

    assert rotation._last_successful["coin-a"] == 1


def test_rotation_cleans_inactive_candidates():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=0,
    )

    rotation.arrange(
        (
            FakeCandidate("coin-a"),
            FakeCandidate("coin-b"),
        ),
        acquisition_budget=2,
    )

    rotation.record_success("coin-a")

    rotation.arrange(
        (FakeCandidate("coin-b"),),
        acquisition_budget=2,
    )

    assert "coin-a" not in rotation._last_successful
    assert "coin-a" not in rotation._last_successful

