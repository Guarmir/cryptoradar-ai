
from datetime import datetime
from typing import Any, Callable

from psycopg.types.json import Jsonb

from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
    ExtremeMovementCandidateComparison,
)


class PostgreSQLExtremeMovementDirectionalHistoryStore:
    TABLE_NAME = (
        "cryptoradar_extreme_movement_directional_history"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Callable[[str], Any] | None = None,
    ) -> None:
        if not database_url or not database_url.strip():
            raise ValueError("DATABASE_URL nao pode ser vazia.")

        if not scope_key or not scope_key.strip():
            raise ValueError("scope_key nao pode ser vazio.")

        self._database_url = database_url.strip()
        self._scope_key = scope_key.strip()
        self._connection_factory = connection_factory

    def save(
        self,
        comparison: ExtremeMovementCandidateComparison,
        *,
        observed_at: datetime,
    ) -> None:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("observed_at precisa conter fuso horario.")

        entries = [
            {
                "coin_id": item.coin_id,
                "state": item.state,
                "direction": item.direction,
                "previous_direction": (
                    item.previous_direction or "unknown"
                ),
                "observation_count": item.observation_count,
                "consecutive_moves": item.consecutive_moves,
                "alternating_moves": item.alternating_moves,
                "latest_price_change_pct": (
                    item.latest_price_change_pct
                ),
            }
            for item in comparison.directional_continuities
        ]

        if not entries:
            return

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    WITH incoming AS (
                        SELECT *
                        FROM jsonb_to_recordset(%s::jsonb) AS item(
                            coin_id TEXT,
                            state TEXT,
                            direction TEXT,
                            previous_direction TEXT,
                            observation_count INTEGER,
                            consecutive_moves INTEGER,
                            alternating_moves INTEGER,
                            latest_price_change_pct DOUBLE PRECISION
                        )
                    )
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        coin_id,
                        observed_at,
                        state,
                        direction,
                        previous_direction,
                        observation_count,
                        consecutive_moves,
                        alternating_moves,
                        latest_price_change_pct
                    )
                    SELECT
                        %s,
                        incoming.coin_id,
                        %s,
                        incoming.state,
                        incoming.direction,
                        incoming.previous_direction,
                        incoming.observation_count,
                        incoming.consecutive_moves,
                        incoming.alternating_moves,
                        incoming.latest_price_change_pct
                    FROM incoming
                    LEFT JOIN LATERAL (
                        SELECT
                            previous.state,
                            previous.direction,
                            previous.observed_at
                        FROM {self.TABLE_NAME} previous
                        WHERE previous.scope_key = %s
                          AND previous.coin_id = incoming.coin_id
                        ORDER BY previous.observed_at DESC
                        LIMIT 1
                    ) last_record ON TRUE
                    WHERE last_record.observed_at IS NULL
                       OR incoming.state IS DISTINCT FROM last_record.state
                       OR incoming.direction IS DISTINCT FROM last_record.direction
                       OR %s - last_record.observed_at >= INTERVAL '2 hours'
                    ON CONFLICT (scope_key, coin_id, observed_at)
                    DO NOTHING
                    """,
                    (
                        Jsonb(entries),
                        self._scope_key,
                        observed_at,
                        self._scope_key,
                        observed_at,
                    ),
                )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory(self._database_url)

        import psycopg

        return psycopg.connect(self._database_url)
