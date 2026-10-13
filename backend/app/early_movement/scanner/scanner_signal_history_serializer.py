
from datetime import timezone

from app.early_movement.scanner.scanner_signal_history_record import (
    EarlyMovementScannerSignalHistoryRecord,
)


class EarlyMovementScannerSignalHistorySerializer:
    @staticmethod
    def serialize(
        record: EarlyMovementScannerSignalHistoryRecord,
    ) -> dict:
        observed_at = record.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(
                tzinfo=timezone.utc,
            )

        return {
            "observed_at": observed_at.isoformat(),
            "coin_id": record.coin_id,
            "symbol": record.symbol,
            "name": record.name,
            "current_price": record.current_price,
            "state": record.state.value,
            "relevance_score": record.relevance_score,
            "price_acceleration": record.price_acceleration,
            "abnormal_volume_ratio": record.abnormal_volume_ratio,
            "liquidity_score": record.liquidity_score,
            "volatility_expansion": record.volatility_expansion,
            "persistence_score": record.persistence_score,
            "false_breakout_risk": record.false_breakout_risk,
            "support_break": record.support_break,
            "resistance_break": record.resistance_break,
            "retest_confirmed": record.retest_confirmed,
            "breakout_direction": record.breakout_direction,
            "alertable": record.alertable,
        }
