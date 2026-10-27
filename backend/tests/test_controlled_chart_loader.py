from app.services.chart_request_pacer import (
    ChartRequestPacer,
)
from app.services.controlled_chart_loader import (
    ControlledChartLoader,
)


def test_controlled_loader_loads_chart() -> None:
    calls = []

    expected = {
        "prices": [
            [1, 10.0],
        ],
    }

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        calls.append(
            (
                coin_id,
                days,
            )
        )

        return expected

    loader = ControlledChartLoader(
        chart_loader=fake_loader,
    )

    result = loader(
        "bitcoin",
        7,
    )

    assert result is expected

    assert calls == [
        (
            "bitcoin",
            7,
        )
    ]


def test_controlled_loader_waits_before_follow_up_request() -> None:
    now = [100.0]
    waits = []
    calls = []

    pacer = ChartRequestPacer(
        min_interval_seconds=1.0,
        clock=lambda: now[0],
    )

    def fake_sleep(
        seconds: float,
    ) -> None:
        waits.append(
            seconds,
        )
        now[0] += seconds

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        calls.append(
            (
                coin_id,
                days,
                now[0],
            )
        )

        return {
            "prices": [
                [1, 10.0],
            ],
        }

    loader = ControlledChartLoader(
        chart_loader=fake_loader,
        pacer=pacer,
        sleeper=fake_sleep,
    )

    loader(
        "bitcoin",
        7,
    )

    loader(
        "ethereum",
        7,
    )

    assert calls[0] == (
        "bitcoin",
        7,
        100.0,
    )

    assert calls[1][0:2] == (
        "ethereum",
        7,
    )

    assert (
        calls[1][2]
        >= 101.0
    )

    assert waits


def test_controlled_loader_records_request_after_loading() -> None:
    now = [100.0]

    pacer = ChartRequestPacer(
        min_interval_seconds=2.0,
        clock=lambda: now[0],
    )

    loader = ControlledChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [
                [1, 10.0],
            ],
        },
        pacer=pacer,
        sleeper=lambda seconds: None,
    )

    assert pacer.can_request() is True

    loader(
        "solana",
        7,
    )

    assert pacer.can_request() is False

def test_controlled_loader_does_not_wait_for_cached_chart() -> None:
    waits = []
    calls = []

    pacer = ChartRequestPacer(
        min_interval_seconds=2.0,
        clock=lambda: 100.0,
    )

    pacer.record_request()

    cached_chart = {
        "prices": [
            [1, 10.0],
        ],
    }

    def fake_cache_loader(
        coin_id: str,
        days: int,
    ):
        return cached_chart

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        calls.append(
            (
                coin_id,
                days,
            )
        )

        return {
            "prices": [],
        }

    loader = ControlledChartLoader(
        chart_loader=fake_loader,
        pacer=pacer,
        sleeper=lambda seconds: waits.append(
            seconds,
        ),
        cache_loader=fake_cache_loader,
    )

    result = loader(
        "bitcoin",
        7,
    )

    assert result is cached_chart
    assert waits == []
    assert calls == []