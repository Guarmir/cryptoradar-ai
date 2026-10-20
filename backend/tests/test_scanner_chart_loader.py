
from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)


def test_loader_uses_cached_chart_without_consuming_budget():
    chart_calls = []

    def cache_loader(coin_id, days):
        if coin_id == "bitcoin":
            return {"prices": [[1, 10.0]]}
        return None

    def chart_loader(coin_id, days):
        chart_calls.append((coin_id, days))
        return {"prices": [[1, 20.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=chart_loader,
        cache_loader=cache_loader,
        request_budget=1,
    )

    cached_result = loader("bitcoin", 7)
    acquired_result = loader("ethereum", 7)
    blocked_result = loader("solana", 7)

    assert cached_result == {"prices": [[1, 10.0]]}
    assert acquired_result == {"prices": [[1, 20.0]]}
    assert blocked_result == {"prices": []}
    assert chart_calls == [("ethereum", 7)]

    assert loader.stats.cache_hits == 1
    assert loader.stats.acquisition_attempts == 1
    assert loader.stats.budget_exhausted == 1
    assert loader.stats.empty_results == 0


def test_loader_budget_can_be_reset():
    chart_calls = []

    def cache_loader(coin_id, days):
        return None

    def chart_loader(coin_id, days):
        chart_calls.append((coin_id, days))
        return {"prices": [[1, 10.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=chart_loader,
        cache_loader=cache_loader,
        request_budget=1,
    )

    loader("bitcoin", 7)
    blocked_result = loader("ethereum", 7)

    assert blocked_result == {"prices": []}
    assert loader.stats.budget_exhausted == 1

    loader.reset_budget()

    assert loader.stats.cache_hits == 0
    assert loader.stats.acquisition_attempts == 0
    assert loader.stats.budget_exhausted == 0
    assert loader.stats.empty_results == 0

    result = loader("ethereum", 7)

    assert result == {"prices": [[1, 10.0]]}
    assert chart_calls == [
        ("bitcoin", 7),
        ("ethereum", 7),
    ]
    assert loader.stats.acquisition_attempts == 1


def test_loader_counts_empty_acquisition_results():
    def cache_loader(coin_id, days):
        return None

    def chart_loader(coin_id, days):
        return {"prices": []}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=chart_loader,
        cache_loader=cache_loader,
        request_budget=2,
    )

    result = loader("cardano", 7)

    assert result == {"prices": []}
    assert loader.stats.acquisition_attempts == 1
    assert loader.stats.empty_results == 1
    assert loader.stats.budget_exhausted == 0


def test_loader_stats_are_immutable_snapshot():
    def cache_loader(coin_id, days):
        return None

    def chart_loader(coin_id, days):
        return {"prices": [[1, 10.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=chart_loader,
        cache_loader=cache_loader,
        request_budget=1,
    )

    before = loader.stats

    loader("bitcoin", 7)

    after = loader.stats

    assert before.acquisition_attempts == 0
    assert after.acquisition_attempts == 1
    assert before.acquisition_attempts == 0
