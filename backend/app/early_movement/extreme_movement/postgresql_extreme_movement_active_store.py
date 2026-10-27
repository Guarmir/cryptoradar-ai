
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
                        last_observed_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
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
                        last_observed_at
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
        )

        return ExtremeMovementActiveRecord(
            entry=entry,
            missed_cycles=missed_cycles,
            first_observed_at=first_observed_at,
            last_observed_at=last_observed_at,
            observation_status=observation_status,
        )
