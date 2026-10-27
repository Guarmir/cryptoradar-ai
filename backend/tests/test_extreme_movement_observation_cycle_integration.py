from types import SimpleNamespace

from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_automation_cycle import (
    EarlyMovementScannerAutomationCycle,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowResult,
)


def make_entry(relevance=20.0):
    return ExtremeMovementAnalysisEntry(
        coin_id="test-coin",
        symbol="TEST",
        name="Test Coin",
        assessment=ExtremeMovementAssessment(
            state="movement_pressure",
            direction="up",
            relevance_score=relevance,
            supporting_evidence_count=1,
        ),
        maturity=ExtremeMovementMaturity(
            level="early",
            evidence_count=1,
            relevance_score=relevance,
        ),
    )


class FakeScanner:
    def __init__(self):
        self.calls = 0

    def scan(self):
        self.calls += 1

        return EarlyMovementScannerRunResult(
            universe_size=250,
            candidate_count=20,
            analyzed_count=1,
            successful_analysis_count=1,
            ranked_results=(),
            analysis_results=(),
        )


class FakeDecisionMaker:
    def decide(self, scan_result):
        return EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )


class FakeShadowRunner:
    def __init__(self, entry_batches):
        self.entry_batches = iter(entry_batches)

    def run(self, scan_result):
        entries = next(self.entry_batches)

        return ExtremeMovementShadowResult(
            analyzed_count=scan_result.analyzed_count,
            evaluated_count=len(entries),
            extreme_acceleration_count=0,
            movement_pressure_count=len(entries),
            possible_reversal_count=0,
            insufficient_evidence_count=0,
            entries=entries,
        )


def make_cycle(monkeypatch, entry_batches):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=FakeScanner(),
        alert_decision_maker=FakeDecisionMaker(),
    )

    cycle._extreme_shadow_runner = FakeShadowRunner(
        entry_batches
    )

    return cycle


def test_tracks_strengthening_across_cycles(monkeypatch):
    cycle = make_cycle(
        monkeypatch,
        (
            (make_entry(20.0),),
            (make_entry(45.0),),
        ),
    )

    cycle.run()

    first = cycle.last_extreme_observation_cycle

    assert first is not None
    assert first.observations[0].change == "new_observation"

    cycle.run()

    second = cycle.last_extreme_observation_cycle

    assert second is not None
    assert second.observations[0].change == "strengthening"
    assert len(second.active_assets) == 1


def test_preserves_asset_missing_from_next_cycle(monkeypatch):
    cycle = make_cycle(
        monkeypatch,
        (
            (make_entry(),),
            (),
        ),
    )

    cycle.run()
    cycle.run()

    result = cycle.last_extreme_observation_cycle

    assert result is not None
    assert len(result.active_assets) == 1
    assert result.missing_assets[0].missed_cycles == 1


def test_resumes_observation_after_missing_cycle(monkeypatch):
    cycle = make_cycle(
        monkeypatch,
        (
            (make_entry(20.0),),
            (),
            (make_entry(45.0),),
        ),
    )

    cycle.run()
    cycle.run()
    cycle.run()

    result = cycle.last_extreme_observation_cycle

    assert result is not None
    assert result.observations[0].change == "strengthening"
    assert result.active_assets[0].missed_cycles == 0