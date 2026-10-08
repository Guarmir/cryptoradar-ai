from app.services.chart_acquisition_service import (
    ChartAcquisitionService,
)
from app.services.chart_request_pacer import (
    ChartRequestPacer,
)


def test_acquisition_fetches_chart():
    calls = []

    def fetcher(
        coin_id,
        days,
    ):
        calls.append(
            (coin_id, days)
        )

        return {
            "prices": [[1, 10.0]],
        }

    service = ChartAcquisitionService(
        chart_fetcher=fetcher,
    )

    result = service.fetch(
        "bitcoin",
        7,
    )

    assert result == {
        "prices": [[1, 10.0]],
    }

    assert calls == [
        ("bitcoin", 7),
    ]


def test_acquisition_waits_before_next_request():
    now = [0.0]
    sleeps = []

    def clock():
        return now[0]

    def sleeper(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    def fetcher(
        coin_id,
        days,
    ):
        return {
            "prices": [],
        }

    pacer = ChartRequestPacer(
        min_interval_seconds=0.2,
        clock=clock,
    )

    service = ChartAcquisitionService(
        chart_fetcher=fetcher,
        pacer=pacer,
        sleeper=sleeper,
    )

    service.fetch(
        "bitcoin",
        7,
    )

    service.fetch(
        "ethereum",
        7,
    )

    assert sleeps
    assert now[0] >= 0.2

def test_acquisition_records_failed_request_attempt():
    now = [0.0]
    fetch_count = 0

    def clock():
        return now[0]

    def fetcher(
        coin_id,
        days,
    ):
        nonlocal fetch_count

        fetch_count += 1

        if fetch_count == 1:
            raise RuntimeError(
                "provider failure"
            )

        return {
            "prices": [],
        }

    pacer = ChartRequestPacer(
        min_interval_seconds=2.0,
        clock=clock,
    )

    service = ChartAcquisitionService(
        chart_fetcher=fetcher,
        pacer=pacer,
        sleeper=lambda seconds: None,
    )

    try:
        service.fetch(
            "bitcoin",
            7,
        )
    except RuntimeError:
        pass

    assert pacer.can_request() is False

def test_acquisition_respects_request_budget():
    fetch_count = 0

    def fetcher(
        coin_id,
        days,
    ):
        nonlocal fetch_count

        fetch_count += 1

        return {
            "prices": [],
        }

    service = ChartAcquisitionService(
        chart_fetcher=fetcher,
        request_budget=2,
    )

    service.fetch(
        "bitcoin",
        7,
    )

    service.fetch(
        "ethereum",
        7,
    )

    result = service.fetch(
        "solana",
        7,
    )

    assert fetch_count == 2

    assert result == {
        "prices": [],
    }

def test_acquisition_budget_can_be_reset():
    fetch_count = 0

    def fetcher(
        coin_id,
        days,
    ):
        nonlocal fetch_count

        fetch_count += 1

        return {
            "prices": [],
        }

    service = ChartAcquisitionService(
        chart_fetcher=fetcher,
        request_budget=1,
    )

    service.fetch(
        "bitcoin",
        7,
    )

    service.fetch(
        "ethereum",
        7,
    )

    assert fetch_count == 1

    service.reset_budget()

    service.fetch(
        "ethereum",
        7,
    )

    assert fetch_count == 2