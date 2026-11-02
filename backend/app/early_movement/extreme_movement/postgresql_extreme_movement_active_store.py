
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_maturity import (
    ExtremeMovementMaturity,
)


@dataclass(frozen=True)
class ExtremeMovementActiveRecord:
    entry: ExtremeMovementAnalysisEntry
    missed_cycles: int
    first_observed_at: datetime
    last_observed_at: datetime
    observation_status: str = "active"

    discovery_price: float | None = None
    discovery_price_at: datetime | None = None
    latest_price: float | None = None
    latest_price_at: datetime | None = None


class PostgreSQLExtremeMovementActiveStore:
    TABLE_NAME = (
        "cryptoradar_extreme_movement_active_observations"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        database_url = database_url.strip()
        scope_key = scope_key.strip()

        if not database_url:
            raise ValueError(
                "A URL do PostgreSQL nao pode ser vazia."
            )

        if not scope_key:
            raise ValueError(
                "O escopo nao pode ser vazio."
            )

        self._database_url = database_url
        self._scope_key = scope_key
        self._connection_factory = connection_factory

    @staticmethod
    def _validate_price(
        price: float | None,
        timestamp: datetime | None,
        field_name: str,
    ) -> None:
        if (price is None) != (timestamp is None):
            raise ValueError(
                f"{field_name}: preco e horario devem "
                "ser informados juntos."
            )

        if price is not None and price <= 0:
            raise ValueError(
                f"{field_name}: preco deve ser positivo."
            )

        if timestamp is not None and (
            timestamp.tzinfo is None
            or timestamp.utcoffset() is None
        ):
            raise ValueError(
                f"{field_name}: horario precisa de fuso."
            )

    def save(
        self,
        record: ExtremeMovementActiveRecord,
        *,
        connection=None,
    ) -> None:
        entry = record.entry
        assessment = entry.assessment
        maturity = entry.maturity

        if maturity is None:
            raise ValueError(
                "A maturidade e obrigatoria para persistencia."
            )

        if record.missed_cycles < 0:
            raise ValueError(
                "missed_cycles nao pode ser negativo."
            )

        if record.last_observed_at < record.first_observed_at:
            raise ValueError(
                "last_observed_at nao pode ser anterior "
                "a first_observed_at."
            )

        if record.observation_status not in {
            "active",
            "awaiting_update",
            "closed",
        }:
            raise ValueError(
                "Status de observacao invalido."
            )

        self._validate_price(
            record.discovery_price,
            record.discovery_price_at,
            "discovery_price",
        )
        self._validate_price(
            record.latest_price,
            record.latest_price_at,
            "latest_price",
        )

        owns_connection = connection is None

        if owns_connection:
            connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        coin_id,
                        symbol,
                        name,
                        state,
                        direction,
                        relevance_score,
                        supporting_evidence_count,
                        maturity_level,
                        observation_status,
                        missed_cycles,
                        first_observed_at,
                        last_observed_at,
                        discovery_price,
                        discovery_price_at,
                        latest_price,
                        latest_price_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s
                    )
                    ON CONFLICT (scope_key, coin_id)
                    DO UPDATE SET
                        symbol = EXCLUDED.symbol,
                        name = EXCLUDED.name,
                        state = EXCLUDED.state,
                        direction = EXCLUDED.direction,
                        relevance_score = EXCLUDED.relevance_score,
                        supporting_evidence_count =
                            EXCLUDED.supporting_evidence_count,
                        maturity_level = EXCLUDED.maturity_level,
                        observation_status =
                            EXCLUDED.observation_status,
                        missed_cycles = EXCLUDED.missed_cycles,
                        last_observed_at =
                            EXCLUDED.last_observed_at,
                        discovery_price = COALESCE(
                            {self.TABLE_NAME}.discovery_price,
                            EXCLUDED.discovery_price
                        ),
                        discovery_price_at = COALESCE(
                            {self.TABLE_NAME}.discovery_price_at,
                            EXCLUDED.discovery_price_at
                        ),
                        latest_price = COALESCE(
                            EXCLUDED.latest_price,
                            {self.TABLE_NAME}.latest_price
                        ),
                        latest_price_at = COALESCE(
                            EXCLUDED.latest_price_at,
                            {self.TABLE_NAME}.latest_price_at
                        ),
                        updated_at = NOW()
                    """,
                    (
                        self._scope_key,
                        entry.coin_id,
                        entry.symbol,
                        entry.name,
                        assessment.state,
                        assessment.direction,
                        assessment.relevance_score,
                        assessment.supporting_evidence_count,
                        maturity.level,
                        record.observation_status,
                        record.missed_cycles,
                        record.first_observed_at,
                        record.last_observed_at,
                        record.discovery_price,
                        record.discovery_price_at,
                        record.latest_price,
                        record.latest_price_at,
                    ),
                )

                if owns_connection:
                    connection.commit()

            except Exception:
                if owns_connection:
                    connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            if owns_connection:
                connection.close()

    def load_active(
        self,
    ) -> tuple[ExtremeMovementActiveRecord, ...]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        coin_id,
                        symbol,
                        name,
                        state,
                        direction,
                        relevance_score,
                        supporting_evidence_count,
                        maturity_level,
                        observation_status,
                        missed_cycles,
                        first_observed_at,
                        last_observed_at,
                        discovery_price,
                        discovery_price_at,
                        latest_price,
                        latest_price_at
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND observation_status IN (
                          'active',
                          'awaiting_update'
                      )
                    ORDER BY last_observed_at DESC, id DESC
                    """,
                    (self._scope_key,),
                )

                rows = cursor.fetchall()

            finally:
                cursor.close()

        finally:
            connection.close()

        return tuple(
            self._record_from_row(row)
            for row in rows
        )

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory(
                self._database_url
            )

        import psycopg

        return psycopg.connect(
            self._database_url
        )

    @staticmethod
    def _record_from_row(
        row,
    ) -> ExtremeMovementActiveRecord:
        (
            coin_id,
            symbol,
            name,
            state,
            direction,
            relevance_score,
            evidence_count,
            maturity_level,
            observation_status,
            missed_cycles,
            first_observed_at,
            last_observed_at,
            discovery_price,
            discovery_price_at,
            latest_price,
            latest_price_at,
        ) = row

        assessment = ExtremeMovementAssessment(
            state=state,
            direction=direction,
            relevance_score=relevance_score,
            supporting_evidence_count=evidence_count,
        )

        maturity = ExtremeMovementMaturity(
            level=maturity_level,
            evidence_count=evidence_count,
            relevance_score=relevance_score,
        )

        entry = ExtremeMovementAnalysisEntry(
            coin_id=coin_id,
            symbol=symbol,
            name=name,
            assessment=assessment,
            maturity=maturity,
            current_price=latest_price,
        )

        return ExtremeMovementActiveRecord(
            entry=entry,
            missed_cycles=missed_cycles,
            first_observed_at=first_observed_at,
            last_observed_at=last_observed_at,
            observation_status=observation_status,
            discovery_price=discovery_price,
            discovery_price_at=discovery_price_at,
            latest_price=latest_price,
            latest_price_at=latest_price_at,
        )
