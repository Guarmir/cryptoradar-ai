"""Consulta somente-leitura de vinculos ja comprovados entre UID e instalacao.

Nao expoe operacao de reivindicacao de instalacao: um installation_id
informado por um cliente nao e prova de posse.
"""
from typing import Any, Callable, Optional


class PostgreSQLPushInstallationOwnerStore:
    TABLE_NAME = "cryptoradar_push_installation_owners"

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

    def load_owner_uid(self, installation_id: str) -> Optional[str]:
        normalized = installation_id.strip()
        if not normalized:
            raise ValueError("O identificador da instalacao nao pode ser vazio.")
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    SELECT firebase_auth_uid
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s AND installation_id = %s
                    """,
                    (self._scope_key, normalized),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()
        if row is None:
            return None
        uid = str(row[0]).strip()
        return uid or None

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory(self._database_url)
        import psycopg
        return psycopg.connect(self._database_url)
