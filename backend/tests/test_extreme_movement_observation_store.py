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


def make_entry(relevance=20.0):
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
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


def test_registers_new_observation():
    store = ExtremeMovementObservationStore()

    result = store.update((make_entry(),))

    assert len(result.active_assets) == 1
    assert result.observations[0].change == "new_observation"


def test_tracks_strengthening():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(20.0),))
    result = store.update((make_entry(40.0),))

    assert result.observations[0].change == "strengthening"


def test_preserves_missing_asset():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(),))
    result = store.update(())

    assert len(result.active_assets) == 1
    assert len(result.missing_assets) == 1
    assert result.missing_assets[0].missed_cycles == 1


def test_counts_multiple_missing_cycles():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(),))
    store.update(())
    result = store.update(())

    assert result.missing_assets[0].missed_cycles == 2


def test_resumes_tracking_when_asset_returns():
    store = ExtremeMovementObservationStore()

    store.update((make_entry(20.0),))
    store.update(())

    result = store.update((make_entry(40.0),))

    assert result.observations[0].change == "strengthening"
    assert result.active_assets[0].missed_cycles == 0


def test_empty_store_remains_empty():
    store = ExtremeMovementObservationStore()

    result = store.update(())

    assert result.active_assets == ()
    assert result.missing_assets == ()
    assert result.observations == ()