
from app.early_movement.scanner.scanner_candidate_rotation import (
    EarlyMovementScannerCandidateRotation,
)
from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)


class FakeCandidate:
    def __init__(self, coin_id: str) -> None:
        self.coin_id = coin_id


def test_rotation_distributes_chart_acquisitions():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    acquired = []

    def fake_chart_loader(coin_id, days):
        acquired.append(coin_id)
        return {"prices": [[1, 100.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=fake_chart_loader,
        cache_loader=lambda coin_id, days: None,
        request_budget=4,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(20)
    )

    for _ in range(5):
        loader.reset_budget()

        ordered = rotation.arrange(
            candidates,
            acquisition_budget=4,
        )

        for candidate in ordered:
            loader(candidate.coin_id, 7)

        assert loader.stats.acquisition_attempts == 4
        assert loader.stats.budget_exhausted == 16

    assert len(acquired) == 20
    assert len(set(acquired)) == 16


def test_rotation_handles_changing_candidate_order():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(8)
    )

    first = rotation.arrange(
        candidates,
        acquisition_budget=4,
    )

    second = rotation.arrange(
        tuple(reversed(candidates)),
        acquisition_budget=4,
    )

    first_rotating = {
        candidate.coin_id
        for candidate in first[1:4]
    }

    second_rotating = {
        candidate.coin_id
        for candidate in second[1:4]
    }

    assert first_rotating.isdisjoint(
        second_rotating
    )

    
def test_failed_candidate_does_not_monopolize_rotation():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=0,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(6)
    )

    first = rotation.arrange(
        candidates,
        acquisition_budget=2,
    )

    assert tuple(
        candidate.coin_id
        for candidate in first[:2]
    ) == ("coin-0", "coin-1")

    rotation.record_failure("coin-0")
    rotation.record_failure("coin-1")

    second = rotation.arrange(
        candidates,
        acquisition_budget=2,
    )

    assert tuple(
        candidate.coin_id
        for candidate in second[:2]
    ) == ("coin-2", "coin-3")


def test_successful_candidate_does_not_repeat_immediately():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=0,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(6)
    )

    first = rotation.arrange(
        candidates,
        acquisition_budget=2,
    )

    for candidate in first[:2]:
        rotation.record_success(candidate.coin_id)

    second = rotation.arrange(
        candidates,
        acquisition_budget=2,
    )

    assert tuple(
        candidate.coin_id
        for candidate in second[:2]
    ) == ("coin-2", "coin-3")

