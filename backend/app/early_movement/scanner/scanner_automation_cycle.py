from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.early_movement.scanner.early_movement_scanner import (
    EarlyMovementScanner,
)
from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
    EarlyMovementScannerAlertDecisionMaker,
)
from app.early_movement.scanner.scanner_push_service import (
    EarlyMovementScannerPushService,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
)


@dataclass(frozen=True)
class EarlyMovementScannerAutomationCycleResult:
    started_at: datetime
    finished_at: datetime
    scan_result: EarlyMovementScannerRunResult
    alert_decision: EarlyMovementScannerAlertDecision
    push_results: tuple[
        PushDeliveryBatchResult,
        ...,
    ] = ()

    @property
    def signal_count(
        self,
    ) -> int:
        return self.scan_result.signal_count

    @property
    def should_alert(
        self,
    ) -> bool:
        return self.alert_decision.should_alert

    @property
    def delivered_push_count(
        self,
    ) -> int:
        return sum(
            result.delivered
            for result in self.push_results
        )


class EarlyMovementScannerAutomationCycle:
    def __init__(
        self,
        *,
        scanner: Optional[
            EarlyMovementScanner
        ] = None,
        alert_decision_maker: Optional[
            EarlyMovementScannerAlertDecisionMaker
        ] = None,
        push_service: Optional[
            EarlyMovementScannerPushService
        ] = None,
    ) -> None:
        self._scanner = (
            scanner
            or EarlyMovementScanner()
        )

        self._alert_decision_maker = (
            alert_decision_maker
            or EarlyMovementScannerAlertDecisionMaker()
        )

        self._push_service = push_service

    def run(
        self,
    ) -> EarlyMovementScannerAutomationCycleResult:
        started_at = datetime.now(
            timezone.utc,
        )

        scan_result = self._scanner.scan()

        alert_decision = (
            self._alert_decision_maker.decide(
                scan_result,
            )
        )

        push_results: tuple[
            PushDeliveryBatchResult,
            ...,
        ] = ()

        if self._push_service is not None:
            push_results = (
                self._push_service.deliver(
                    alert_decision,
                )
            )

        finished_at = datetime.now(
            timezone.utc,
        )

        return (
            EarlyMovementScannerAutomationCycleResult(
                started_at=started_at,
                finished_at=finished_at,
                scan_result=scan_result,
                alert_decision=alert_decision,
                push_results=push_results,
            )
        )