
from dataclasses import replace

from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_early_observation_evaluator import (
    EarlyMovementScannerEarlyObservationEvaluator,
)


def make_evidence(**overrides) -> EarlyMovementEvidence:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=-0.8,
        abnormal_volume_ratio=1.1,
        liquidity_score=70.0,
        volatility_expansion=1.2,
        support_break=True,
        persistence_score=55.0,
        false_breakout_risk=40.0,
    )
    return replace(evidence, **overrides)


def test_accepts_relevant_downward_observation() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    assert evaluator.is_relevant(make_evidence()) is True


def test_accepts_relevant_upward_observation() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=0.8,
        support_break=False,
        resistance_break=True,
    )

    assert evaluator.is_relevant(evidence) is True


def test_accepts_downward_breakout_with_positive_acceleration() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=0.8,
        support_break=True,
        resistance_break=False,
    )

    assert evaluator.is_relevant(evidence) is True


def test_accepts_upward_breakout_with_negative_acceleration() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=-0.8,
        support_break=False,
        resistance_break=True,
    )

    assert evaluator.is_relevant(evidence) is True


def test_rejects_simultaneous_opposite_breakouts() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        support_break=True,
        resistance_break=True,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_insufficient_acceleration() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=0.3,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_excessive_false_breakout_risk() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        false_breakout_risk=70.0,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_insufficient_liquidity() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        liquidity_score=30.0,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_missing_essential_information() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        abnormal_volume_ratio=None,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_insufficient_supporting_evidence() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        abnormal_volume_ratio=0.8,
        volatility_expansion=1.0,
        persistence_score=40.0,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_non_observation_state() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        state=EarlyMovementState.EARLY_MOVEMENT,
    )

    assert evaluator.is_relevant(evidence) is False

    
def test_accepts_early_upward_observation_with_strong_evidence() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
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

    assert evaluator.is_relevant(evidence) is True


def test_accepts_early_downward_observation_with_strong_evidence() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=-2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.6,
        support_break=True,
        resistance_break=False,
        retest_confirmed=True,
        persistence_score=15.0,
    )

    assert evaluator.is_relevant(evidence) is True


def test_rejects_early_observation_without_retest() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.6,
        persistence_score=12.0,
        retest_confirmed=False,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_early_observation_with_weak_persistence() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.6,
        persistence_score=8.0,
        retest_confirmed=True,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_early_observation_with_insufficient_volatility() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.3,
        persistence_score=12.0,
        retest_confirmed=True,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_early_observation_with_excessive_risk() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.6,
        persistence_score=12.0,
        retest_confirmed=True,
        false_breakout_risk=60.0,
    )

    assert evaluator.is_relevant(evidence) is False


def test_rejects_early_observation_with_low_liquidity() -> None:
    evaluator = EarlyMovementScannerEarlyObservationEvaluator()

    evidence = make_evidence(
        price_acceleration=2.0,
        abnormal_volume_ratio=0.9,
        volatility_expansion=1.6,
        persistence_score=12.0,
        retest_confirmed=True,
        liquidity_score=40.0,
    )

    assert evaluator.is_relevant(evidence) is False

