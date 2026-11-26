"""Read-only account-scoped snapshot. Never grants access."""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Any


@dataclass(frozen=True)
class SubscriptionSnapshot:
    state: str
    expires_at: datetime
    acknowledgement_state: str
    verified_at: datetime


class SubscriptionStatusStore:
    def __init__(self, *, database_url: str, scope_key: str, package_name: str,
                 connection_factory: Callable[[str], Any] | None = None):
        self._database_url = database_url.strip()
        self._scope = scope_key.strip()
        self._package = package_name.strip()
        self._connect_factory = connection_factory
        if not all((self._database_url, self._scope, self._package)):
            raise ValueError("Configuracao de assinatura incompleta.")

    def load_candidate(self, uid: str) -> SubscriptionSnapshot | None:
        if not uid.strip():
            raise ValueError("UID obrigatorio.")
        if self._connect_factory is None:
            import psycopg
            connection = psycopg.connect(self._database_url)
        else:
            connection = self._connect_factory(self._database_url)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    SELECT subscription_state, expires_at, acknowledgement_state, verified_at
                    FROM cryptoradar_google_play_subscriptions
                    WHERE scope_key = %s AND firebase_auth_uid = %s
                      AND package_name = %s AND product_id = %s
                      AND expires_at > NOW()
                      AND subscription_state IN (%s, %s, %s)
                    ORDER BY expires_at DESC, verified_at DESC
                    LIMIT 1
                    """,
                    (self._scope, uid.strip(), self._package,
                     "cryptoradar_pro_monthly", "SUBSCRIPTION_STATE_ACTIVE",
                     "SUBSCRIPTION_STATE_IN_GRACE_PERIOD", "SUBSCRIPTION_STATE_CANCELED"),
                )
                row = cursor.fetchone()
            finally:
                cursor.close()
        finally:
            connection.close()
        return SubscriptionSnapshot(*row) if row is not None else None
