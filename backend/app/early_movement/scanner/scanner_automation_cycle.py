
from collections.abc import Callable
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
from app.early_movement.scanner.scanner_chart_loader import (
    ScannerChartLoaderStats,
)
from app.early_movement.scanner.scanner_push_service import (
    EarlyMovementScannerPushService,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)
from app.early_movement.scanner.scanner_signal_history_service import (
    EarlyMovementScannerSignalHistoryService,
)
from app.push.push_delivery_models import (
    PushDeliveryBatchResult,
)
from app.early_movement.early_movement_direction_transition import (
    EarlyMovementDirectionTransition,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_config import (
    ExtremeMovementShadowConfig,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowRunner,
    ExtremeMovementShadowResult,
)


@dataclass(frozen=True)
class EarlyMovementScannerAutomationCycleResult:
    started_at: datetime
    finished_at: datetime
    scan_result: EarlyMovementScannerRunResult
    alert_decision: EarlyMovementScannerAlertDecision

    history_records: tuple[
        EarlyMovementScannerSignalHistoryRecord,
        ...,
    ] = ()

    direction_transitions: tuple[
        EarlyMovementDirectionTransition,
        ...,
    ] = ()

    push_results: tuple[
        PushDeliveryBatchResult,
        ...,
    ] = ()

    push_results: tuple[
        PushDeliveryBatchResult,
        ...,
    ] = ()

    chart_loader_stats: Optional[
        ScannerChartLoaderStats
    ] = None

    @property
    def signal_count(self) -> int:
        return self.scan_result.signal_count

    @property
    def should_alert(self) -> bool:
        return self.alert_decision.should_alert

    @property
    def history_record_count(self) -> int:
        return len(self.history_records)

    @property
    def delivered_push_count(self) -> int:
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
        history_service: Optional[
            EarlyMovementScannerSignalHistoryService
        ] = None,
        push_service: Optional[
            EarlyMovementScannerPushService
        ] = None,
        on_cycle_start: Optional[
            Callable[[], None]
        ] = None,
        chart_stats_provider: Optional[
            Callable[[], ScannerChartLoaderStats]
        ] = None,
    ) -> None:
        self._scanner = (
            scanner or EarlyMovementScanner()
        )

        self._alert_decision_maker = (
            alert_decision_maker
            or EarlyMovementScannerAlertDecisionMaker()
        )

        self._history_service = history_service
        self._push_service = push_service
        self._on_cycle_start = on_cycle_start
        self._chart_stats_provider = (
            chart_stats_provider
        )

        self._extreme_shadow_runner = (
            ExtremeMovementShadowRunner()
            if ExtremeMovementShadowConfig.is_enabled()
            else None
        )

        self.last_extreme_shadow_result: Optional[
            ExtremeMovementShadowResult
        ] = None

    def run(
        self,
    ) -> EarlyMovementScannerAutomationCycleResult:
        started_at = datetime.now(timezone.utc)

        if self._on_cycle_start is not None:
            self._on_cycle_start()

        scan_result = self._scanner.scan()

        self.last_extreme_shadow_result = None

        if self._extreme_shadow_runner is not None:
            try:
                self.last_extreme_shadow_result = (
                    self._extreme_shadow_runner.run(
                        scan_result
                    )
                )
            except Exception:
                self.last_extreme_shadow_result = None

        chart_loader_stats = None

        if self._chart_stats_provider is not None:
            chart_loader_stats = (
                self._chart_stats_provider()
            )

        alert_decision = (
            self._alert_decision_maker.decide(
                scan_result,
            )
        )

        
        register_followup = getattr(
            self._scanner,
            "register_followup",
            None,
        )

        if (
            callable(register_followup)
            and isinstance(
                alert_decision,
                EarlyMovementScannerAlertDecision,
            )
            and alert_decision.should_alert
            and alert_decision.results
        ):
            register_followup(
                result.result.candidate.coin_id
                for result in alert_decision.results
            )

        direction_transitions: tuple[
            EarlyMovementDirectionTransition,
            ...,
        ] = ()


        history_records: tuple[
            EarlyMovementScannerSignalHistoryRecord,
            ...,
        ] = ()

        if self._history_service is not None:
            history_records = (
                self._history_service.record(
                    scan_result=scan_result,
                    alert_decision=alert_decision,
                )
            )
            direction_transitions = tuple(
                getattr(
                    self._history_service,
                    "last_transitions",
                    (),
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

        finished_at = datetime.now(timezone.utc)

        return EarlyMovementScannerAutomationCycleResult(
            started_at=started_at,
            finished_at=finished_at,
            scan_result=scan_result,
            alert_decision=alert_decision,
            history_records=history_records,
            push_results=push_results,
            chart_loader_stats=chart_loader_stats,
            direction_transitions=direction_transitions,
        )
