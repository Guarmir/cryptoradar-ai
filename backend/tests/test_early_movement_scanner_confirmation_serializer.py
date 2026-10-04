from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_confirmation_serializer import (
    EarlyMovementScannerConfirmationSerializer,
)


def test_serializes_missing_confirmation_criteria() -> None:
    evidence = EarlyMovementEvidence(
        state=EarlyMovementState.OBSERVATION,
        price_acceleration=1.07,
        abnormal_volume_ratio=0.99,
        liquidity_score=80.0,
        volatility_expansion=1.68,
        resistance_break=True,
        retest_confirmed=True,
        persistence_score=100.0,
        false_breakout_risk=30.0,
    )

    serializer = (
        EarlyMovementScannerConfirmationSerializer()
    )

    result = serializer.serialize(
        evidence,
    )

    assert (
        result["target_state"]
        == "early_movement"
    )

    assert result["passed_count"] == 5
    assert result["failed_count"] == 1
    assert result["is_confirmed"] is False

    assert result["missing_criteria"] == [
        {
            "key": "abnormal_volume_ratio",
            "label": "Abnormal volume",
            "value": 0.99,
            "threshold": 1.50,
            "reason": None,
        }
    ]