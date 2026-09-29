from dataclasses import dataclass
from typing import Optional

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecisionMaker,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


@dataclass(frozen=True)
class FakeRankedResult:
    relevance_score: float
    state: Optional[EarlyMovementState]


def make_scan_result(
    *ranked_results: FakeRankedResult,
) -> EarlyMovementScannerRunResult:
    return EarlyMovementScannerRunResult(
        universe_size=100,
        candidate_count=20,
        analyzed_count=20,
        successful_analysis_count=8,
        ranked_results=ranked_results,
    )


def test_alert_decision_without_ranked_results() -> None:
    decision_maker = (
        EarlyMovementScannerAlertDecisionMaker()
    )

    decision = decision_maker.decide(
        make_scan_result()
    )

    assert decision.should_alert is False
    assert decision.results == ()


def test_alert_decision_accepts_valid_signal() -> None:
    signal = FakeRankedResult(
        relevance_score=80.0,
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    decision_maker = (
        EarlyMovementScannerAlertDecisionMaker()
    )

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is True
    assert decision.results == (signal,)


def test_alert_decision_ignores_missing_state() -> None:
    signal = FakeRankedResult(
        relevance_score=90.0,
        state=None,
    )

    decision_maker = (
        EarlyMovementScannerAlertDecisionMaker()
    )

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is False
    assert decision.results == ()


def test_alert_decision_respects_minimum_score() -> None:
    weak_signal = FakeRankedResult(
        relevance_score=49.9,
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    strong_signal = FakeRankedResult(
        relevance_score=50.0,
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    decision_maker = (
        EarlyMovementScannerAlertDecisionMaker(
            min_relevance_score=50.0,
        )
    )

    decision = decision_maker.decide(
        make_scan_result(
            weak_signal,
            strong_signal,
        )
    )

    assert decision.should_alert is True
    assert decision.results == (
        strong_signal,
    )


def test_alert_decision_limits_alert_count() -> None:
    signals = tuple(
        FakeRankedResult(
            relevance_score=100.0 - index,
            state=EarlyMovementState.EARLY_MOVEMENT,
        )
        for index in range(5)
    )

    decision_maker = (
        EarlyMovementScannerAlertDecisionMaker(
            max_alerts=3,
        )
    )

    decision = decision_maker.decide(
        make_scan_result(
            *signals,
        )
    )

    assert decision.should_alert is True
    assert decision.results == signals[:3]