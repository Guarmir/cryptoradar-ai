
from datetime import datetime, timedelta, timezone

from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
    ExtremeMovementCandidateComparator,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


BASE_TIME = datetime(
    2026, 11, 2, 12, 0, tzinfo=timezone.utc
)


def make_asset(
    coin_id,
    price,
    volume,
    change,
):
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id.upper(),
        name=coin_id,
        current_price=price,
        total_volume=volume,
        market_cap=10_000_000,
        price_change_percentage_24h=change,
    )


def test_detects_candidate_between_two_cycles():
    comparator = ExtremeMovementCandidateComparator()

    first = comparator.compare(
        [
            make_asset("coin-a", 1.0, 2_000_000, 20),
            make_asset("coin-b", 1.0, 2_000_000, 1),
        ],
        observed_at=BASE_TIME,
    )

    assert first.current_coin_ids == ("coin-a",)
    assert first.experimental_coin_ids == ()

    second = comparator.compare(
        [
            make_asset("coin-a", 1.0, 2_000_000, 20),
            make_asset("coin-b", 1.05, 2_600_000, 2),
        ],
        observed_at=BASE_TIME + timedelta(minutes=15),
    )

    assert second.current_coin_ids == ("coin-a",)
    assert second.experimental_coin_ids == ("coin-b",)
    assert second.experimental_only_coin_ids == ("coin-b",)

    priority = second.experimental_priorities[0]

    assert priority.coin_id == "coin-b"
    assert priority.direction == "up"
    assert priority.state == "priority"
    assert priority.evidence_count == 3
    assert priority.score == 76.0
