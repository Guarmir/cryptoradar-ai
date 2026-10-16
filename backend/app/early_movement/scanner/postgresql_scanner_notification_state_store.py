
from typing import Any, Callable, Optional

from app.early_movement.scanner.scanner_notification_state_store import (
    EarlyMovementScannerNotificationState,
    EarlyMovementScannerNotificationStateStore,
)


class PostgreSQLEarlyMovementScannerNotificationStateStore(
    EarlyMovementScannerNotificationStateStore
):
    TABLE_NAME = "cryptoradar_early_movement_notification_state"

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[
            Callable[[str], Any]
        ] = None,
    ) -> None:
        if not database_url.strip():
            raise ValueError("A URL do PostgreSQL não pode ser vazia.")

        if not scope_key.strip():
            raise ValueError("O escopo não pode ser vazio.")

        self._database_url = database_url.strip()
        self._scope_key = scope_key.strip()
        self._connection_factory = connection_factory

    def load(
        self,
        coin_id: str,
    ) -> Optional[EarlyMovementScannerNotificationState]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        coin_id,
                        last_notified_state,
                        last_notified_at
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND coin_id = %s
                    """,
                    (self._scope_key, coin_id),
                )

                row = cursor.fetchone()

            finally:
                cursor.close()

        finally:
            connection.close()

        if row is None:
            return None

        return EarlyMovementScannerNotificationState(
            coin_id=row[0],
            last_notified_state=row[1],
            last_notified_at=row[2],
        )

    def save(
        self,
        state: EarlyMovementScannerNotificationState,
    ) -> None:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        coin_id,
                        last_notified_state,
                        last_notified_at
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (scope_key, coin_id)
                    DO UPDATE SET
                        last_notified_state = EXCLUDED.last_notified_state,
                        last_notified_at = EXCLUDED.last_notified_at,
                        updated_at = NOW()
                    """,
                    (
                        self._scope_key,
                        state.coin_id,
                        state.last_notified_state,
                        state.last_notified_at,
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
            return self._connection_factory(self._database_url)

        import psycopg

        return psycopg.connect(self._database_url)
