"""Atomic consumption; database clock controls expiration."""
class PostgreSQLFcmChallengeStore:
    def __init__(self, *, database_url, scope_key, connection_factory=None):
        self._url = database_url.strip()
        self._scope = scope_key.strip()
        self._factory = connection_factory
        if not self._url or not self._scope:
            raise ValueError('Configuracao incompleta.')

    def _execute(self, sql, values, *, returning=False):
        if self._factory is None:
            import psycopg
            connection = psycopg.connect(self._url)
        else:
            connection = self._factory(self._url)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(sql, values)
                result = cursor.fetchone() is not None if returning else None
                connection.commit()
                return result
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()

    def create(self, *, challenge_id, uid, destination_hash, proof_hash, ttl_seconds):
        self._execute('''INSERT INTO cryptoradar_fcm_possession_challenges
            (scope_key, challenge_id, firebase_auth_uid, destination_hash, proof_hash, expires_at)
            VALUES (%s, %s, %s, %s, %s, NOW() + %s * INTERVAL '1 second')''',
            (self._scope, challenge_id, uid, destination_hash, proof_hash, ttl_seconds))

    def consume(self, *, challenge_id, uid, destination_hash, proof_hash):
        return self._execute('''DELETE FROM cryptoradar_fcm_possession_challenges
            WHERE scope_key = %s AND challenge_id = %s AND firebase_auth_uid = %s
              AND destination_hash = %s AND proof_hash = %s AND expires_at > NOW()
            RETURNING challenge_id''', (self._scope, challenge_id, uid, destination_hash, proof_hash), returning=True)

    def discard(self, challenge_id):
        self._execute('''DELETE FROM cryptoradar_fcm_possession_challenges
            WHERE scope_key = %s AND challenge_id = %s''', (self._scope, challenge_id))
