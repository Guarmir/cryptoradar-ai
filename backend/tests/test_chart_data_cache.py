from app.services.chart_data_cache import (
    ChartDataCache,
)


def test_chart_cache_starts_empty():
    cache = ChartDataCache()

    assert (
        cache.get(
            "bitcoin",
            7,
        )
        is None
    )


def test_chart_cache_returns_fresh_data():
    cache = ChartDataCache()

    expected = {
        "prices": [
            [1, 10.0],
        ],
    }

    cache.set(
        "bitcoin",
        7,
        expected,
    )

    assert (
        cache.get(
            "bitcoin",
            7,
        )
        is expected
    )


def test_chart_cache_separates_periods():
    cache = ChartDataCache()

    seven_days = {
        "prices": [[1, 10.0]],
    }

    one_day = {
        "prices": [[1, 11.0]],
    }

    cache.set(
        "bitcoin",
        7,
        seven_days,
    )

    cache.set(
        "bitcoin",
        1,
        one_day,
    )

    assert (
        cache.get(
            "bitcoin",
            7,
        )
        is seven_days
    )

    assert (
        cache.get(
            "bitcoin",
            1,
        )
        is one_day
    )


def test_chart_cache_exposes_stale_data():
    cache = ChartDataCache()

    stale = {
        "prices": [
            [1, 10.0],
        ],
    }

    cache.storage["bitcoin_7"] = {
        "data": stale,
        "timestamp": 0,
    }

    assert (
        cache.get(
            "bitcoin",
            7,
        )
        is None
    )

    assert (
        cache.get_stale(
            "bitcoin",
            7,
        )
        is stale
    )