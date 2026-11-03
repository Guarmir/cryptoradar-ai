
from datetime import datetime, timezone

import pytest

from app.early_movement.extreme_movement.extreme_movement_discovery_runner import (
    ExtremeMovementDiscoveryResult,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)


def make_result():
    return ExtremeMovementDiscoveryResult(
        universe_size=4,
        candidate_count=2,
        analyzed_count=1,
        analysis_results=(),
        selected_coin_ids=("coin-b", "coin-c"),
        submitted_coin_ids=("coin-b",),
        not_submitted_coin_ids=("coin-c",),
        excluded_count=1,
    )


def test_creates_trace_from_discovery_result():
    timestamp = datetime(
        2026, 11, 2, 12, 0, tzinfo=timezone.utc
    )

    trace = ExtremeMovementDiscoveryTrace.from_result(
        make_result(),
        observed_at=timestamp,
    )

    assert trace.observed_at == timestamp
    assert trace.universe_size == 4
    assert trace.candidate_count == 2
    assert trace.analyzed_count == 1
    assert trace.excluded_count == 1
    assert trace.selected_coin_ids == ("coin-b", "coin-c")
    assert trace.submitted_coin_ids == ("coin-b",)
    assert trace.not_submitted_coin_ids == ("coin-c",)


def test_rejects_timestamp_without_timezone():
    timestamp = datetime(2026, 11, 2, 12, 0)

    with pytest.raises(ValueError):
        ExtremeMovementDiscoveryTrace.from_result(
            make_result(),
            observed_at=timestamp,
        )

        
def test_trace_preserves_experimental_comparison():
    from types import SimpleNamespace

    comparison = SimpleNamespace(
        experimental_coin_ids=("coin-a", "coin-b"),
        experimental_only_coin_ids=("coin-b",),
        common_coin_ids=("coin-a",),
        experimental_priorities=(
            SimpleNamespace(
                coin_id="coin-b",
                score=76.0,
                state="priority",
                direction="up",
                evidence_count=3,
            ),
        ),
    )

    result = SimpleNamespace(
        universe_size=500,
        candidate_count=20,
        analyzed_count=2,
        excluded_count=10,
        selected_coin_ids=("coin-a",),
        submitted_coin_ids=("coin-a",),
        not_submitted_coin_ids=(),
    )

    trace = ExtremeMovementDiscoveryTrace.from_result(
        result,
        experimental_comparison=comparison,
    )

    assert trace.experimental_status == "completed"
    assert trace.experimental_coin_ids == (
        "coin-a",
        "coin-b",
    )
    assert trace.experimental_only_coin_ids == ("coin-b",)
    assert trace.common_coin_ids == ("coin-a",)
    assert trace.experimental_priorities == (
        {
            "coin_id": "coin-b",
            "score": 76.0,
            "state": "priority",
            "direction": "up",
            "evidence_count": 3,
        },
    )

