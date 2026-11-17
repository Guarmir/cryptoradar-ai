
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from app.early_movement.extreme_movement.extreme_movement_discovery_schedule import (
    ExtremeMovementDiscoverySchedule,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_runner import (
    ExtremeMovementDiscoveryRunner,
    ExtremeMovementDiscoveryResult,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowRunner,
    ExtremeMovementShadowResult,
)


@dataclass(frozen=True)
class ExtremeMovementDiscoveryBridgeResult:
    discovery: ExtremeMovementDiscoveryResult
    shadow: ExtremeMovementShadowResult


class ExtremeMovementDiscoveryBridge:
    def __init__(
        self,
        *,
        discovery_runner: ExtremeMovementDiscoveryRunner,
        shadow_runner: Optional[ExtremeMovementShadowRunner] = None,
        schedule: Optional[ExtremeMovementDiscoverySchedule] = None,
        trace_store: Optional[Any] = None,
        directional_history_store: Optional[Any] = None,
    ) -> None:
        self._discovery_runner = discovery_runner

        self._shadow_runner = (
            shadow_runner
            if shadow_runner is not None
            else ExtremeMovementShadowRunner()
        )

        self._schedule = (
            schedule
            if schedule is not None
            else ExtremeMovementDiscoverySchedule()
        )

        self._trace_store = trace_store
        self._directional_history_store = directional_history_store

        self.last_result: Optional[
            ExtremeMovementDiscoveryBridgeResult
        ] = None

        self.last_error: Optional[Exception] = None
        self.last_trace_error: Optional[Exception] = None
        self.last_directional_history_error: Optional[Exception] = None

    def run_if_due(
        self,
        *,
        excluded_coin_ids: Optional[set[str]] = None,
    ) -> Optional[ExtremeMovementDiscoveryBridgeResult]:
        if not self._schedule.should_run():
            return None

        self.last_error = None
        self.last_trace_error = None
        self.last_directional_history_error = None

        try:
            discovery = self._discovery_runner.run(
                excluded_coin_ids=excluded_coin_ids,
            )

            observed_at = datetime.now(timezone.utc)

            self._save_discovery_trace(
                discovery,
                observed_at=observed_at,
            )

            self._save_directional_history(
                observed_at=observed_at,
            )

            shadow = self._shadow_runner.run_analysis_results(
                discovery.analysis_results
            )

            result = ExtremeMovementDiscoveryBridgeResult(
                discovery=discovery,
                shadow=shadow,
            )

            self.last_result = result
            return result

        except Exception as error:
            self.last_error = error
            return None

    def _save_discovery_trace(
        self,
        discovery: ExtremeMovementDiscoveryResult,
        *,
        observed_at: datetime,
    ) -> None:
        if self._trace_store is None:
            return

        try:
            trace = ExtremeMovementDiscoveryTrace.from_result(
                discovery,
                observed_at=observed_at,
                experimental_comparison=getattr(
                    self._discovery_runner,
                    "last_experimental_comparison",
                    None,
                ),
                experimental_error=getattr(
                    self._discovery_runner,
                    "last_experimental_error",
                    None,
                ),
            )

            self._trace_store.save(trace)

        except Exception as error:
            self.last_trace_error = error

    def _save_directional_history(
        self,
        *,
        observed_at: datetime,
    ) -> None:
        if self._directional_history_store is None:
            return

        comparison = getattr(
            self._discovery_runner,
            "last_experimental_comparison",
            None,
        )

        if comparison is None:
            return

        try:
            self._directional_history_store.save(
                comparison,
                observed_at=observed_at,
            )

        except Exception as error:
            # O historico experimental nao deve interromper
            # o scanner conservador nem a analise Shadow.
            self.last_directional_history_error = error
