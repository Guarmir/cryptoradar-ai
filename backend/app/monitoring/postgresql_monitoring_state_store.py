import json
from typing import Any, Callable, Optional

from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_state_serializer import (
    monitoring_state_from_dict,
    monitoring_state_to_dict,
)
from app.monitoring.monitoring_state_store import (
    MonitoringStateStore,
)


class PostgreSQLMonitoringStateStore(
    MonitoringStateStore
):
    TABLE_NAME = (
        "cryptoradar_monitoring_states"
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
                "O escopo do monitoramento "
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

    def load_state(
        self,
        symbol: str,
    ) -> Optional[MonitoringState]:
        normalized_symbol = (
            self._normalize_symbol(
                symbol,
            )
        )

        if not normalized_symbol:
            return None

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT state_data
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND symbol = %s
                    """,
                    (
                        self._scope_key,
                        normalized_symbol,
                    ),
                )

                row = cursor.fetchone()

            finally:
                cursor.close()

        finally:
            connection.close()

        if row is None:
            return None

        payload = self._decode_payload(
            row[0],
        )

        return monitoring_state_from_dict(
            payload,
        )

    def load_all(
        self,
    ) -> tuple[MonitoringState, ...]:
        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    SELECT state_data
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                    ORDER BY symbol
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
            monitoring_state_from_dict(
                self._decode_payload(
                    row[0],
                )
            )
            for row in rows
        )

    def save_state(
        self,
        state: MonitoringState,
    ) -> None:
        serialized = (
            monitoring_state_to_dict(
                state,
            )
        )

        encoded = json.dumps(
            serialized,
            separators=(
                ",",
                ":",
            ),
        )

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        symbol,
                        state_data,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s::jsonb,
                        NOW()
                    )
                    ON CONFLICT (
                        scope_key,
                        symbol
                    )
                    DO UPDATE SET
                        state_data =
                            EXCLUDED.state_data,
                        updated_at =
                            NOW()
                    """,
                    (
                        self._scope_key,
                        state.target.symbol,
                        encoded,
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

    def delete_state(
        self,
        symbol: str,
    ) -> bool:
        normalized_symbol = (
            self._normalize_symbol(
                symbol,
            )
        )

        if not normalized_symbol:
            return False

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    DELETE FROM {self.TABLE_NAME}
                    WHERE scope_key = %s
                      AND symbol = %s
                    """,
                    (
                        self._scope_key,
                        normalized_symbol,
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
    def _decode_payload(
        value: Any,
    ) -> dict[str, Any]:
        if isinstance(
            value,
            dict,
        ):
            return dict(
                value,
            )

        if isinstance(
            value,
            bytes,
        ):
            value = value.decode(
                "utf-8",
            )

        if isinstance(
            value,
            str,
        ):
            decoded = json.loads(
                value,
            )

            if not isinstance(
                decoded,
                dict,
            ):
                raise ValueError(
                    "Estado persistido "
                    "possui estrutura inválida."
                )

            return decoded

        raise ValueError(
            "Estado persistido "
            "possui formato inválido."
        )

    @staticmethod
    def _normalize_symbol(
        value: str,
    ) -> str:
        return value.strip().upper()