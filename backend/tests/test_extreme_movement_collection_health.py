
import pytest

from app.early_movement.extreme_movement.extreme_movement_collection_health import (
    ExtremeMovementCollectionHealth,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


def make_result(
    *,
    universe_size=100,
    candidate_count=20,
    analyzed_count=20,
    successful_analysis_count=15,
):
    return EarlyMovementScannerRunResult(
        universe_size=universe_size,
        candidate_count=candidate_count,
        analyzed_count=analyzed_count,
        successful_analysis_count=successful_analysis_count,
        ranked_results=(),
        analysis_results=(),
    )


def test_healthy_collection():
    result = make_result()

    assert ExtremeMovementCollectionHealth.is_healthy(
        result
    ) is True


def test_minimum_healthy_collection():
    result = make_result(
        universe_size=1,
        candidate_count=1,
        analyzed_count=1,
        successful_analysis_count=1,
    )

    assert ExtremeMovementCollectionHealth.is_healthy(
        result
    ) is True


@pytest.mark.parametrize(
    "field",
    [
        "universe_size",
        "candidate_count",
        "analyzed_count",
        "successful_analysis_count",
    ],
)
def test_zero_value_marks_collection_unhealthy(field):
    values = {
        "universe_size": 100,
        "candidate_count": 20,
        "analyzed_count": 20,
        "successful_analysis_count": 15,
    }

    values[field] = 0

    result = make_result(**values)

    assert ExtremeMovementCollectionHealth.is_healthy(
        result
    ) is False


def test_ranked_results_not_required():
    result = make_result()

    assert result.ranked_results == ()
    assert ExtremeMovementCollectionHealth.is_healthy(
        result
    ) is True
