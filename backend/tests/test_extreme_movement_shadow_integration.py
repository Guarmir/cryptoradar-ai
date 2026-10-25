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
from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowResult,
)


class FakeScanner:
    def __init__(self):
        self.calls = 0
        self.result = EarlyMovementScannerRunResult(
            universe_size=250,
            candidate_count=20,
            analyzed_count=4,
            successful_analysis_count=0,
            ranked_results=(),
            analysis_results=(),
        )

    def scan(self):
        self.calls += 1
        return self.result


class FakeDecisionMaker:
    def __init__(self):
        self.calls = 0

    def decide(self, scan_result):
        self.calls += 1
        return EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )


class FakeShadowRunner:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.calls = 0
        self.received_result = None

    def run(self, scan_result):
        self.calls += 1
        self.received_result = scan_result

        if self.fail:
            raise RuntimeError("Simulated shadow failure")

        return ExtremeMovementShadowResult(
            analyzed_count=scan_result.analyzed_count,
            evaluated_count=0,
            extreme_acceleration_count=0,
            movement_pressure_count=0,
            possible_reversal_count=0,
            insufficient_evidence_count=0,
        )


class FakeHistoryService:
    def __init__(self):
        self.calls = 0

    def record(self, *, scan_result, alert_decision):
        self.calls += 1
        return ()


class FakePushService:
    def __init__(self):
        self.calls = 0

    def deliver(self, alert_decision):
        self.calls += 1
        return ()


def make_cycle():
    scanner = FakeScanner()
    decision_maker = FakeDecisionMaker()
    history_service = FakeHistoryService()
    push_service = FakePushService()

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=scanner,
        alert_decision_maker=decision_maker,
        history_service=history_service,
        push_service=push_service,
    )

    return (
        cycle,
        scanner,
        decision_maker,
        history_service,
        push_service,
    )


def test_shadow_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        raising=False,
    )

    cycle, scanner, decision, history, push = make_cycle()

    result = cycle.run()

    assert cycle.last_extreme_shadow_result is None
    assert scanner.calls == 1
    assert decision.calls == 1
    assert history.calls == 1
    assert push.calls == 1
    assert result.should_alert is False


def test_shadow_enabled_runs_without_affecting_cycle(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )

    cycle, scanner, decision, history, push = make_cycle()

    shadow_runner = FakeShadowRunner()
    cycle._extreme_shadow_runner = shadow_runner

    result = cycle.run()

    assert shadow_runner.calls == 1
    assert shadow_runner.received_result is scanner.result

    assert cycle.last_extreme_shadow_result is not None
    assert (
        cycle.last_extreme_shadow_result.analyzed_count
        == 4
    )

    assert scanner.calls == 1
    assert decision.calls == 1
    assert history.calls == 1
    assert push.calls == 1
    assert result.should_alert is False


def test_shadow_failure_does_not_interrupt_cycle(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )

    cycle, scanner, decision, history, push = make_cycle()

    shadow_runner = FakeShadowRunner(fail=True)
    cycle._extreme_shadow_runner = shadow_runner

    result = cycle.run()

    assert shadow_runner.calls == 1
    assert cycle.last_extreme_shadow_result is None

    assert scanner.calls == 1
    assert decision.calls == 1
    assert history.calls == 1
    assert push.calls == 1
    assert result.should_alert is False

def test_shadow_enabled_preserves_positive_push(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )

    cycle, scanner, decision, history, push = make_cycle()

    shadow_runner = FakeShadowRunner()
    cycle._extreme_shadow_runner = shadow_runner

    from app.early_movement.scanner.scanner_alert_decision import (
        EarlyMovementScannerAlertDecision,
    )

    decision.decide = lambda scan_result: (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(),
        )
    )

    result = cycle.run()

    assert result.should_alert is True
    assert push.calls == 1
    assert history.calls == 1
    assert shadow_runner.calls == 1
    assert cycle.last_extreme_shadow_result is not None

def test_shadow_logger_failure_does_not_interrupt_cycle(monkeypatch):
    monkeypatch.setenv(
        "EXTREME_MOVEMENT_SHADOW_ENABLED",
        "true",
    )

    cycle, scanner, decision, history, push = make_cycle()

    shadow_runner = FakeShadowRunner()
    cycle._extreme_shadow_runner = shadow_runner

    class FailingLogger:
        def log(self, result):
            raise RuntimeError("Simulated logging failure")

    cycle._extreme_shadow_logger = FailingLogger()

    result = cycle.run()

    assert shadow_runner.calls == 1
    assert cycle.last_extreme_shadow_result is not None

    assert scanner.calls == 1
    assert decision.calls == 1
    assert history.calls == 1
    assert push.calls == 1
    assert result.should_alert is False