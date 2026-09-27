from app.early_movement import (
    EarlyMovementBreakoutConfirmationDetector,
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


def test_confirms_upward_breakout_retest() -> None:
    detector = (
        EarlyMovementBreakoutConfirmationDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.2,
                    101.5,
                    102.0,
                    103.0,
                    102.2,
                    103.4,
                ]
            )
        }
    )

    assert result.retest_confirmed is True
    assert result.breakout_direction == "up"
    assert result.breakout_level == 102.0
    assert result.breakout_price == 103.0
    assert result.retest_price == 102.2
    assert result.holding_breakout_level is True


def test_confirms_downward_breakout_retest() -> None:
    detector = (
        EarlyMovementBreakoutConfirmationDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    99.8,
                    99.5,
                    99.2,
                    99.0,
                    98.8,
                    97.8,
                    98.6,
                    97.2,
                ]
            )
        }
    )

    assert result.retest_confirmed is True
    assert result.breakout_direction == "down"
    assert result.breakout_level == 98.8
    assert result.breakout_price == 97.8
    assert result.retest_price == 98.6
    assert result.holding_breakout_level is True


def test_breakout_without_retest_is_not_confirmed() -> None:
    detector = (
        EarlyMovementBreakoutConfirmationDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.2,
                    101.5,
                    102.0,
                    103.0,
                    103.5,
                    104.0,
                ]
            )
        }
    )

    assert result.retest_confirmed is False


def test_failed_retest_is_not_confirmed() -> None:
    detector = (
        EarlyMovementBreakoutConfirmationDetector()
    )

    result = detector.detect(
        {
            "prices": _series(
                [
                    100.0,
                    100.5,
                    101.0,
                    101.2,
                    101.5,
                    102.0,
                    103.0,
                    102.1,
                    101.0,
                ]
            )
        }
    )

    assert result.retest_confirmed is False


def test_insufficient_data_is_safe() -> None:
    detector = (
        EarlyMovementBreakoutConfirmationDetector()
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

    assert result.retest_confirmed is False
    assert result.breakout_direction is None
    assert result.sample_count == 3