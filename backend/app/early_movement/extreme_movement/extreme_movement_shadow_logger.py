import json
import logging
from datetime import datetime, timezone

from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowResult,
)


class ExtremeMovementShadowLogger:
    def __init__(
        self,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = (
            logger
            if logger is not None
            else logging.getLogger(
                "cryptoradar.extreme_movement.shadow"
            )
        )

    def log(
        self,
        result: ExtremeMovementShadowResult,
    ) -> None:
        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        payload = {
            "event": "extreme_movement_shadow_cycle",
            "timestamp": timestamp,
            "analyzed_count": result.analyzed_count,
            "evaluated_count": result.evaluated_count,
            "extreme_acceleration_count": (
                result.extreme_acceleration_count
            ),
            "movement_pressure_count": (
                result.movement_pressure_count
            ),
            "possible_reversal_count": (
                result.possible_reversal_count
            ),
            "insufficient_evidence_count": (
                result.insufficient_evidence_count
            ),
            "assets": [
                {
                    "coin_id": entry.coin_id,
                    "symbol": entry.symbol,
                    "name": entry.name,
                    "state": entry.assessment.state,
                    "direction": entry.assessment.direction,
                    "relevance_score": (
                        entry.assessment.relevance_score
                    ),
                    "supporting_evidence_count": (
                        entry.assessment.supporting_evidence_count
                    ),
                }
                for entry in result.entries
            ],
        }

        self._logger.info(
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
            )
        )