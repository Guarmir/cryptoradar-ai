
import pytest

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
    ExtremeMovementTrackedAsset,
)


def make_entry(
    *,
    coin_id="test-coin",
    relevance=20.0,
):
    return ExtremeMovementAnalysisEntry(
        coin_id=coin_id,
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction="up",
            relevance_score=relevance,
            supporting_evidence_count=1,
        ),
        maturity=ExtremeMovementMaturity(
            level="early",
            evidence_count=1,
            relevance_score=relevance,
        ),
    )


def make_asset(
    *,
    coin_id="test-coin",
    relevance=20.0,
    missed_cycles=0,
):
    return ExtremeMovementTrackedAsset(
        coin_id=coin_id,
        last_entry=make_entry(
            coin_id=coin_id,
            relevance=relevance,
        ),
        missed_cycles=missed_cycles,
    )


def test_restore_preserves_previous_assessment():
    store = ExtremeMovementObservationStore()

    store.restore((make_asset(relevance=20.0),))

    result = store.update(
        (make_entry(relevance=40.0),)
    )

    assert result.observations[0].change == "strengthening"
    assert result.observations[0].previous is not None
    assert (
        result.observations[0]
        .previous.assessment.relevance_score
        == 20.0
    )


def test_restore_preserves_missed_cycles():
    store = ExtremeMovementObservationStore()

    store.restore(
        (make_asset(missed_cycles=3),)
    )

    result = store.update(())

    assert result.missing_assets[0].missed_cycles == 4


def test_restore_resets_missed_cycles_when_asset_returns():
    store = ExtremeMovementObservationStore()

    store.restore(
        (make_asset(missed_cycles=3),)
    )

    result = store.update((make_entry(),))

    assert result.active_assets[0].missed_cycles == 0


def test_restore_replaces_existing_memory():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(),))
    store.restore(())

    result = store.update(())

    assert result.active_assets == ()


def test_restore_rejects_negative_missed_cycles():
    store = ExtremeMovementObservationStore()

    with pytest.raises(ValueError):
        store.restore(
            (make_asset(missed_cycles=-1),)
        )


def test_restore_rejects_duplicate_assets():
    store = ExtremeMovementObservationStore()
    asset = make_asset()

    with pytest.raises(ValueError):
        store.restore((asset, asset))


def test_restore_rejects_mismatched_coin_id():
    store = ExtremeMovementObservationStore()

    asset = ExtremeMovementTrackedAsset(
        coin_id="different-coin",
        last_entry=make_entry(),
    )

    with pytest.raises(ValueError):
        store.restore((asset,))


def test_failed_restore_preserves_existing_memory():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(relevance=20.0),))

    with pytest.raises(ValueError):
        store.restore(
            (make_asset(missed_cycles=-1),)
        )

    result = store.update(
        (make_entry(relevance=40.0),)
    )

    assert result.observations[0].change == "strengthening"
