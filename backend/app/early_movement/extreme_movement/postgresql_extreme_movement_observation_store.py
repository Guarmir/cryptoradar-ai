
from typing import Any, Callable, Optional

from app.early_movement.extreme_movement.extreme_movement_observation_record import (
    ExtremeMovementObservationRecord,
)


class PostgreSQLExtremeMovementObservationStore:
    TABLE_NAME = (
        "cryptoradar_extreme_movement_observation_history"
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

    @property
    def scope_key(self) -> str:
        return self._scope_key

    def save(
        self,
        record: ExtremeMovementObservationRecord,
        *,
        connection=None,
    ) -> None:
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
                        observed_at,
                        coin_id,
                        symbol,
                        name,
                        state,
                        direction,
                        relevance_score,
                        supporting_evidence_count,
                        maturity_level,
                        observation_change
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        self._scope_key,
                        record.observed_at,
                        record.coin_id,
                        record.symbol,
                        record.name,
                        record.state,
                        record.direction,
                        record.relevance_score,
                        record.supporting_evidence_count,
                        record.maturity_level,
                        record.observation_change,
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

    def load_recent(
        self,
        *,
        limit: int = 100,
    ) -> tuple[ExtremeMovementObservationRecord, ...]:
        if limit < 1:
            raise ValueError(
                "O limite deve ser maior que zero."
            )

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        observed_at,
                        coin_id,
                        symbol,
                        name,
                        state,
                        direction,
                        relevance_score,
                        supporting_evidence_count,
                        maturity_level,
                        observation_change
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                    ORDER BY observed_at DESC, id DESC
                    LIMIT %s
                    """,
                    (
                        self._scope_key,
                        limit,
                    ),
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

    def load_latest_for_coin(
        self,
        *,
        coin_id: str,
    ) -> Optional[ExtremeMovementObservationRecord]:
        coin_id = coin_id.strip()

        if not coin_id:
            raise ValueError(
                "O identificador do ativo nao pode ser vazio."
            )

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        observed_at,
                        coin_id,
                        symbol,
                        name,
                        state,
                        direction,
                        relevance_score,
                        supporting_evidence_count,
                        maturity_level,
                        observation_change
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND coin_id = %s
                    ORDER BY observed_at DESC, id DESC
                    LIMIT 1
                    """,
                    (
                        self._scope_key,
                        coin_id,
                    ),
                )

                row = cursor.fetchone()

            finally:
                cursor.close()

        finally:
            connection.close()

        if row is None:
            return None

        return self._record_from_row(row)

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
    ) -> ExtremeMovementObservationRecord:
        return ExtremeMovementObservationRecord(
            observed_at=row[0],
            coin_id=row[1],
            symbol=row[2],
            name=row[3],
            state=row[4],
            direction=row[5],
            relevance_score=row[6],
            supporting_evidence_count=row[7],
            maturity_level=row[8],
            observation_change=row[9],
        )
