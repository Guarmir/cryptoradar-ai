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

def test_alert_decision_accepts_relevant_observation() -> None:
    weak_observation = FakeRankedResult(
        relevance_score=69.9,
        state=EarlyMovementState.OBSERVATION,
    )

    strong_observation = FakeRankedResult(
        relevance_score=70.0,
        state=EarlyMovementState.OBSERVATION,
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker()

    decision = decision_maker.decide(
        make_scan_result(
            weak_observation,
            strong_observation,
        )
    )

    assert decision.should_alert is True
    assert decision.results == (strong_observation,)


def test_alert_decision_ignores_normal_state() -> None:
    normal = FakeRankedResult(
        relevance_score=100.0,
        state=EarlyMovementState.NORMAL,
    )

    observation = FakeRankedResult(
        relevance_score=100.0,
        state=EarlyMovementState.OBSERVATION,
    )

    early_movement = FakeRankedResult(
        relevance_score=80.0,
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    confirmed_movement = FakeRankedResult(
        relevance_score=85.0,
        state=EarlyMovementState.CONFIRMED_MOVEMENT,
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker()

    decision = decision_maker.decide(
        make_scan_result(
            normal,
            observation,
            early_movement,
            confirmed_movement,
        )
    )

    assert decision.should_alert is True
    assert decision.results == (
        observation,
        early_movement,
        confirmed_movement,
    )

    
from types import SimpleNamespace

from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)


def make_observation_with_evidence(
    *,
    price_acceleration: float,
    false_breakout_risk: float = 40.0,
):
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=price_acceleration,
        abnormal_volume_ratio=1.10,
        liquidity_score=70.0,
        volatility_expansion=1.20,
        support_break=True,
        persistence_score=55.0,
        false_breakout_risk=false_breakout_risk,
    )

    return SimpleNamespace(
        relevance_score=55.0,
        state=EarlyMovementState.OBSERVATION,
        result=SimpleNamespace(
            analysis=SimpleNamespace(
                evidence=evidence,
            ),
        ),
    )


def test_early_observation_enabled_accepts_relevant_signal() -> None:
    signal = make_observation_with_evidence(
        price_acceleration=-0.80,
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker(
        enable_early_observation=True,
    )

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is True
    assert decision.results == (signal,)


def test_early_observation_disabled_preserves_previous_rule() -> None:
    signal = make_observation_with_evidence(
        price_acceleration=-0.80,
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker()

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is False
    assert decision.results == ()

    
def test_alert_decision_accepts_strong_early_observation() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=2.254,
        abnormal_volume_ratio=0.907,
        liquidity_score=70.0,
        volatility_expansion=1.589,
        support_break=False,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=12.0,
        false_breakout_risk=50.0,
    )

    signal = SimpleNamespace(
        relevance_score=48.1,
        state=EarlyMovementState.OBSERVATION,
        result=SimpleNamespace(
            analysis=SimpleNamespace(evidence=evidence),
        ),
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker(
        enable_early_observation=True,
    )

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is True
    assert decision.results == (signal,)


def test_alert_decision_blocks_strong_early_observation_when_disabled() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=2.254,
        abnormal_volume_ratio=0.907,
        liquidity_score=70.0,
        volatility_expansion=1.589,
        support_break=False,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=12.0,
        false_breakout_risk=50.0,
    )

    signal = SimpleNamespace(
        relevance_score=48.1,
        state=EarlyMovementState.OBSERVATION,
        result=SimpleNamespace(
            analysis=SimpleNamespace(evidence=evidence),
        ),
    )

    decision_maker = EarlyMovementScannerAlertDecisionMaker(
        enable_early_observation=False,
    )

    decision = decision_maker.decide(
        make_scan_result(signal)
    )

    assert decision.should_alert is False
    assert decision.results == ()

