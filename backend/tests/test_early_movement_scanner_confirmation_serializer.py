import pytest
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

    missing = result[
        "missing_criteria"
    ]

    assert len(missing) == 1

    assert (
        missing[0]["key"]
        == "abnormal_volume_ratio"
    )

    assert missing[0]["value"] == 0.99
    assert missing[0]["threshold"] == 1.50

    assert (
        missing[0]["distance_ratio"]
        == pytest.approx(0.34)
    )

    assert (
        missing[0]["proximity"]
        == "far"
    )

    blocker = result[
        "main_blocker"
    ]

    assert blocker is not None

    assert (
        blocker["key"]
        == "abnormal_volume_ratio"
    )

    assert (
        blocker["distance_ratio"]
        == pytest.approx(0.34)
    )

    assert (
        blocker["proximity"]
        == "far"
    )