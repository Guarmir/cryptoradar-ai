"""Account-scoped watchlist storage. Callers must authenticate the UID.

No HTTP routes or background workers are enabled by this module.
All additions serialize by account across installations and processes.
"""
from dataclasses import dataclass
import json

from app.monitoring.individual_monitoring_intent import MonitoringIntent


class IndividualMonitoringLimitReached(ValueError):
    pass


@dataclass(frozen=True)
class IndividualMonitoringAsset:
    coin_id: str
    symbol: str

    def __post_init__(self):
        object.__setattr__(self, 'coin_id', _normalize(self.coin_id, 200).lower())
        object.__setattr__(self, 'symbol', _normalize(self.symbol, 50).upper())
        if len(self.coin_id) > 200 or len(self.symbol) > 50:
            raise ValueError('Identificador de ativo invalido.')


def _normalize(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum or '\x00' in value:
        raise ValueError('Identificador invalido.')
    return value.strip()


class PostgreSQLIndividualMonitoringStore:
    def __init__(self, *, database_url, scope_key, connection_factory=None):
        self._url = _normalize(database_url, 10000)
        self._scope = _normalize(scope_key, 200)
        self._factory = connection_factory

    def _connect(self):
        if self._factory is not None:
            return self._factory(self._url)
        import psycopg
        return psycopg.connect(self._url)

    def _account(self, uid):
        return self._scope, _normalize(uid, 128)

    @staticmethod
    def _lock(cursor, account):
        key = json.dumps(('individual-monitoring', *account), ensure_ascii=True)
        cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (key,))

    def load_all(self, *, uid):
        account = self._account(uid)
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''SELECT coin_id, symbol
                    FROM cryptoradar_individual_monitoring_assets
                    WHERE scope_key = %s AND firebase_auth_uid = %s
                    ORDER BY created_at, coin_id''', account)
                return tuple(IndividualMonitoringAsset(*row) for row in cursor.fetchall())
        finally:
            connection.close()

    def add(self, *, uid, asset, limit):
        """Idempotent by canonical ID. Limit must come from trusted server policy."""
        account = self._account(uid)
        if not isinstance(asset, IndividualMonitoringAsset):
            raise TypeError('Ativo invalido.')
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Limite invalido.')
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                self._lock(cursor, account)
                cursor.execute('''SELECT symbol FROM cryptoradar_individual_monitoring_assets
                    WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s''',
                    (*account, asset.coin_id))
                existing = cursor.fetchone()
                if existing is not None:
                    result = IndividualMonitoringAsset(asset.coin_id, existing[0])
                else:
                    cursor.execute('''SELECT COUNT(*) FROM cryptoradar_individual_monitoring_assets
                        WHERE scope_key = %s AND firebase_auth_uid = %s''', account)
                    if cursor.fetchone()[0] >= limit:
                        raise IndividualMonitoringLimitReached('Limite de ativos atingido.')
                    cursor.execute('''INSERT INTO cryptoradar_individual_monitoring_assets
                        (scope_key, firebase_auth_uid, coin_id, symbol) VALUES (%s, %s, %s, %s)''',
                        (*account, asset.coin_id, asset.symbol))
                    result = asset
            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def remove(self, *, uid, coin_id):
        account = self._account(uid)
        coin_id = _normalize(coin_id, 200).lower()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                self._lock(cursor, account)
                cursor.execute('''DELETE FROM cryptoradar_individual_monitoring_assets
                    WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s''',
                    (*account, coin_id))
                removed = cursor.rowcount == 1
            connection.commit()
            return removed
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def load_intent(self, *, uid, coin_id):
        account = self._account(uid)
        coin_id = _normalize(coin_id, 200).lower()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT intent, position_side
                    FROM cryptoradar_individual_monitoring_assets
                    WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s""",
                    (*account, coin_id))
                row = cursor.fetchone()
                return None if row is None else MonitoringIntent(*row)
        finally:
            connection.close()

    def save_intent(self, *, uid, coin_id, intent):
        if not isinstance(intent, MonitoringIntent):
            raise TypeError('Intencao invalida.')
        account = self._account(uid)
        coin_id = _normalize(coin_id, 200).lower()
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                self._lock(cursor, account)
                cursor.execute("""UPDATE cryptoradar_individual_monitoring_assets
                    SET intent = %s, position_side = %s
                    WHERE scope_key = %s AND firebase_auth_uid = %s AND coin_id = %s""",
                    (intent.intent, intent.side, *account, coin_id))
                updated = cursor.rowcount == 1
            connection.commit()
            return updated
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
