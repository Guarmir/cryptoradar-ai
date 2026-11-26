"""Atomic insertion of a new Android device and its owner, without upsert.

This store is intentionally not connected to public routes yet.
"""
class PostgreSQLAuthenticatedInstallationStore:
    def __init__(self, *, database_url: str, scope_key: str, connection_factory=None):
        self._database_url = database_url.strip()
        self._scope_key = scope_key.strip()
        if not self._database_url or not self._scope_key:
            raise ValueError('Configuracao de instalacao incompleta')
        self._factory = connection_factory

    def _connect(self):
        if self._factory is not None:
            return self._factory(self._database_url)
        import psycopg
        return psycopg.connect(self._database_url)

    def create_owned_device(self, *, installation_id: str, firebase_auth_uid: str,
                            fcm_token: str, firebase_installation_id: str | None):
        # Both rows must be committed together. A conflict never transfers ownership.
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    '''INSERT INTO cryptoradar_push_devices
                       (scope_key, installation_id, fcm_token, firebase_installation_id,
                        platform, enabled, updated_at)
                       VALUES (%s, %s, %s, %s, 'android', TRUE, NOW())''',
                    (self._scope_key, installation_id, fcm_token, firebase_installation_id),
                )
                cursor.execute(
                    '''INSERT INTO cryptoradar_push_installation_owners
                       (scope_key, installation_id, firebase_auth_uid)
                       VALUES (%s, %s, %s)''',
                    (self._scope_key, installation_id, firebase_auth_uid),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()
