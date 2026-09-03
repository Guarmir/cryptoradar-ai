from typing import Any, Callable, Optional

from app.push.push_device import PushDevice
from app.push.push_device_store import PushDeviceStore


class PostgreSQLPushDeviceStore(
    PushDeviceStore
):
    TABLE_NAME = (
        "cryptoradar_push_devices"
    )

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Optional[
            Callable[[str], Any]
        ] = None,
    ):
        normalized_database_url = (
            database_url.strip()
        )

        normalized_scope_key = (
            scope_key.strip()
        )

        if not normalized_database_url:
            raise ValueError(
                "A URL do PostgreSQL "
                "não pode ser vazia."
            )

        if not normalized_scope_key:
            raise ValueError(
                "O escopo de push "
                "não pode ser vazio."
            )

        self._database_url = (
            normalized_database_url
        )

        self._scope_key = (
            normalized_scope_key
        )

        self._connection_factory = (
            connection_factory
        )

    @property
    def scope_key(self) -> str:
        return self._scope_key

    def load_device(
        self,
        installation_id: str,
    ) -> Optional[PushDevice]:
        normalized_installation_id = (
            self._normalize_installation_id(
                installation_id,
            )
        )

        if not normalized_installation_id:
            return None

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        installation_id,
                        fcm_token,
                        platform,
                        enabled
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND installation_id = %s
                    """,
                    (
                        self._scope_key,
                        normalized_installation_id,
                    ),
                )

                row = cursor.fetchone()

            finally:
                cursor.close()

        finally:
            connection.close()

        if row is None:
            return None

        return self._device_from_row(
            row,
        )

    def load_all(
        self,
    ) -> tuple[PushDevice, ...]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        installation_id,
                        fcm_token,
                        platform,
                        enabled
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                    ORDER BY installation_id
                    """,
                    (
                        self._scope_key,
                    ),
                )

                rows = cursor.fetchall()

            finally:
                cursor.close()

        finally:
            connection.close()

        return tuple(
            self._device_from_row(
                row,
            )
            for row in rows
        )

    def load_enabled(
        self,
    ) -> tuple[PushDevice, ...]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT
                        installation_id,
                        fcm_token,
                        platform,
                        enabled
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND enabled = TRUE
                    ORDER BY installation_id
                    """,
                    (
                        self._scope_key,
                    ),
                )

                rows = cursor.fetchall()

            finally:
                cursor.close()

        finally:
            connection.close()

        return tuple(
            self._device_from_row(
                row,
            )
            for row in rows
        )

    def save_device(
        self,
        device: PushDevice,
    ) -> None:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        installation_id,
                        fcm_token,
                        platform,
                        enabled,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        NOW()
                    )
                    ON CONFLICT (
                        scope_key,
                        installation_id
                    )
                    DO UPDATE SET
                        fcm_token =
                            EXCLUDED.fcm_token,
                        platform =
                            EXCLUDED.platform,
                        enabled =
                            EXCLUDED.enabled,
                        updated_at =
                            NOW()
                    """,
                    (
                        self._scope_key,
                        device.installation_id,
                        device.fcm_token,
                        device.platform,
                        device.enabled,
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

    def delete_device(
        self,
        installation_id: str,
    ) -> bool:
        normalized_installation_id = (
            self._normalize_installation_id(
                installation_id,
            )
        )

        if not normalized_installation_id:
            return False

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    DELETE FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND installation_id = %s
                    """,
                    (
                        self._scope_key,
                        normalized_installation_id,
                    ),
                )

                removed = (
                    cursor.rowcount > 0
                )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                cursor.close()

        finally:
            connection.close()

        return removed

    def clear(
        self,
    ) -> None:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    DELETE FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                    """,
                    (
                        self._scope_key,
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

    def _connect(
        self,
    ):
        if self._connection_factory is not None:
            return self._connection_factory(
                self._database_url,
            )

        import psycopg

        return psycopg.connect(
            self._database_url,
        )

    @staticmethod
    def _device_from_row(
        row: Any,
    ) -> PushDevice:
        return PushDevice(
            installation_id=str(
                row[0],
            ),
            fcm_token=str(
                row[1],
            ),
            platform=str(
                row[2],
            ),
            enabled=bool(
                row[3],
            ),
        )

    @staticmethod
    def _normalize_installation_id(
        value: str,
    ) -> str:
        return value.strip()