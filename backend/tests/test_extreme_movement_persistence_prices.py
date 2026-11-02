
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationStore,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_service import (
    ExtremeMovementPersistenceService,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    ExtremeMovementActiveRecord,
)


T0 = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
T1 = T0 + timedelta(minutes=2)
T2 = T1 + timedelta(minutes=2)


def make_entry(price):
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction="down",
            relevance_score=25.0,
            supporting_evidence_count=2,
        ),
        maturity=ExtremeMovementMaturity(
            level="developing",
            evidence_count=2,
            relevance_score=25.0,
        ),
        current_price=price,
    )


def make_service(existing=()):
    memory = ExtremeMovementObservationStore()
    history = MagicMock()
    active = MagicMock()
    active.load_active.return_value = existing
    connection = MagicMock()

    service = ExtremeMovementPersistenceService(
        observation_store=memory,
        history_store=history,
        active_store=active,
        connection_factory=lambda: connection,
    )

    service.restore()
    return service, memory, active


def test_new_discovery_captures_initial_price():
    service, memory, active = make_service()

    cycle = memory.update((make_entry(0.0295),))
    service.persist(cycle, observed_at=T0)

    saved = active.save.call_args.args[0]

    assert saved.discovery_price == 0.0295
    assert saved.discovery_price_at == T0
    assert saved.latest_price == 0.0295
    assert saved.latest_price_at == T0


def test_next_cycle_preserves_discovery_price():
    service, memory, active = make_service()

    first = memory.update((make_entry(0.0295),))
    service.persist(first, observed_at=T0)

    second = memory.update((make_entry(0.0288),))
    service.persist(second, observed_at=T1)

    saved = active.save.call_args.args[0]

    assert saved.discovery_price == 0.0295
    assert saved.discovery_price_at == T0
    assert saved.latest_price == 0.0288
    assert saved.latest_price_at == T1


def test_missing_cycle_does_not_change_prices():
    service, memory, active = make_service()

    first = memory.update((make_entry(0.0295),))
    service.persist(first, observed_at=T0)

    missing = memory.update(())
    service.persist(missing, observed_at=T1)

    saved = active.save.call_args.args[0]

    assert saved.observation_status == "awaiting_update"
    assert saved.discovery_price == 0.0295
    assert saved.latest_price == 0.0295
    assert saved.latest_price_at == T0


def test_restart_preserves_discovery_price():
    previous = ExtremeMovementActiveRecord(
        entry=make_entry(0.0295),
        missed_cycles=0,
        first_observed_at=T0,
        last_observed_at=T0,
        discovery_price=0.0295,
        discovery_price_at=T0,
        latest_price=0.0295,
        latest_price_at=T0,
    )

    service, memory, active = make_service((previous,))

    cycle = memory.update((make_entry(0.0275),))
    service.persist(cycle, observed_at=T1)

    saved = active.save.call_args.args[0]

    assert saved.discovery_price == 0.0295
    assert saved.discovery_price_at == T0
    assert saved.latest_price == 0.0275
    assert saved.latest_price_at == T1


def test_legacy_asset_keeps_discovery_unavailable():
    previous = ExtremeMovementActiveRecord(
        entry=make_entry(None),
        missed_cycles=0,
        first_observed_at=T0,
        last_observed_at=T0,
    )

    service, memory, active = make_service((previous,))

    cycle = memory.update((make_entry(0.0288),))
    service.persist(cycle, observed_at=T1)

    saved = active.save.call_args.args[0]

    assert saved.discovery_price is None
    assert saved.discovery_price_at is None
    assert saved.latest_price == 0.0288
    assert saved.latest_price_at == T1
