from typing import Any, Callable, Optional

from app.push.push_notification_preferences import PushNotificationPreferences


class PostgreSQLPushNotificationPreferencesStore:
    """Preferencias isoladas por (scope_key, installation_id)."""

    TABLE_NAME = "cryptoradar_push_notification_preferences"

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self._database_url = database_url.strip()
        self._scope_key = scope_key.strip()
        self._connection_factory = connection_factory
        if not self._database_url:
            raise ValueError("A URL do PostgreSQL nao pode ser vazia.")
        if not self._scope_key:
            raise ValueError("O escopo de push nao pode ser vazio.")

    def load(self, installation_id: str) -> PushNotificationPreferences:
        installation_id = self._normalize_installation_id(installation_id)
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    SELECT observation_enabled,
                           early_movement_enabled,
                           confirmed_movement_enabled
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s AND installation_id = %s
                    """,
                    (self._scope_key, installation_id),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()

        if row is None:
            return PushNotificationPreferences()
        return PushNotificationPreferences(
            observation_enabled=bool(row[0]),
            early_movement_enabled=bool(row[1]),
            confirmed_movement_enabled=bool(row[2]),
        )

    def save(
        self,
        installation_id: str,
        preferences: PushNotificationPreferences,
    ) -> None:
        installation_id = self._normalize_installation_id(installation_id)
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key, installation_id,
                        observation_enabled, early_movement_enabled,
                        confirmed_movement_enabled, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (scope_key, installation_id)
                    DO UPDATE SET
                        observation_enabled = EXCLUDED.observation_enabled,
                        early_movement_enabled = EXCLUDED.early_movement_enabled,
                        confirmed_movement_enabled = EXCLUDED.confirmed_movement_enabled,
                        updated_at = NOW()
                    """,
                    (
                        self._scope_key,
                        installation_id,
                        preferences.observation_enabled,
                        preferences.early_movement_enabled,
                        preferences.confirmed_movement_enabled,
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

    @staticmethod
    def _normalize_installation_id(value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O identificador da instalacao nao pode ser vazio.")
        return normalized
