import pytest

from app.early_movement.extreme_movement.extreme_movement_candidate_selector import (
    ExtremeMovementCandidateSelector,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


def make_asset(
    coin_id: str,
    change: float,
    volume: float = 1_000_000.0,
) -> EarlyMovementScannerMarketAsset:
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id,
        name=coin_id,
        current_price=1.0,
        total_volume=volume,
        market_cap=10_000_000.0,
        price_change_percentage_24h=change,
    )


def test_selects_extreme_positive_movement():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select([
        make_asset("irys", 400.0),
        make_asset("normal", 3.0),
    ])

    assert len(result) == 1
    assert result[0].coin_id == "irys"
    assert result[0].direction == "up"
    assert result[0].activity_score == 400.0


def test_selects_extreme_negative_movement():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select([
        make_asset("irys", -80.0),
    ])

    assert len(result) == 1
    assert result[0].direction == "down"
    assert result[0].absolute_change_24h == 80.0


def test_prioritizes_stronger_movement():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select([
        make_asset("coin-a", 12.0),
        make_asset("coin-b", -85.0),
        make_asset("coin-c", 250.0),
    ])

    assert [item.coin_id for item in result] == [
        "coin-c",
        "coin-b",
        "coin-a",
    ]


def test_rejects_insufficient_volume():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select([
        make_asset("low-volume", 400.0, 1_000.0),
    ])

    assert result == ()


def test_respects_result_limit():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select(
        [
            make_asset("a", 100.0),
            make_asset("b", 80.0),
            make_asset("c", 60.0),
        ],
        limit=2,
    )

    assert len(result) == 2
    assert [item.coin_id for item in result] == [
        "a",
        "b",
    ]


def test_rejects_duplicate_assets():
    selector = ExtremeMovementCandidateSelector()

    result = selector.select([
        make_asset("irys", 400.0),
        make_asset("irys", 400.0),
    ])

    assert len(result) == 1


def test_rejects_invalid_limit():
    selector = ExtremeMovementCandidateSelector()

    with pytest.raises(ValueError):
        selector.select([], limit=0)