import pytest

from app.early_movement import (
    EarlyMovementPriceStructureDetector,
)


def _series(
    values: list[float],
) -> list[list[float]]:
    return [
        [
            float(index),
            value,
        ]
        for index, value in enumerate(values)
    ]


def test_detects_resistance_break() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    100.8,
                    101.4,
                    101.8,
                    102.0,
                    101.6,
                    103.0,
                ]
            )
        }
    )

    assert result.current_price == 103.0

    assert result.support_level == pytest.approx(
        100.0,
    )

    assert result.resistance_level == pytest.approx(
        102.0,
    )

    assert result.resistance_break is True
    assert result.support_break is False

    assert (
        result.resistance_break_distance_percent
        is not None
    )

    assert (
        result.resistance_break_distance_percent
        > 0
    )


def test_detects_support_break() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    99.8,
                    99.5,
                    99.7,
                    99.2,
                    99.0,
                    98.8,
                    99.1,
                    97.5,
                ]
            )
        }
    )

    assert result.current_price == 97.5

    assert result.support_level == pytest.approx(
        98.8,
    )

    assert result.resistance_level == pytest.approx(
        100.0,
    )

    assert result.support_break is True
    assert result.resistance_break is False

    assert (
        result.support_break_distance_percent
        is not None
    )

    assert (
        result.support_break_distance_percent
        < 0
    )


def test_does_not_create_breakout_inside_recent_range() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    101.0,
                    100.5,
                    102.0,
                    101.5,
                    100.8,
                    101.2,
                    101.8,
                    101.6,
                ]
            )
        }
    )

    assert result.support_break is False
    assert result.resistance_break is False

    assert (
        result.support_break_distance_percent
        is None
    )

    assert (
        result.resistance_break_distance_percent
        is None
    )


def test_small_price_excess_does_not_count_as_breakout() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.5,
                    102.0,
                    101.6,
                    101.8,
                    101.9,
                    102.1,
                ]
            )
        }
    )

    assert result.resistance_level == pytest.approx(
        102.0,
    )

    assert result.resistance_break is False


def test_insufficient_data_is_safe() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    101.0,
                    102.0,
                ]
            )
        }
    )

    assert result.current_price == 102.0

    assert result.support_level is None
    assert result.resistance_level is None

    assert result.support_break is False
    assert result.resistance_break is False

    assert result.sample_count == 3


def test_invalid_price_samples_are_ignored() -> None:
    detector = (
        EarlyMovementPriceStructureDetector()
    )

    result = detector.detect(
        {
            "prices": [
                [1, 100.0],
                [2, None],
                [3, "invalid"],
                [4, -10.0],
                [5, 101.0],
            ]
        }
    )

    assert result.sample_count == 2
    assert result.current_price == 101.0

    assert result.support_level is None
    assert result.resistance_level is None