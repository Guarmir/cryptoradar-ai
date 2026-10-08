import pytest

from app.services.chart_request_pacer import (
    ChartRequestPacer,
)


def test_pacer_allows_first_request():
    pacer = ChartRequestPacer()

    assert pacer.can_request() is True


def test_pacer_blocks_immediate_follow_up():
    pacer = ChartRequestPacer()

    pacer.record_request()

    assert pacer.can_request() is False


def test_pacer_allows_request_after_interval():
    now = [100.0]

    pacer = ChartRequestPacer(
        min_interval_seconds=2.0,
        clock=lambda: now[0],
    )

    pacer.record_request()

    now[0] = 101.9

    assert pacer.can_request() is False

    now[0] = 102.0

    assert pacer.can_request() is True


def test_pacer_reset_allows_request_again():
    pacer = ChartRequestPacer()

    pacer.record_request()

    assert pacer.can_request() is False

    pacer.reset()

    assert pacer.can_request() is True


def test_pacer_rejects_invalid_interval():
    with pytest.raises(
        ValueError,
        match="intervalo mínimo",
    ):
        ChartRequestPacer(
            min_interval_seconds=0,
        )