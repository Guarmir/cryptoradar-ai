"""Read bounded subscription grants for a verified installation owner.

Never upgrades the legacy access plan or trusts an installation ID alone.
"""
import os

from fastapi import HTTPException


class InstallationGrantReader:
    def __init__(self, *, database_url, push_scope, subscription_scope,
                 package_name, connection_factory=None):
        if not all((database_url, push_scope, subscription_scope, package_name)):
            raise ValueError('Configuracao incompleta.')
        self.url = database_url
        self.push_scope = push_scope
        self.subscription_scope = subscription_scope
        self.package = package_name
        self.factory = connection_factory

    def has_access(self, *, installation_id, uid):
        if self.factory is None:
            import psycopg
            connection = psycopg.connect(self.url)
        else:
            connection = self.factory(self.url)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute('''SELECT EXISTS (
                    SELECT 1 FROM cryptoradar_subscription_installation_grants g
                    JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key = g.push_scope
                     AND o.installation_id = g.installation_id
                     AND o.firebase_auth_uid = g.firebase_auth_uid
                    JOIN cryptoradar_google_play_subscriptions s
                      ON s.scope_key = g.subscription_scope
                     AND s.purchase_token_hash = g.purchase_token_hash
                     AND s.firebase_auth_uid = g.firebase_auth_uid
                    WHERE g.push_scope = %s AND g.installation_id = %s
                      AND g.firebase_auth_uid = %s AND g.subscription_scope = %s
                      AND s.package_name = %s
                      AND s.product_id = 'cryptoradar_pro_monthly'
                      AND g.valid_until > NOW() AND s.expires_at > NOW()
                      AND s.verified_at > NOW() - INTERVAL '15 minutes'
                      AND s.subscription_state IN ('SUBSCRIPTION_STATE_ACTIVE',
                          'SUBSCRIPTION_STATE_IN_GRACE_PERIOD', 'SUBSCRIPTION_STATE_CANCELED')
                      AND s.acknowledgement_state IN ('ACKNOWLEDGEMENT_STATE_PENDING',
                          'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'))''',
                    (self.push_scope, installation_id, uid,
                     self.subscription_scope, self.package))
                row = cursor.fetchone()
                return bool(row and row[0] is True)
            finally:
                cursor.close()
        finally:
            connection.close()


class InstallationAccessService:
    def __init__(self, *, authorizer, grant_reader, entitlements_config):
        self.authorizer = authorizer
        self.reader = grant_reader
        self.config = entitlements_config

    def resolve(self, *, authorization, installation_id):
        from app.access.access_api import AccessEntitlementsResponse
        installation_id = installation_id.strip()
        if not installation_id or len(installation_id) > 200:
            raise HTTPException(status_code=422, detail='Instalacao invalida.')
        uid = self.authorizer.authorize(authorization=authorization,
                                        installation_id=installation_id)
        granted = self.reader.has_access(installation_id=installation_id, uid=uid)
        rights = self.config.pro if granted is True else self.config.free
        return AccessEntitlementsResponse(
            plan='pro' if granted is True else 'free',
            monitored_asset_limit=rights.monitored_asset_limit,
            automatic_market_alerts=rights.automatic_market_alerts,
            futures_enabled=rights.futures_enabled)


def create_installation_access_service():
    # Explicit opt-in, separate from registering grants.
    if any(os.getenv(flag, '').strip().lower() != 'true' for flag in (
        'GOOGLE_PLAY_INSTALLATION_ACCESS_ENABLED', 'GOOGLE_PLAY_INSTALLATION_GRANT_ENABLED',
        'GOOGLE_PLAY_CLAIM_ENABLED')):
        raise HTTPException(status_code=503, detail='Acesso comercial indisponivel.')
    from app.access.access_api_config import AccessApiConfig
    from app.access.access_entitlements_config import AccessEntitlementsConfig
    from app.push.push_registration_config import PushRegistrationConfig
    from app.push.firebase_identity_verifier import FirebaseIdentityVerifier
    from app.push.push_installation_authorizer import PushInstallationAuthorizer
    from app.push.postgresql_push_installation_owner_store import PostgreSQLPushInstallationOwnerStore
    access = AccessApiConfig.from_environment()
    push = PushRegistrationConfig.from_environment()
    scope = os.getenv('GOOGLE_PLAY_SUBSCRIPTION_SCOPE_KEY', '').strip()
    package = os.getenv('GOOGLE_PLAY_PACKAGE_NAME', '').strip()
    if (not access.enabled or not push.enabled or not access.database_url
            or access.database_url != push.database_url or not push.scope_key
            or not scope or not package):
        raise HTTPException(status_code=503, detail='Acesso comercial indisponivel.')
    return InstallationAccessService(
        authorizer=PushInstallationAuthorizer(identity_verifier=FirebaseIdentityVerifier(),
            owner_store=PostgreSQLPushInstallationOwnerStore(database_url=access.database_url,
                                                             scope_key=push.scope_key)),
        grant_reader=InstallationGrantReader(database_url=access.database_url,
            push_scope=push.scope_key, subscription_scope=scope, package_name=package),
        entitlements_config=AccessEntitlementsConfig.from_environment())


def get_installation_access(installation_id, authorization, service=None):
    try:
        effective = service if service is not None else create_installation_access_service()
        return effective.resolve(authorization=authorization, installation_id=installation_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail='Acesso temporariamente indisponivel.') from None
