
import pytest

from app.early_movement.early_movement_metric_extractor import (
    EarlyMovementMetricExtractor,
)


@pytest.mark.parametrize(
    ("prices", "expected"),
    [
        ([100, 100, 100, 100, 104], 4.0),
        ([100, 100, 100, 100, 96], -4.0),
        ([100, 100, 100, 100], 0.0),
    ],
)
def test_recent_price_return(prices, expected):
    extractor = EarlyMovementMetricExtractor()

    result = extractor._recent_price_return(prices)

    assert result == pytest.approx(expected)


def test_recent_price_return_insufficient_data():
    extractor = EarlyMovementMetricExtractor()

    assert extractor._recent_price_return([100, 101, 102]) is None


def test_extract_exposes_recent_price_return():
    extractor = EarlyMovementMetricExtractor()

    chart_data = {
        "prices": [
            [index, price]
            for index, price in enumerate(
                [100, 100, 100, 100, 104]
            )
        ],
        "total_volumes": [],
    }

    metrics = extractor.extract(chart_data)

    assert metrics.recent_price_return == pytest.approx(4.0)
