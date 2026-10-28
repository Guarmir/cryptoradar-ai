from dataclasses import dataclass
from typing import Any, Optional

from app.early_movement.extreme_movement.extreme_movement_discovery_schedule import (
    ExtremeMovementDiscoverySchedule,
)
from app.early_movement.extreme_movement.extreme_movement_discovery_runner import (
    ExtremeMovementDiscoveryRunner,
    ExtremeMovementDiscoveryResult,
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

        self.last_result: Optional[
            ExtremeMovementDiscoveryBridgeResult
        ] = None
        self.last_error: Optional[Exception] = None

    def run_if_due(
        self,
        *,
        excluded_coin_ids: Optional[set[str]] = None,
    ) -> Optional[ExtremeMovementDiscoveryBridgeResult]:
        if not self._schedule.should_run():
            return None

        self.last_error = None

        try:
            discovery = self._discovery_runner.run(
                excluded_coin_ids=excluded_coin_ids,
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
