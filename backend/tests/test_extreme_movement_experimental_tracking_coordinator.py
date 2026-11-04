
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
    ExtremeMovementCandidateComparison,
)
from app.early_movement.extreme_movement.extreme_movement_candidate_priority import (
    ExtremeMovementCandidatePriority,
)
from app.early_movement.extreme_movement.extreme_movement_experimental_tracking import (
    ExtremeMovementExperimentalTrackingEvaluator,
)
from app.early_movement.extreme_movement.extreme_movement_experimental_tracking_coordinator import (
    ExtremeMovementExperimentalTrackingCoordinator,
)


BASE_TIME = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)


def make_asset(coin_id="irys", price=1.0):
    return SimpleNamespace(
        coin_id=coin_id,
        current_price=price,
    )


def make_comparison(
    coin_id="irys",
    *,
    selected=True,
    score=65.0,
    direction="up",
):
    priority = ExtremeMovementCandidatePriority(
        coin_id=coin_id,
        score=score,
        state="priority",
        direction=direction,
        evidence_count=3,
    )

    return ExtremeMovementCandidateComparison(
        current_coin_ids=(),
        experimental_coin_ids=(coin_id,) if selected else (),
        common_coin_ids=(),
        experimental_only_coin_ids=(coin_id,) if selected else (),
        current_only_coin_ids=(),
        experimental_priorities=(priority,) if selected else (),
    )


@pytest.fixture
def store():
    result = MagicMock()
    result.load_active.return_value = ()
    result.save_batch.return_value = (42,)
    return result


@pytest.fixture
def coordinator(store):
    return ExtremeMovementExperimentalTrackingCoordinator(
        store=store,
    )


def test_starts_new_tracking(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    assert coordinator.active_count == 1
    store.load_active.assert_called_once()
    store.save_batch.assert_called_once()

    starts = store.save_batch.call_args.kwargs["starts"]
    updates = store.save_batch.call_args.kwargs["updates"]

    assert len(starts) == 1
    assert updates == ()
    assert starts[0].coin_id == "irys"
    assert starts[0].initial_price == 1.0
    assert starts[0].initial_score == 65.0

    store.save_start.assert_not_called()
    store.save_update.assert_not_called()


def test_updates_existing_tracking(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.05)],
        make_comparison(score=80.0),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    store.save_batch.assert_called_once()

    starts = store.save_batch.call_args.kwargs["starts"]
    updates = store.save_batch.call_args.kwargs["updates"]

    assert starts == ()
    assert len(updates) == 1

    tracking_id, tracking, is_selected = updates[0]

    assert tracking_id == 42
    assert tracking.latest_price == 1.05
    assert tracking.latest_score == 80.0
    assert tracking.price_change_pct == pytest.approx(5.0)
    assert tracking.observation_count == 2
    assert is_selected is True


def test_continues_when_asset_leaves_ranking(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=0.97)],
        make_comparison(selected=False),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    updates = store.save_batch.call_args.kwargs["updates"]

    assert len(updates) == 1
    tracking_id, tracking, is_selected = updates[0]

    assert tracking_id == 42
    assert tracking.latest_price == 0.97
    assert tracking.latest_state == "not_selected"
    assert tracking.latest_direction == "unknown"
    assert is_selected is False
    assert coordinator.active_count == 1


