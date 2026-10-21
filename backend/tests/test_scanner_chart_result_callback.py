
import pytest

from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)


def test_callback_reports_success():
    events = []

    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [[1, 100.0]],
        },
        cache_loader=lambda coin_id, days: None,
        on_chart_result=lambda coin_id, success: (
            events.append((coin_id, success))
        ),
    )

    loader("bitcoin", 7)

    assert events == [
        ("bitcoin", True),
    ]


def test_callback_reports_empty_chart():
    events = []

    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [],
        },
        cache_loader=lambda coin_id, days: None,
        on_chart_result=lambda coin_id, success: (
            events.append((coin_id, success))
        ),
    )

    loader("bitcoin", 7)

    assert events == [
        ("bitcoin", False),
    ]

    assert loader.stats.empty_results == 1


def test_callback_reports_loader_exception():
    events = []

    def failing_loader(coin_id, days):
        raise RuntimeError("Falha simulada")

    loader = EarlyMovementScannerChartLoader(
        chart_loader=failing_loader,
        cache_loader=lambda coin_id, days: None,
        on_chart_result=lambda coin_id, success: (
            events.append((coin_id, success))
        ),
    )

    with pytest.raises(RuntimeError):
        loader("bitcoin", 7)

    assert events == [
        ("bitcoin", False),
    ]


def test_callback_reports_cache_success():
    events = []

    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [],
        },
        cache_loader=lambda coin_id, days: {
            "prices": [[1, 100.0]],
        },
        on_chart_result=lambda coin_id, success: (
            events.append((coin_id, success))
        ),
    )

    loader("bitcoin", 7)

    assert events == [
        ("bitcoin", True),
    ]

    assert loader.stats.cache_hits == 1
    assert loader.stats.acquisition_attempts == 0


def test_budget_exhaustion_does_not_notify():
    events = []

    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [[1, 100.0]],
        },
        cache_loader=lambda coin_id, days: None,
        request_budget=1,
        on_chart_result=lambda coin_id, success: (
            events.append((coin_id, success))
        ),
    )

    loader("bitcoin", 7)
    loader("ethereum", 7)

    assert events == [
        ("bitcoin", True),
    ]

    assert loader.stats.acquisition_attempts == 1
    assert loader.stats.budget_exhausted == 1


def test_callback_is_optional():
    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [[1, 100.0]],
        },
        cache_loader=lambda coin_id, days: None,
    )

    result = loader("bitcoin", 7)

    assert result["prices"] == [[1, 100.0]]
