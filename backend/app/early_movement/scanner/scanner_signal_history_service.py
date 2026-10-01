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


class EarlyMovementScannerSignalHistoryService:
    def __init__(
        self,
        *,
        store: EarlyMovementScannerSignalHistoryStore,
    ) -> None:
        self._store = store

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
                )
            )

            self._store.save(
                record,
            )

            records.append(
                record,
            )

        return tuple(
            records,
        )