
from app.early_movement.scanner import (
    EarlyMovementScanner,
)
from app.early_movement.scanner.scanner_candidate_rotation import (
    EarlyMovementScannerCandidateRotation,
)


class FakeMarketProvider:
    def fetch(self):
        return tuple(range(1, 9))


class FakeCandidateSelector:
    def select(self, assets, *, limit):
        return tuple(assets[:limit])


class FakeAnalysisResult:
    def __init__(self):
        self.analysis = object()


class FakeDeepAnalyzer:
    def __init__(self):
        self.calls = []

    def analyze_candidates(self, candidates):
        candidates = tuple(candidates)
        self.calls.append(candidates)

        return tuple(
            FakeAnalysisResult()
            for _ in candidates
        )


class FakeRanker:
    def rank(self, results, *, limit):
        return tuple(results[:limit])


def test_scanner_preserves_original_order_by_default():
    analyzer = FakeDeepAnalyzer()

    scanner = EarlyMovementScanner(
        market_provider=FakeMarketProvider(),
        candidate_selector=FakeCandidateSelector(),
        deep_analyzer=analyzer,
        result_ranker=FakeRanker(),
    )

    scanner.scan()

    assert analyzer.calls == [
        (1, 2, 3, 4, 5, 6, 7, 8),
    ]


def test_scanner_rotates_candidates_between_cycles():
    analyzer = FakeDeepAnalyzer()

    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    scanner = EarlyMovementScanner(
        market_provider=FakeMarketProvider(),
        candidate_selector=FakeCandidateSelector(),
        deep_analyzer=analyzer,
        result_ranker=FakeRanker(),
        candidate_arranger=lambda candidates: (
            rotation.arrange(
                candidates,
                acquisition_budget=4,
            )
        ),
    )

    first = scanner.scan()
    second = scanner.scan()

    assert analyzer.calls[0][:4] == (
        1, 2, 3, 4,
    )

    assert analyzer.calls[1][:4] == (
        1, 5, 6, 7,
    )

    assert first.candidate_count == 8
    assert second.candidate_count == 8

    assert first.analyzed_count == 8
    assert second.analyzed_count == 8


def test_rotation_reserves_followup_slot_without_exceeding_budget():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    candidates = tuple(range(1, 9))

    result = rotation.arrange(
        candidates,
        acquisition_budget=4,
        followup_ids=("8",),
    )

    assert result[:4] == (1, 8, 2, 3)
    assert len(result[:4]) == 4
    assert set(result) == set(candidates)


def test_rotation_distributes_followup_priority_between_cycles():
    rotation = EarlyMovementScannerCandidateRotation(
        priority_slots=1,
    )

    candidates = tuple(range(1, 9))

    first = rotation.arrange(
        candidates,
        acquisition_budget=4,
        followup_ids=("7", "8"),
    )

    second = rotation.arrange(
        candidates,
        acquisition_budget=4,
        followup_ids=("7", "8"),
    )

    assert first[1] == 7
    assert second[0] == 8 or second[1] == 8
    assert len(first[:4]) == 4
    assert len(second[:4]) == 4
