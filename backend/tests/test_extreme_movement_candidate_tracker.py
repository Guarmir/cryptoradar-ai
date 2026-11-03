
from datetime import datetime, timedelta, timezone

import pytest

from app.early_movement.extreme_movement.extreme_movement_candidate_tracker import (
    ExtremeMovementCandidateTracker,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


BASE_TIME = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)


def make_asset(
    coin_id="test-coin",
    price=100.0,
    volume=1_000_000.0,
    change=1.0,
):
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id,
        name=coin_id,
        current_price=price,
        total_volume=volume,
        price_change_percentage_24h=change,
    )


def test_first_observation_is_new():
    tracker = ExtremeMovementCandidateTracker()

    result = tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME,
    )

    assert len(result) == 1
    assert result[0].state == "new"
    assert result[0].observation_count == 1
    assert result[0].price_change_since_previous_pct is None


def test_detects_price_and_volume_evolution():
    tracker = ExtremeMovementCandidateTracker()

    tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME,
    )

    result = tracker.observe(
        [make_asset(price=105, volume=1_200_000, change=3)],
        observed_at=BASE_TIME + timedelta(minutes=15),
    )

    evolution = result[0]

    assert evolution.state == "rising"
    assert evolution.observation_count == 2
    assert evolution.price_change_since_previous_pct == pytest.approx(5)
    assert evolution.volume_change_since_previous_pct == pytest.approx(20)
    assert evolution.change_24h_delta == pytest.approx(2)


def test_detects_falling_price():
    tracker = ExtremeMovementCandidateTracker()

    tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME,
    )

    result = tracker.observe(
        [make_asset(price=95)],
        observed_at=BASE_TIME + timedelta(minutes=15),
    )

    assert result[0].state == "falling"
    assert result[0].price_change_since_previous_pct == pytest.approx(-5)


def test_detects_stable_price():
    tracker = ExtremeMovementCandidateTracker()

    tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME,
    )

    result = tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME + timedelta(minutes=15),
    )

    assert result[0].state == "stable"


def test_limits_observation_history():
    tracker = ExtremeMovementCandidateTracker(
        max_observations_per_asset=3,
    )

    for index in range(5):
        tracker.observe(
            [make_asset(price=100 + index)],
            observed_at=BASE_TIME + timedelta(minutes=index),
        )

    history = tracker.get_history("test-coin")

    assert len(history) == 3
    assert history[0].price == 102
    assert history[-1].price == 104


def test_removes_expired_history():
    tracker = ExtremeMovementCandidateTracker(
        max_age_minutes=30,
    )

    tracker.observe(
        [make_asset()],
        observed_at=BASE_TIME,
    )

    result = tracker.observe(
        [make_asset(price=110)],
        observed_at=BASE_TIME + timedelta(minutes=31),
    )

    assert result[0].state == "new"
    assert result[0].observation_count == 1


def test_rejects_naive_datetime():
    tracker = ExtremeMovementCandidateTracker()

    with pytest.raises(ValueError):
        tracker.observe(
            [make_asset()],
            observed_at=datetime(2026, 11, 2, 12, 0),
        )


def test_ignores_duplicate_asset_ids():
    tracker = ExtremeMovementCandidateTracker()

    result = tracker.observe(
        [
            make_asset(price=100),
            make_asset(price=200),
        ],
        observed_at=BASE_TIME,
    )

    assert len(result) == 1
    assert len(tracker.get_history("test-coin")) == 1


def test_limits_number_of_tracked_assets():
    tracker = ExtremeMovementCandidateTracker(
        max_tracked_assets=2,
    )

    tracker.observe(
        [
            make_asset(coin_id="coin-a"),
            make_asset(coin_id="coin-b"),
            make_asset(coin_id="coin-c"),
        ],
        observed_at=BASE_TIME,
    )

    total = sum(
        bool(tracker.get_history(coin_id))
        for coin_id in ("coin-a", "coin-b", "coin-c")
    )

    assert total == 2
