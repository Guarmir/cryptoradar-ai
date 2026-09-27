import pytest

from app.early_movement import EarlyMovementMetricExtractor


def _series(values: list[float]) -> list[list[float]]:
    return [
        [
            float(index),
            value,
        ]
        for index, value in enumerate(values)
    ]


def test_extracts_real_market_chart_metrics() -> None:
    extractor = EarlyMovementMetricExtractor()

    result = extractor.extract(
        {
            "prices": _series(
                [
                    100.0,
                    100.2,
                    100.4,
                    100.6,
                    100.8,
                    101.0,
                    101.2,
                    102.5,
                    104.0,
                    106.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    100.0,
                    110.0,
                    90.0,
                    100.0,
                    100.0,
                    180.0,
                    220.0,
                    200.0,
                ]
            ),
        }
    )

    assert result.price_sample_count == 10
    assert result.volume_sample_count == 9

    assert result.price_acceleration is not None
    assert result.price_acceleration > 4.0

    assert result.abnormal_volume_ratio == pytest.approx(
        2.0,
    )

    assert result.volatility_expansion is not None
    assert result.volatility_expansion > 5.0

    assert result.persistence_score == pytest.approx(
        100.0,
    )


def test_preserves_downward_acceleration_direction() -> None:
    extractor = EarlyMovementMetricExtractor()

    result = extractor.extract(
        {
            "prices": _series(
                [
                    100.0,
                    99.9,
                    99.8,
                    99.7,
                    99.6,
                    99.5,
                    99.4,
                    98.0,
                    96.0,
                    93.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    100.0,
                    150.0,
                    170.0,
                    190.0,
                ]
            ),
        }
    )

    assert result.price_acceleration is not None
    assert result.price_acceleration < 0

    assert result.persistence_score == pytest.approx(
        100.0,
    )


def test_insufficient_data_does_not_create_fake_metrics() -> None:
    extractor = EarlyMovementMetricExtractor()

    result = extractor.extract(
        {
            "prices": _series(
                [
                    100.0,
                    101.0,
                    102.0,
                ]
            ),
            "total_volumes": _series(
                [
                    100.0,
                    120.0,
                ]
            ),
        }
    )

    assert result.price_acceleration is None
    assert result.abnormal_volume_ratio is None
    assert result.volatility_expansion is None
    assert result.persistence_score is None

    assert result.price_sample_count == 3
    assert result.volume_sample_count == 2


def test_ignores_invalid_market_chart_samples() -> None:
    extractor = EarlyMovementMetricExtractor()

    result = extractor.extract(
        {
            "prices": [
                [1, 100.0],
                [2, None],
                [3, "invalid"],
                [4, -1.0],
                [5, 101.0],
            ],
            "total_volumes": [
                [1, 1000.0],
                [2, None],
                [3, -10.0],
                [4, 1200.0],
            ],
        }
    )

    assert result.price_sample_count == 2
    assert result.volume_sample_count == 2

    assert result.price_acceleration is None
    assert result.abnormal_volume_ratio is None