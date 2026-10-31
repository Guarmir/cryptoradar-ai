
from fastapi import APIRouter, HTTPException

from app.early_movement.scanner.scanner_runtime_config import (
    EarlyMovementScannerRuntimeConfig,
)
from app.early_movement.extreme_movement.extreme_movement_persistence_factory import (
    EXTREME_MOVEMENT_SCOPE_KEY,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    PostgreSQLExtremeMovementActiveStore,
)


def create_extreme_movement_router() -> APIRouter:
    router = APIRouter(
        tags=["extreme-movement"],
    )

    @router.get("/extreme-movement/active")
    def get_extreme_movement_active():
        config = EarlyMovementScannerRuntimeConfig.from_environment()

        if not config.database_url:
            raise HTTPException(
                status_code=503,
                detail="Radar Dinamico temporariamente indisponivel.",
            )

        try:
            store = PostgreSQLExtremeMovementActiveStore(
                database_url=config.database_url,
                scope_key=EXTREME_MOVEMENT_SCOPE_KEY,
            )

            records = store.load_active()

            observations = []

            for record in records:
                entry = record.entry
                assessment = entry.assessment
                maturity = entry.maturity

                observations.append(
                    {
                        "coin_id": entry.coin_id,
                        "symbol": entry.symbol,
                        "name": entry.name,
                        "state": assessment.state,
                        "direction": assessment.direction,
                        "relevance_score": assessment.relevance_score,
                        "supporting_evidence_count": (
                            assessment.supporting_evidence_count
                        ),
                        "maturity_level": maturity.level,
                        "observation_status": record.observation_status,
                        "missed_cycles": record.missed_cycles,
                        "first_observed_at": (
                            record.first_observed_at.isoformat()
                        ),
                        "last_observed_at": (
                            record.last_observed_at.isoformat()
                        ),
                    }
                )

            return {
                "status": "ok",
                "count": len(observations),
                "observations": observations,
            }

        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Radar Dinamico temporariamente indisponivel.",
            ) from exc

    return router
