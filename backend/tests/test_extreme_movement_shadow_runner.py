from types import SimpleNamespace

from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowRunner,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)


def make_scan_result(
    analysis_results=(),
    analyzed_count=0,
):
    return EarlyMovementScannerRunResult(
        universe_size=250,
        candidate_count=20,
        analyzed_count=analyzed_count,
        successful_analysis_count=0,
        ranked_results=(),
        analysis_results=analysis_results,
    )


def make_entry(state):
    return SimpleNamespace(
        assessment=SimpleNamespace(state=state)
    )


class FakeAdapter:
    def __init__(self, entries):
        self.entries = entries
        self.received_results = None

    def adapt(self, results):
        self.received_results = results
        return self.entries


def test_empty_scan_result():
    result = ExtremeMovementShadowRunner().run(
        make_scan_result()
    )

    assert result.analyzed_count == 0
    assert result.evaluated_count == 0
    assert result.entries == ()


def test_counts_detected_states():
    entries = (
        make_entry("extreme_acceleration"),
        make_entry("movement_pressure"),
        make_entry("possible_reversal"),
        make_entry("insufficient_evidence"),
        make_entry("extreme_acceleration"),
    )

    adapter = FakeAdapter(entries)

    result = ExtremeMovementShadowRunner(
        adapter=adapter
    ).run(
        make_scan_result(
            analyzed_count=8,
        )
    )

    assert result.analyzed_count == 8
    assert result.evaluated_count == 5
    assert result.extreme_acceleration_count == 2
    assert result.movement_pressure_count == 1
    assert result.possible_reversal_count == 1
    assert result.insufficient_evidence_count == 1


def test_passes_existing_analysis_results():
    existing_results = (
        object(),
        object(),
    )

    adapter = FakeAdapter(())

    ExtremeMovementShadowRunner(
        adapter=adapter
    ).run(
        make_scan_result(
            analysis_results=existing_results,
            analyzed_count=2,
        )
    )

    assert adapter.received_results is existing_results


def test_does_not_modify_original_scan_result():
    scan_result = make_scan_result(
        analyzed_count=3,
    )

    adapter = FakeAdapter(())

    ExtremeMovementShadowRunner(
        adapter=adapter
    ).run(scan_result)

    assert scan_result.analyzed_count == 3
    assert scan_result.analysis_results == ()
    assert scan_result.ranked_results == ()