def test_recovers_active_tracking_after_restart(store):
    evaluator = ExtremeMovementExperimentalTrackingEvaluator()

    previous = evaluator.start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )

    store.load_active.return_value = ((42, previous),)
    store.save_batch.return_value = ()

    coordinator = ExtremeMovementExperimentalTrackingCoordinator(
        store=store,
    )

    coordinator.process(
        [make_asset(price=1.04)],
        make_comparison(selected=False),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    assert coordinator.active_count == 1
    store.save_batch.assert_called_once()
    store.save_start.assert_not_called()

    updates = store.save_batch.call_args.kwargs["updates"]
    assert len(updates) == 1

    updated = updates[0][1]

    assert updated.initial_price == 1.0
    assert updated.latest_price == 1.04
    assert updated.observation_count == 2


def test_does_not_duplicate_same_timestamp(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    coordinator.process(
        [make_asset(price=1.05)],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    store.save_batch.assert_called_once()
    assert coordinator.active_count == 1


def test_missing_asset_does_not_invent_price(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    coordinator.process(
        [],
        make_comparison(selected=False),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    store.save_batch.assert_called_once()
    assert coordinator.active_count == 1


def test_invalid_price_does_not_start_tracking(coordinator, store):
    coordinator.process(
        [make_asset(price=0.0)],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    assert coordinator.active_count == 0
    store.save_batch.assert_not_called()


def test_rejects_naive_datetime(coordinator, store):
    with pytest.raises(ValueError, match="fuso"):
        coordinator.process(
            [make_asset()],
            make_comparison(),
            observed_at=datetime(2026, 11, 3, 15, 0),
        )

    store.load_active.assert_not_called()


def test_batch_failure_preserves_existing_state(coordinator, store):
    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    store.save_batch.reset_mock()
    store.save_batch.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        coordinator.process(
            [make_asset(price=1.05)],
            make_comparison(score=80.0),
            observed_at=BASE_TIME + timedelta(minutes=20),
        )

    assert coordinator.active_count == 1

    store.save_batch.side_effect = None
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.05)],
        make_comparison(score=80.0),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    updates = store.save_batch.call_args.kwargs["updates"]
    updated = updates[0][1]

    assert updated.observation_count == 2
    assert updated.initial_price == 1.0
    assert updated.latest_price == 1.05


def test_batch_failure_does_not_register_new_asset(coordinator, store):
    store.save_batch.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        coordinator.process(
            [make_asset()],
            make_comparison(),
            observed_at=BASE_TIME,
        )

    assert coordinator.active_count == 0

    store.save_batch.side_effect = None
    store.save_batch.return_value = (42,)

    coordinator.process(
        [make_asset()],
        make_comparison(),
        observed_at=BASE_TIME,
    )

    assert coordinator.active_count == 1


def test_multiple_assets_use_single_batch(store):
    store.save_batch.return_value = (42, 43)

    coordinator = ExtremeMovementExperimentalTrackingCoordinator(
        store=store,
    )

    first = make_comparison("irys")
    second = make_comparison("bitcoin")

    comparison = ExtremeMovementCandidateComparison(
        current_coin_ids=(),
        experimental_coin_ids=("irys", "bitcoin"),
        common_coin_ids=(),
        experimental_only_coin_ids=("irys", "bitcoin"),
        current_only_coin_ids=(),
        experimental_priorities=(
            *first.experimental_priorities,
            *second.experimental_priorities,
        ),
    )

    coordinator.process(
        [
            make_asset("irys", 1.0),
            make_asset("bitcoin", 70000.0),
        ],
        comparison,
        observed_at=BASE_TIME,
    )

    store.save_batch.assert_called_once()

    starts = store.save_batch.call_args.kwargs["starts"]

    assert len(starts) == 2
    assert {item.coin_id for item in starts} == {
        "irys",
        "bitcoin",
    }
    assert coordinator.active_count == 2


def test_invalid_batch_ids_resets_local_cache(coordinator, store):
    store.save_batch.return_value = ()

    with pytest.raises(RuntimeError, match="IDs no lote"):
        coordinator.process(
            [make_asset()],
            make_comparison(),
            observed_at=BASE_TIME,
        )

    assert coordinator.active_count == 0

    recovered = ExtremeMovementExperimentalTrackingEvaluator().start(
        coin_id="irys",
        observed_at=BASE_TIME,
        price=1.0,
        direction="up",
        score=65.0,
        evidence_count=3,
        state="priority",
    )

    store.load_active.return_value = ((42, recovered),)
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.05)],
        make_comparison(selected=False),
        observed_at=BASE_TIME + timedelta(minutes=20),
    )

    assert store.load_active.call_count == 2
    assert coordinator.active_count == 1


def test_closes_at_exactly_24_hours(coordinator, store):
    coordinator.process([make_asset()], make_comparison(), observed_at=BASE_TIME)
    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.10)],
        make_comparison(),
        observed_at=BASE_TIME + timedelta(hours=24),
    )

    kwargs = store.save_batch.call_args.kwargs
    assert kwargs["starts"] == ()
    assert kwargs["updates"] == ()
    assert len(kwargs["closes"]) == 1
    tracking_id, closed = kwargs["closes"][0]
    assert tracking_id == 42
    assert closed.status == "closed"
    assert closed.close_reason == "observation_window_completed"
    assert closed.closed_at == BASE_TIME + timedelta(hours=24)
    assert closed.latest_price == 1.0
    assert closed.observation_count == 1
    assert coordinator.active_count == 0


def test_closes_without_market_price(coordinator, store):
    coordinator.process([make_asset()], make_comparison(), observed_at=BASE_TIME)
    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [],
        make_comparison(selected=False),
        observed_at=BASE_TIME + timedelta(hours=25),
    )

    kwargs = store.save_batch.call_args.kwargs
    assert kwargs["starts"] == ()
    assert kwargs["updates"] == ()
    assert len(kwargs["closes"]) == 1
    assert kwargs["closes"][0][1].latest_price == 1.0
    assert coordinator.active_count == 0


def test_close_failure_preserves_memory_and_allows_retry(coordinator, store):
    coordinator.process([make_asset()], make_comparison(), observed_at=BASE_TIME)
    store.save_batch.reset_mock()
    store.save_batch.side_effect = RuntimeError("database unavailable")
    deadline = BASE_TIME + timedelta(hours=24)

    with pytest.raises(RuntimeError, match="database unavailable"):
        coordinator.process([make_asset()], make_comparison(), observed_at=deadline)

    assert coordinator.active_count == 1
    store.save_batch.side_effect = None
    store.save_batch.return_value = ()
    coordinator.process([make_asset()], make_comparison(), observed_at=deadline)
    assert len(store.save_batch.call_args.kwargs["closes"]) == 1
    assert coordinator.active_count == 0


def test_does_not_restart_closed_coin_in_same_cycle(coordinator, store):
    coordinator.process([make_asset()], make_comparison(), observed_at=BASE_TIME)
    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.2)],
        make_comparison(selected=True),
        observed_at=BASE_TIME + timedelta(hours=24, minutes=1),
    )

    kwargs = store.save_batch.call_args.kwargs
    assert kwargs["starts"] == ()
    assert len(kwargs["closes"]) == 1
    assert coordinator.active_count == 0


def test_custom_duration_closes_only_at_configured_limit(store):
    coordinator = ExtremeMovementExperimentalTrackingCoordinator(
        store=store, max_tracking_duration=timedelta(hours=2)
    )
    coordinator.process([make_asset()], make_comparison(), observed_at=BASE_TIME)
    store.save_batch.reset_mock()
    store.save_batch.return_value = ()

    coordinator.process(
        [make_asset(price=1.05)],
        make_comparison(),
        observed_at=BASE_TIME + timedelta(hours=1),
    )
    assert len(store.save_batch.call_args.kwargs["updates"]) == 1
    assert store.save_batch.call_args.kwargs["closes"] == ()
    assert coordinator.active_count == 1

    coordinator.process(
        [make_asset(price=1.07)],
        make_comparison(),
        observed_at=BASE_TIME + timedelta(hours=2),
    )
    assert len(store.save_batch.call_args.kwargs["closes"]) == 1
    assert coordinator.active_count == 0
