"""Persistencia de assinaturas verificadas, sem ativar o plano PRO.

Somente uma camada autenticada, apos consultar diretamente a Google Play,
deve chamar save_verified. O armazenamento nao valida pagamentos por si so.
O hash do token identifica a compra sem persistir a credencial em texto puro.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Callable


class PurchaseTokenAlreadyClaimedError(Exception):
    """Uma compra ja esta associada a outro UID Firebase."""


@dataclass(frozen=True)
class StoredGooglePlaySubscription:
    firebase_auth_uid: str
    product_id: str
    subscription_state: str
    acknowledgement_state: str
    expires_at: datetime


class PostgreSQLGooglePlaySubscriptionStore:
    TABLE_NAME = "cryptoradar_google_play_subscriptions"

    def __init__(
        self,
        *,
        database_url: str,
        scope_key: str,
        connection_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self._database_url = self._required(database_url, "database_url")
        self._scope_key = self._required(scope_key, "scope_key")
        self._connection_factory = connection_factory

    def save_verified(
        self,
        *,
        purchase_token: str,
        firebase_auth_uid: str,
        package_name: str,
        product_id: str,
        subscription_state: str,
        acknowledgement_state: str,
        expires_at: datetime,
    ) -> None:
        """Grava somente dados ja verificados na API Google Play.

        Nunca transfere uma compra existente para outro UID. O conflito e
        tratado atomicamente pelo PostgreSQL, inclusive sob concorrencia.
        """
        token_hash = self._token_hash(purchase_token)
        uid = self._required(firebase_auth_uid, "firebase_auth_uid")
        package = self._required(package_name, "package_name")
        product = self._required(product_id, "product_id")
        state = self._required(subscription_state, "subscription_state")
        acknowledgement = self._required(acknowledgement_state, "acknowledgement_state")
        if not isinstance(expires_at, datetime) or expires_at.tzinfo is None:
            raise ValueError("expires_at deve conter fuso horario")
        expiry = expires_at.astimezone(timezone.utc)

        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (
                        scope_key, purchase_token_hash, firebase_auth_uid,
                        package_name, product_id, subscription_state,
                        acknowledgement_state, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (scope_key, purchase_token_hash)
                    DO UPDATE SET
                        product_id = EXCLUDED.product_id,
                        subscription_state = EXCLUDED.subscription_state,
                        acknowledgement_state = EXCLUDED.acknowledgement_state,
                        expires_at = EXCLUDED.expires_at,
                        verified_at = NOW()
                    WHERE {self.TABLE_NAME}.firebase_auth_uid = EXCLUDED.firebase_auth_uid
                      AND {self.TABLE_NAME}.package_name = EXCLUDED.package_name
                    RETURNING id
                    """,
                    (
                        self._scope_key, token_hash, uid, package, product,
                        state, acknowledgement, expiry,
                    ),
                )
                if cursor.fetchone() is None:
                    raise PurchaseTokenAlreadyClaimedError(
                        "Compra ja vinculada a outra identidade ou aplicativo"
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()

    def load_by_token(self, purchase_token: str) -> StoredGooglePlaySubscription | None:
        """Consulta interna; nao deve ser exposta diretamente ao aplicativo."""
        token_hash = self._token_hash(purchase_token)
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    f"""
                    SELECT firebase_auth_uid, product_id, subscription_state,
                           acknowledgement_state, expires_at
                    FROM {self.TABLE_NAME}
                    WHERE scope_key = %s AND purchase_token_hash = %s
                    """,
                    (self._scope_key, token_hash),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()
        if row is None:
            return None
        return StoredGooglePlaySubscription(*row)

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory(self._database_url)
        import psycopg
        return psycopg.connect(self._database_url)

    @staticmethod
    def _required(value: str, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} obrigatorio")
        return value.strip()

    @classmethod
    def _token_hash(cls, purchase_token: str) -> str:
        token = cls._required(purchase_token, "purchase_token")
        return sha256(token.encode("utf-8")).hexdigest()
