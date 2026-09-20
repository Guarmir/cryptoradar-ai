from typing import Any, Callable, Optional

from app.access.access_entitlements import (
    AccessPlan,
)
from app.access.access_plan_store import (
    AccessPlanStore,
)


class PostgreSQLAccessPlanStore(
    AccessPlanStore
):
    TABLE_NAME = (
        "cryptoradar_access_plans"
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
                "nao pode ser vazia."
            )

        if not normalized_scope_key:
            raise ValueError(
                "O escopo de acesso "
                "nao pode ser vazio."
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

    def load_plan(
        self,
        installation_id: str,
    ) -> Optional[AccessPlan]:
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
                        plan
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

        return self._normalize_plan(
            str(
                row[0],
            )
        )

    def save_plan(
        self,
        *,
        installation_id: str,
        plan: AccessPlan,
    ) -> None:
        normalized_installation_id = (
            self._normalize_installation_id(
                installation_id,
            )
        )

        if not normalized_installation_id:
            raise ValueError(
                "O installation_id "
                "nao pode ser vazio."
            )

        normalized_plan = (
            self._normalize_plan(
                plan,
            )
        )

        connection = self._connect()

        try:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key,
                        installation_id,
                        plan,
                        updated_at
                    )
                    VALUES (
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
                        plan = EXCLUDED.plan,
                        updated_at = NOW()
                    """,
                    (
                        self._scope_key,
                        normalized_installation_id,
                        normalized_plan,
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
    def _normalize_installation_id(
        value: str,
    ) -> str:
        return value.strip()

    @staticmethod
    def _normalize_plan(
        value: str,
    ) -> AccessPlan:
        normalized = value.strip().lower()

        if normalized not in (
            "free",
            "pro",
        ):
            raise ValueError(
                "O plano deve ser "
                "'free' ou 'pro'."
            )

        return normalized