
import pytest

from app.early_movement.scanner.scanner_rotation_bridge import (
    EarlyMovementScannerRotationBridge,
)


class FakeCandidate:
    def __init__(self, coin_id: str) -> None:
        self.coin_id = coin_id


def test_bridge_distributes_candidates():
    bridge = EarlyMovementScannerRotationBridge(
        acquisition_budget=4,
        priority_slots=1,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(8)
    )

    first = bridge.arrange(candidates)
    second = bridge.arrange(candidates)

    assert tuple(
        item.coin_id for item in first[:4]
    ) == (
        "coin-0",
        "coin-1",
        "coin-2",
        "coin-3",
    )

    assert tuple(
        item.coin_id for item in second[:4]
    ) == (
        "coin-0",
        "coin-4",
        "coin-5",
        "coin-6",
    )


def test_bridge_accepts_chart_confirmation():
    bridge = EarlyMovementScannerRotationBridge(
        acquisition_budget=2,
        priority_slots=0,
    )

    candidates = tuple(
        FakeCandidate(f"coin-{index}")
        for index in range(4)
    )

    first = bridge.arrange(candidates)

    bridge.on_chart_result(
        first[0].coin_id,
        True,
    )

    bridge.on_chart_result(
        first[1].coin_id,
        False,
    )

    second = bridge.arrange(candidates)

    assert tuple(
        item.coin_id for item in second[:2]
    ) == (
        "coin-2",
        "coin-3",
    )


def test_bridge_preserves_original_order_on_error():
    bridge = EarlyMovementScannerRotationBridge()

    candidates = (
        FakeCandidate("bitcoin"),
        FakeCandidate("ethereum"),
    )

    def failing_arrange(*args, **kwargs):
        raise RuntimeError("Falha simulada")

    bridge._rotation.arrange = failing_arrange

    assert bridge.arrange(candidates) == candidates


def test_bridge_ignores_confirmation_error():
    bridge = EarlyMovementScannerRotationBridge()

    def failing_confirmation(coin_id):
        raise RuntimeError("Falha simulada")

    bridge._rotation.record_success = (
        failing_confirmation
    )

    bridge.on_chart_result(
        "bitcoin",
        True,
    )


def test_bridge_rejects_invalid_budget():
    with pytest.raises(ValueError):
        EarlyMovementScannerRotationBridge(
            acquisition_budget=0,
        )
