from datetime import datetime, timezone

from app.early_movement.scanner.scanner_alert_decision import (
    EarlyMovementScannerAlertDecision,
)
from app.early_movement.scanner.scanner_run_result import (
    EarlyMovementScannerRunResult,
)
from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)
from app.early_movement.scanner.scanner_signal_history_store import (
    EarlyMovementScannerSignalHistoryStore,
)
from app.early_movement.early_movement_direction_classifier import (
    EarlyMovementDirectionClassifier,
)
from app.early_movement.early_movement_direction_transition import (
    EarlyMovementDirectionTransitionDetector,
)


class EarlyMovementScannerSignalHistoryService:
    def __init__(
        self,
        *,
        store: EarlyMovementScannerSignalHistoryStore,
    ) -> None:
        self._store = store

        self._transition_detector = (
            EarlyMovementDirectionTransitionDetector()
        )
        self.last_transitions = ()

    def record(
        self,
        *,
        scan_result: EarlyMovementScannerRunResult,
        alert_decision: EarlyMovementScannerAlertDecision,
    ) -> tuple[
        EarlyMovementScannerSignalHistoryRecord,
        ...,
    ]:
        observed_at = datetime.now(
            timezone.utc,
        )

        alertable_ids = {
            id(result)
            for result in alert_decision.results
        }

        records = []

        transitions = []
        self.last_transitions = ()

        for ranked in scan_result.ranked_results:
            analysis_result = ranked.result
            analysis = analysis_result.analysis

            if analysis is None:
                continue

            candidate = analysis_result.candidate
            asset = candidate.asset
            evidence = analysis.evidence

            breakout_confirmation = (
                analysis.breakout_confirmation
            )

            direction = EarlyMovementDirectionClassifier().classify(
                metrics=analysis.metrics,
                price_structure=analysis.price_structure,
            )

            previous_record = (
                self._store.load_latest_for_coin(
                    coin_id=asset.coin_id,
                )
            )

            previous_direction = (
                previous_record.direction
                if previous_record is not None
                else None
            )

            transition = self._transition_detector.detect(
                previous=previous_direction,
                current=direction,
            )

            transitions.append(transition)

            record = (
                EarlyMovementScannerSignalHistoryRecord(
                    observed_at=observed_at,
                    coin_id=asset.coin_id,
                    symbol=asset.symbol,
                    name=asset.name,
                    current_price=asset.current_price,
                    state=evidence.state,
                    relevance_score=(
                        ranked.relevance_score
                    ),
                    price_acceleration=(
                        evidence.price_acceleration
                    ),
                    abnormal_volume_ratio=(
                        evidence.abnormal_volume_ratio
                    ),
                    liquidity_score=(
                        evidence.liquidity_score
                    ),
                    volatility_expansion=(
                        evidence.volatility_expansion
                    ),
                    persistence_score=(
                        evidence.persistence_score
                    ),
                    false_breakout_risk=(
                        evidence.false_breakout_risk
                    ),
                    support_break=(
                        evidence.support_break
                    ),
                    resistance_break=(
                        evidence.resistance_break
                    ),
                    retest_confirmed=(
                        evidence.retest_confirmed
                    ),
                    breakout_direction=(
                        breakout_confirmation
                        .breakout_direction
                    ),
                    alertable=(
                        id(ranked)
                        in alertable_ids
                    ),
                    recent_price_return=(
                        analysis.metrics.recent_price_return
                    ),
                    direction=direction,
                )
            )

            self._store.save(
                record,
            )

            records.append(
                record,
            )

            self.last_transitions = tuple(transitions)

        return tuple(
            records,
        )