
from datetime import datetime, timezone
from typing import Any, Callable

from app.early_movement.extreme_movement.extreme_movement_observation_record import (
    ExtremeMovementObservationRecord,
)
from app.early_movement.extreme_movement.extreme_movement_observation_store import (
    ExtremeMovementObservationCycle,
    ExtremeMovementObservationStore,
    ExtremeMovementTrackedAsset,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_active_store import (
    ExtremeMovementActiveRecord,
    PostgreSQLExtremeMovementActiveStore,
)
from app.early_movement.extreme_movement.postgresql_extreme_movement_observation_store import (
    PostgreSQLExtremeMovementObservationStore,
)


class ExtremeMovementPersistenceService:
    def __init__(
        self,
        *,
        observation_store: ExtremeMovementObservationStore,
        history_store: PostgreSQLExtremeMovementObservationStore,
        active_store: PostgreSQLExtremeMovementActiveStore,
        connection_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._observation_store = observation_store
        self._history_store = history_store
        self._active_store = active_store
        self._connection_factory = connection_factory
        self._active_records: dict[str, ExtremeMovementActiveRecord] = {}
        self._restored = False

    def restore(self) -> bool:
        if self._restored:
            return True

        records = self._active_store.load_active()

        assets = tuple(
            ExtremeMovementTrackedAsset(
                coin_id=record.entry.coin_id,
                last_entry=record.entry,
                missed_cycles=record.missed_cycles,
            )
            for record in records
        )

        self._observation_store.restore(assets)

        self._active_records = {
            record.entry.coin_id: record
            for record in records
        }
        self._restored = True
        return True

    def persist(
        self,
        cycle: ExtremeMovementObservationCycle,
        *,
        observed_at: datetime | None = None,
    ) -> None:
        if not self._restored:
            raise RuntimeError(
                "A persistencia precisa ser restaurada "
                "antes de registrar novos ciclos."
            )

        timestamp = (
            observed_at
            if observed_at is not None
            else datetime.now(timezone.utc)
        )

        if (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                "observed_at precisa conter fuso horario."
            )

        history_records = []
        active_records = []
        observed_coin_ids = set()

        for observation in cycle.observations:
            entry = observation.current
            assessment = entry.assessment
            maturity = entry.maturity

            if maturity is None:
                raise ValueError(
                    "Maturidade obrigatoria para persistencia."
                )

            observed_coin_ids.add(entry.coin_id)

            history_records.append(
                ExtremeMovementObservationRecord(
                    observed_at=timestamp,
                    coin_id=entry.coin_id,
                    symbol=entry.symbol,
                    name=entry.name,
                    state=assessment.state,
                    direction=assessment.direction,
                    relevance_score=assessment.relevance_score,
                    supporting_evidence_count=(
                        assessment.supporting_evidence_count
                    ),
                    maturity_level=maturity.level,
                    observation_change=observation.change,
                )
            )

        for asset in cycle.active_assets:
            coin_id = asset.coin_id
            previous = self._active_records.get(coin_id)

            if coin_id in observed_coin_ids:
                first_observed_at = (
                    previous.first_observed_at
                    if previous is not None
                    else timestamp
                )
                last_observed_at = timestamp
                status = "active"
            else:
                if previous is None:
                    continue

                first_observed_at = previous.first_observed_at
                last_observed_at = previous.last_observed_at
                status = "awaiting_update"

            active_records.append(
                ExtremeMovementActiveRecord(
                    entry=asset.last_entry,
                    missed_cycles=asset.missed_cycles,
                    first_observed_at=first_observed_at,
                    last_observed_at=last_observed_at,
                    observation_status=status,
                )
            )

        if not history_records and not active_records:
            return

        if self._connection_factory is None:
            raise RuntimeError(
                "Conexao transacional nao configurada."
            )

        connection = self._connection_factory()

        try:
            for record in history_records:
                self._history_store.save(
                    record,
                    connection=connection,
                )

            for record in active_records:
                self._active_store.save(
                    record,
                    connection=connection,
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        # Atualiza a memoria somente apos o commit.
        for record in active_records:
            self._active_records[record.entry.coin_id] = record
