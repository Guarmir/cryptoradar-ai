"""Server-side revalidation of stored purchases; never acknowledges or creates grants."""
import os
from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest

PRODUCT = 'cryptoradar_pro_monthly'
ACK = 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
STATES = ('SUBSCRIPTION_STATE_ACTIVE', 'SUBSCRIPTION_STATE_IN_GRACE_PERIOD',
          'SUBSCRIPTION_STATE_CANCELED')


def token_cipher():
    from cryptography.fernet import Fernet
    return Fernet(os.environ['GOOGLE_PLAY_REFRESH_ENCRYPTION_KEY'].strip().encode('ascii'))


def retain_token(cursor, *, scope, package, uid, token, cipher):
    """Call inside the successful grant transaction only; no plaintext in SQL."""
    digest = sha256(token.encode('utf-8')).hexdigest()
    encrypted = cipher.encrypt(token.encode('utf-8')).decode('ascii')
    cursor.execute('''INSERT INTO cryptoradar_subscription_refresh_tokens AS r
        (subscription_scope, package_name, purchase_token_hash, firebase_auth_uid, encrypted_token)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (subscription_scope, package_name, purchase_token_hash)
        DO UPDATE SET encrypted_token = EXCLUDED.encrypted_token
        WHERE r.firebase_auth_uid = EXCLUDED.firebase_auth_uid
        RETURNING purchase_token_hash''', (scope, package, digest, uid, encrypted))
    if cursor.fetchone() is None:
        raise ValueError('Refresh ownership mismatch.')


def eligible_snapshot(verified, uid, now):
    account = verified.obfuscated_account_id
    if not isinstance(account, str) or not account.isascii():
        return False
    return (compare_digest(account, sha256(uid.encode('utf-8')).hexdigest())
            and verified.product_id == PRODUCT and not verified.linked_purchase_token
            and verified.entitled_now is True and verified.state in STATES
            and verified.acknowledgement_state == ACK
            and isinstance(verified.expires_at, datetime)
            and verified.expires_at.utcoffset() is not None and verified.expires_at > now)


class SubscriptionLifecycle:
    def __init__(self, *, database_url, scope, package, verifier, cipher,
                 connection_factory=None, now_provider=None):
        if not all((database_url, scope, package)):
            raise ValueError('Incomplete refresh configuration.')
        self.url, self.scope, self.package = database_url, scope, package
        self.verifier, self.cipher = verifier, cipher
        self.factory = connection_factory
        self.now = now_provider or (lambda: datetime.now(timezone.utc))

    def _connect(self):
        if self.factory is not None:
            return self.factory(self.url)
        import psycopg
        return psycopg.connect(self.url)

    def refresh_one(self):
        """Process one due token. Locks avoid overlapping workers; errors never extend access.

        A successfully verified negative decision revokes the matching grants.
        Transient errors leave existing bounded grants untouched until expiry.
        """
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute('''SELECT purchase_token_hash, firebase_auth_uid, encrypted_token
                    FROM cryptoradar_subscription_refresh_tokens
                    WHERE subscription_scope=%s AND package_name=%s AND next_check_at <= NOW()
                    ORDER BY next_check_at, purchase_token_hash LIMIT 1 FOR UPDATE SKIP LOCKED''',
                    (self.scope, self.package))
                row = cursor.fetchone()
                if row is None:
                    connection.commit()
                    return 'idle'
                digest, uid, encrypted = row
                try:
                    token = self.cipher.decrypt(encrypted.encode('ascii')).decode('utf-8')
                    if not compare_digest(sha256(token.encode('utf-8')).hexdigest(), digest):
                        raise ValueError('Token mismatch.')
                    verified = self.verifier.verify(token)
                    eligible = eligible_snapshot(verified, uid, self.now())
                except Exception:
                    self._schedule(cursor, digest, 60)
                    connection.commit()
                    return 'retry'
                # Never update a purchase belonging to a different UID or package.
                if eligible:
                    cursor.execute('''UPDATE cryptoradar_google_play_subscriptions
                        SET subscription_state=%s, acknowledgement_state=%s, expires_at=%s, verified_at=NOW()
                        WHERE scope_key=%s AND package_name=%s AND purchase_token_hash=%s
                          AND firebase_auth_uid=%s AND product_id=%s RETURNING purchase_token_hash''',
                        (verified.state, verified.acknowledgement_state, verified.expires_at,
                         self.scope, self.package, digest, uid, PRODUCT))
                    eligible = cursor.fetchone() is not None
                if eligible:
                    cursor.execute('''UPDATE cryptoradar_subscription_installation_grants g
                        SET valid_until=LEAST(%s, NOW()+INTERVAL '15 minutes')
                        WHERE g.subscription_scope=%s AND g.purchase_token_hash=%s AND g.firebase_auth_uid=%s
                          AND EXISTS (SELECT 1 FROM cryptoradar_push_installation_owners o
                              WHERE o.scope_key=g.push_scope AND o.installation_id=g.installation_id
                              AND o.firebase_auth_uid=g.firebase_auth_uid)''',
                        (verified.expires_at, self.scope, digest, uid))
                else:
                    cursor.execute('''UPDATE cryptoradar_subscription_installation_grants
                        SET valid_until=LEAST(valid_until,NOW())
                        WHERE subscription_scope=%s AND purchase_token_hash=%s AND firebase_auth_uid=%s''',
                        (self.scope, digest, uid))
                self._schedule(cursor, digest, 300)
                connection.commit()
                return 'renewed' if eligible else 'revoked'
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _schedule(self, cursor, digest, seconds):
        cursor.execute('''UPDATE cryptoradar_subscription_refresh_tokens
            SET next_check_at=NOW()+(%s * INTERVAL '1 second')
            WHERE subscription_scope=%s AND package_name=%s AND purchase_token_hash=%s''',
            (seconds, self.scope, self.package, digest))

    def run_batch(self, limit=20):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError('Invalid batch size.')
        counts = {'renewed': 0, 'revoked': 0, 'retry': 0}
        for _ in range(limit):
            outcome = self.refresh_one()
            if outcome == 'idle':
                break
            counts[outcome] += 1
        return counts


def create_subscription_lifecycle():
    """Explicit opt-in for the future worker; never run at import/startup."""
    from app.access.access_api_config import AccessApiConfig
    from app.billing.google_play_subscription_verifier import GooglePlaySubscriptionVerifier
    from app.push.push_registration_config import PushRegistrationConfig
    flags = ('GOOGLE_PLAY_REFRESH_ENABLED', 'GOOGLE_PLAY_CLAIM_ENABLED',
             'GOOGLE_PLAY_INSTALLATION_GRANT_ENABLED', 'GOOGLE_PLAY_INSTALLATION_ACCESS_ENABLED')
    if any(os.getenv(flag, '').strip().lower() != 'true' for flag in flags):
        raise RuntimeError('Subscription refresh disabled.')
    access = AccessApiConfig.from_environment()
    push = PushRegistrationConfig.from_environment()
    scope = os.getenv('GOOGLE_PLAY_SUBSCRIPTION_SCOPE_KEY', '').strip()
    package = os.getenv('GOOGLE_PLAY_PACKAGE_NAME', '').strip()
    if (not access.enabled or not push.enabled or not access.database_url
            or access.database_url != push.database_url or not push.scope_key or not scope or not package):
        raise RuntimeError('Subscription refresh configuration incomplete.')
    return SubscriptionLifecycle(database_url=access.database_url, scope=scope, package=package,
        verifier=GooglePlaySubscriptionVerifier(package_name=package, product_id=PRODUCT),
        cipher=token_cipher())
