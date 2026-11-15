"""Regressoes da serializacao direcional experimental no discovery trace."""

from datetime import datetime, timezone
from types import SimpleNamespace

from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)


NOW = datetime(2026, 11, 14, 18, 0, tzinfo=timezone.utc)


def _result():
    return SimpleNamespace(
        universe_size=3,
        candidate_count=2,
        analyzed_count=1,
        excluded_count=0,
        selected_coin_ids=("bitcoin", "ethereum"),
        submitted_coin_ids=("bitcoin",),
        not_submitted_coin_ids=("ethereum",),
    )


def _priority(coin_id="bitcoin"):
    return SimpleNamespace(
        coin_id=coin_id,
        score=64.0,
        state="priority",
        direction="up",
        evidence_count=2,
    )


def _directional(coin_id="bitcoin"):
    return SimpleNamespace(
        coin_id=coin_id,
        state="opposite_detected",
        direction="down",
        previous_direction="up",
        observation_count=4,
        consecutive_moves=1,
        alternating_moves=1,
        latest_price_change_pct=-0.83,
    )


def _comparison(priorities=(), directional=()):
    return SimpleNamespace(
        experimental_coin_ids=tuple(item.coin_id for item in priorities),
        experimental_only_coin_ids=(),
        common_coin_ids=(),
        experimental_priorities=priorities,
        directional_continuities=directional,
    )


def test_adds_directional_diagnostic_without_changing_priority_fields():
    comparison = _comparison((_priority(),), (_directional(),))
    trace = ExtremeMovementDiscoveryTrace.from_result(
        _result(), observed_at=NOW, experimental_comparison=comparison
    )

    assert trace.experimental_status == "completed"
    assert trace.experimental_priorities == (
        {
            "coin_id": "bitcoin",
            "score": 64.0,
            "state": "priority",
            "direction": "up",
            "evidence_count": 2,
            "directional_continuity": {
                "state": "opposite_detected",
                "direction": "down",
                "previous_direction": "up",
                "observation_count": 4,
                "consecutive_moves": 1,
                "alternating_moves": 1,
                "latest_price_change_pct": -0.83,
            },
        },
    )
    assert trace.selected_coin_ids == ("bitcoin", "ethereum")


def test_non_selected_directional_diagnostic_does_not_become_priority():
    comparison = _comparison(
        (_priority("bitcoin"),), (_directional("ethereum"),)
    )
    trace = ExtremeMovementDiscoveryTrace.from_result(
        _result(), observed_at=NOW, experimental_comparison=comparison
    )
    assert trace.experimental_priorities == (
        {
            "coin_id": "bitcoin",
            "score": 64.0,
            "state": "priority",
            "direction": "up",
            "evidence_count": 2,
        },
    )
    assert comparison.directional_continuities[0].coin_id == "ethereum"


def test_without_directional_results_preserves_legacy_json_shape():
    comparison = _comparison((_priority(),))
    trace = ExtremeMovementDiscoveryTrace.from_result(
        _result(), observed_at=NOW, experimental_comparison=comparison
    )
    assert trace.experimental_priorities[0] == {
        "coin_id": "bitcoin",
        "score": 64.0,
        "state": "priority",
        "direction": "up",
        "evidence_count": 2,
    }


def test_without_comparison_keeps_original_defaults():
    trace = ExtremeMovementDiscoveryTrace.from_result(
        _result(), observed_at=NOW
    )
    assert trace.experimental_status == "not_available"
    assert trace.experimental_priorities == ()
    assert trace.experimental_coin_ids == ()


def test_error_takes_priority_over_completed_comparison():
    trace = ExtremeMovementDiscoveryTrace.from_result(
        _result(),
        observed_at=NOW,
        experimental_comparison=_comparison((_priority(),), (_directional(),)),
        experimental_error=RuntimeError("falha simulada"),
    )
    assert trace.experimental_status == "error"
    assert trace.experimental_priorities == ()


def test_rejects_naive_timestamp():
    try:
        ExtremeMovementDiscoveryTrace.from_result(
            _result(), observed_at=datetime(2026, 11, 14)
        )
    except ValueError as exc:
        assert "fuso horario" in str(exc)
    else:
        raise AssertionError("Deveria rejeitar horario sem timezone")
