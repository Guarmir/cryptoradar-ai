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

    def recover_or_create_owned_device(self, *, installation_id: str,
                                       firebase_auth_uid: str, fcm_token: str,
                                       firebase_installation_id: str | None):
        """Called only after fresh possession proof. Never transfer ownership."""
        from hashlib import sha256
        lock_key = sha256((self._scope_key + "\0" + fcm_token).encode()).hexdigest()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                               (lock_key,))
                cursor.execute('''SELECT d.installation_id, o.firebase_auth_uid,
                    d.firebase_installation_id, d.enabled
                    FROM cryptoradar_push_devices d
                    JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key = d.scope_key AND o.installation_id = d.installation_id
                    WHERE d.scope_key = %s AND d.fcm_token = %s
                    FOR UPDATE OF d, o''', (self._scope_key, fcm_token))
                rows = cursor.fetchall()
                if rows:
                    if (len(rows) != 1 or rows[0][1] != firebase_auth_uid
                            or rows[0][2] != firebase_installation_id or rows[0][3] is not True):
                        raise ValueError('Destino ja vinculado ou indisponivel.')
                    recovered = rows[0][0]
                    connection.commit()
                    return recovered
                cursor.execute('''INSERT INTO cryptoradar_push_devices
                    (scope_key, installation_id, fcm_token, firebase_installation_id,
                     platform, enabled, updated_at)
                    VALUES (%s, %s, %s, %s, 'android', TRUE, NOW())''',
                    (self._scope_key, installation_id, fcm_token, firebase_installation_id))
                cursor.execute('''INSERT INTO cryptoradar_push_installation_owners
                    (scope_key, installation_id, firebase_auth_uid) VALUES (%s, %s, %s)''',
                    (self._scope_key, installation_id, firebase_auth_uid))
                connection.commit()
                return installation_id
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()

    def rotate_owned_device(self, *, installation_id, firebase_auth_uid,
                            fcm_token, firebase_installation_id):
        """Only after fresh FCM proof; preserve the original owner and grant."""
        from hashlib import sha256
        lock_key = sha256((self._scope_key + "\0" + fcm_token).encode()).hexdigest()
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                               (lock_key,))
                cursor.execute('''SELECT o.firebase_auth_uid, d.firebase_installation_id, d.enabled
                    FROM cryptoradar_push_devices d
                    JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key=d.scope_key AND o.installation_id=d.installation_id
                    WHERE d.scope_key=%s AND d.installation_id=%s
                    FOR UPDATE OF d, o''', (self._scope_key, installation_id))
                row = cursor.fetchone()
                if (row is None or row[0] != firebase_auth_uid or row[2] is not True
                        or not firebase_installation_id or row[1] != firebase_installation_id):
                    raise ValueError('Vinculacao indisponivel.')
                cursor.execute('''SELECT d.installation_id FROM cryptoradar_push_devices d
                    JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key=d.scope_key AND o.installation_id=d.installation_id
                    WHERE d.scope_key=%s AND d.fcm_token=%s AND d.installation_id<>%s''',
                    (self._scope_key, fcm_token, installation_id))
                if cursor.fetchone() is not None:
                    raise ValueError('Destino ja vinculado.')
                cursor.execute('''UPDATE cryptoradar_push_devices
                    SET fcm_token=%s, updated_at=NOW()
                    WHERE scope_key=%s AND installation_id=%s RETURNING installation_id''',
                    (fcm_token, self._scope_key, installation_id))
                if cursor.fetchone() != (installation_id,):
                    raise ValueError('Vinculacao indisponivel.')
                connection.commit()
                return installation_id
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()

    def detach_owned_device(self, *, installation_id, firebase_auth_uid):
        """Remove only this installation; ownership and grants cascade, not the account."""
        connection = self._connect()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute('''SELECT d.installation_id, o.firebase_auth_uid
                    FROM cryptoradar_push_devices d
                    LEFT JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key=d.scope_key AND o.installation_id=d.installation_id
                    WHERE d.scope_key=%s AND d.installation_id=%s FOR UPDATE OF d''',
                    (self._scope_key, installation_id))
                row = cursor.fetchone()
                if row is not None:
                    if row[1] != firebase_auth_uid:
                        raise ValueError('Vinculacao indisponivel.')
                    cursor.execute('''DELETE FROM cryptoradar_push_devices
                        WHERE scope_key=%s AND installation_id=%s RETURNING installation_id''',
                        (self._scope_key, installation_id))
                    if cursor.fetchone() != (installation_id,):
                        raise ValueError('Vinculacao indisponivel.')
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()
