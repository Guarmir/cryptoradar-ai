
from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)
from app.early_movement.scanner.scanner_automation_cycle import (
    EarlyMovementScannerAutomationCycle,
)


def test_cycle_captures_chart_loader_diagnostics():
    loader = EarlyMovementScannerChartLoader(
        chart_loader=lambda coin_id, days: {
            "prices": [[1, 10.0]],
        },
        cache_loader=lambda coin_id, days: None,
        request_budget=1,
    )

    class FakeScanner:
        def scan(self):
            loader("bitcoin", 7)
            loader("ethereum", 7)
            return "scan_result"

    class FakeDecisionMaker:
        def decide(self, scan_result):
            return "decision"

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=FakeScanner(),
        alert_decision_maker=FakeDecisionMaker(),
        on_cycle_start=loader.reset_budget,
        chart_stats_provider=lambda: loader.stats,
    )

    first_result = cycle.run()

    assert first_result.chart_loader_stats is not None
    assert first_result.chart_loader_stats.cache_hits == 0
    assert first_result.chart_loader_stats.acquisition_attempts == 1
    assert first_result.chart_loader_stats.budget_exhausted == 1
    assert first_result.chart_loader_stats.empty_results == 0

    second_result = cycle.run()

    assert second_result.chart_loader_stats is not None
    assert second_result.chart_loader_stats.acquisition_attempts == 1
    assert second_result.chart_loader_stats.budget_exhausted == 1

    assert first_result.chart_loader_stats.acquisition_attempts == 1
