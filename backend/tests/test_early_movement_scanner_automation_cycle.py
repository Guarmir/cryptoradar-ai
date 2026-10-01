from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_automation_cycle import (
    EarlyMovementScannerAutomationCycle,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
    PushDeliveryOutcome,
)


class FakeScanner:
    def __init__(
        self,
        result: EarlyMovementScannerRunResult,
    ) -> None:
        self.result = result
        self.call_count = 0

    def scan(
        self,
    ) -> EarlyMovementScannerRunResult:
        self.call_count += 1

        return self.result


class FakeAlertDecisionMaker:
    def __init__(
        self,
        decision: EarlyMovementScannerAlertDecision,
    ) -> None:
        self.decision = decision
        self.call_count = 0
        self.received_result = None

    def decide(
        self,
        scan_result: EarlyMovementScannerRunResult,
    ) -> EarlyMovementScannerAlertDecision:
        self.call_count += 1
        self.received_result = scan_result

        return self.decision


class FakePushService:
    def __init__(
        self,
        results=(),
    ) -> None:
        self.results = results
        self.call_count = 0
        self.received_decision = None

    def deliver(
        self,
        decision: EarlyMovementScannerAlertDecision,
    ):
        self.call_count += 1
        self.received_decision = decision

        return self.results

class FakeHistoryService:
    def __init__(
        self,
        records=(),
    ) -> None:
        self.records = records
        self.call_count = 0
        self.received_scan_result = None
        self.received_alert_decision = None

    def record(
        self,
        *,
        scan_result,
        alert_decision,
    ):
        self.call_count += 1

        self.received_scan_result = (
            scan_result
        )

        self.received_alert_decision = (
            alert_decision
        )

        return self.records


def make_scan_result() -> EarlyMovementScannerRunResult:
    return EarlyMovementScannerRunResult(
        universe_size=100,
        candidate_count=20,
        analyzed_count=20,
        successful_analysis_count=8,
        ranked_results=(),
    )


def test_automation_cycle_runs_scanner_and_alert_decision() -> None:
    scan_result = make_scan_result()

    alert_decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )
    )

    scanner = FakeScanner(
        scan_result,
    )

    decision_maker = FakeAlertDecisionMaker(
        alert_decision,
    )

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=scanner,
        alert_decision_maker=decision_maker,
    )

    result = cycle.run()

    assert scanner.call_count == 1
    assert decision_maker.call_count == 1

    assert (
        decision_maker.received_result
        is scan_result
    )

    assert result.scan_result is scan_result

    assert (
        result.alert_decision
        is alert_decision
    )

    assert result.signal_count == 0
    assert result.should_alert is False
    assert result.push_results == ()
    assert result.delivered_push_count == 0

    assert (
        result.finished_at
        >= result.started_at
    )


def test_automation_cycle_delivers_push() -> None:
    scan_result = make_scan_result()

    alert_decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=True,
            results=(),
        )
    )

    push_result = PushDeliveryBatchResult(
        outcomes=(
            PushDeliveryOutcome(
                installation_id="device-1",
                delivered=True,
            ),
        ),
    )

    scanner = FakeScanner(
        scan_result,
    )

    decision_maker = FakeAlertDecisionMaker(
        alert_decision,
    )

    push_service = FakePushService(
        results=(push_result,),
    )

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=scanner,
        alert_decision_maker=decision_maker,
        push_service=push_service,
    )

    result = cycle.run()

    assert push_service.call_count == 1

    assert (
        push_service.received_decision
        is alert_decision
    )

    assert result.push_results == (
        push_result,
    )

    assert (
        result.delivered_push_count
        == 1
    )

def test_automation_cycle_records_history() -> None:
    scan_result = make_scan_result()

    alert_decision = (
        EarlyMovementScannerAlertDecision(
            should_alert=False,
            results=(),
        )
    )

    scanner = FakeScanner(
        scan_result,
    )

    decision_maker = FakeAlertDecisionMaker(
        alert_decision,
    )

    history_record = object()

    history_service = FakeHistoryService(
        records=(
            history_record,
        ),
    )

    cycle = EarlyMovementScannerAutomationCycle(
        scanner=scanner,
        alert_decision_maker=decision_maker,
        history_service=history_service,
    )

    result = cycle.run()

    assert (
        history_service.call_count
        == 1
    )

    assert (
        history_service.received_scan_result
        is scan_result
    )

    assert (
        history_service.received_alert_decision
        is alert_decision
    )

    assert result.history_records == (
        history_record,
    )

    assert (
        result.history_record_count
        == 1
    )