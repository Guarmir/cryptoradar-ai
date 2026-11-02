
from typing import Any, Callable, Optional

from psycopg.types.json import Jsonb

from app.early_movement.extreme_movement.extreme_movement_discovery_trace import (
    ExtremeMovementDiscoveryTrace,
)


class PostgreSQLExtremeMovementDiscoveryTraceStore:
    TABLE_NAME = (
        "cryptoradar_extreme_movement_discovery_trace"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[
            Callable[[str], Any]
        ] = None,
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
        trace: ExtremeMovementDiscoveryTrace,
    ) -> None:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        observed_at,
                        universe_size,
                        candidate_count,
                        analyzed_count,
                        excluded_count,
                        selected_coin_ids,
                        submitted_coin_ids,
                        not_submitted_coin_ids
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    """,
                    (
                        self._scope_key,
                        trace.observed_at,
                        trace.universe_size,
                        trace.candidate_count,
                        trace.analyzed_count,
                        trace.excluded_count,
                        Jsonb(list(trace.selected_coin_ids)),
                        Jsonb(list(trace.submitted_coin_ids)),
                        Jsonb(list(trace.not_submitted_coin_ids)),
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

    def _connect(self):
        if self._connection_factory is not None:
            return self._connection_factory(
                self._database_url
            )

        import psycopg

        return psycopg.connect(
            self._database_url
        )
