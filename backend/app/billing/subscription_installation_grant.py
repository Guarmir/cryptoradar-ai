"""Authenticated, bounded installation entitlement. No acknowledgement yet."""
import os
from hashlib import sha256
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field


class GrantRequest(BaseModel):
    installation_id: str = Field(min_length=1, max_length=200)
    purchase_token: str = Field(min_length=1, max_length=8192)


class GrantResponse(BaseModel):
    status: Literal['authorization_registered'] = 'authorization_registered'
    pro_granted: Literal[False] = False


class InstallationGrantStore:
    def __init__(self, *, database_url, push_scope, subscription_scope, package_name, connection_factory=None):
        self.url = database_url
        self.push_scope = push_scope
        self.subscription_scope = subscription_scope
        self.package = package_name
        self.factory = connection_factory
        if not all((database_url, push_scope, subscription_scope, package_name)):
            raise ValueError('Configuracao incompleta.')

    def register(self, *, uid, installation_id, purchase_token):
        token_hash = sha256(purchase_token.encode('utf-8')).hexdigest()
        if self.factory is None:
            import psycopg
            connection = psycopg.connect(self.url)
        else:
            connection = self.factory(self.url)
        try:
            cursor = connection.cursor()
            try:
                # Recheck persisted ownership and purchase atomically with the write.
                cursor.execute('''INSERT INTO cryptoradar_subscription_installation_grants AS grants
                    (push_scope, installation_id, firebase_auth_uid, subscription_scope,
                     purchase_token_hash, valid_until)
                    SELECT o.scope_key, o.installation_id, o.firebase_auth_uid, s.scope_key,
                           s.purchase_token_hash, LEAST(s.expires_at, NOW() + INTERVAL '15 minutes')
                    FROM cryptoradar_push_installation_owners o
                    JOIN cryptoradar_google_play_subscriptions s ON s.firebase_auth_uid = o.firebase_auth_uid
                    WHERE o.scope_key = %s AND o.installation_id = %s AND o.firebase_auth_uid = %s
                      AND s.scope_key = %s AND s.purchase_token_hash = %s AND s.package_name = %s
                      AND s.product_id = 'cryptoradar_pro_monthly' AND s.expires_at > NOW()
                      AND s.verified_at > NOW() - INTERVAL '1 minute'
                      AND s.subscription_state IN ('SUBSCRIPTION_STATE_ACTIVE',
                          'SUBSCRIPTION_STATE_IN_GRACE_PERIOD', 'SUBSCRIPTION_STATE_CANCELED')
                      AND s.acknowledgement_state IN ('ACKNOWLEDGEMENT_STATE_PENDING',
                          'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED')
                    ON CONFLICT (push_scope, installation_id) DO UPDATE SET
                        subscription_scope = EXCLUDED.subscription_scope,
                        purchase_token_hash = EXCLUDED.purchase_token_hash,
                        valid_until = EXCLUDED.valid_until
                    WHERE grants.firebase_auth_uid = EXCLUDED.firebase_auth_uid
                    RETURNING valid_until''', (self.push_scope, installation_id, uid,
                    self.subscription_scope, token_hash, self.package))
                row = cursor.fetchone()
                if row is None:
                    connection.rollback()
                    return False
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()
        finally:
            connection.close()


class InstallationGrantService:
    def __init__(self, *, authorizer, claim_service, entitlement_service, grant_store):
        self.authorizer = authorizer
        self.claim_service = claim_service
        self.entitlement_service = entitlement_service
        self.grant_store = grant_store

    def register(self, request, authorization):
        installation = request.installation_id.strip()
        token = request.purchase_token.strip()
        if not installation or not token:
            raise HTTPException(status_code=422, detail='Dados invalidos.')
        uid = self.authorizer.authorize(authorization=authorization, installation_id=installation)
        # Refresh the verified snapshot, then require a live entitlement decision.
        self.claim_service.claim(authorization=authorization, purchase_token=token)
        decision = self.entitlement_service.evaluate(authorization=authorization, purchase_token=token)
        if decision.eligible is not True:
            raise HTTPException(status_code=409, detail='Assinatura indisponivel para autorizacao.')
        if self.grant_store.register(uid=uid, installation_id=installation, purchase_token=token) is not True:
            raise HTTPException(status_code=409, detail='Autorizacao indisponivel.')
        return GrantResponse()


def create_grant_service():
    if os.getenv('GOOGLE_PLAY_INSTALLATION_GRANT_ENABLED', '').strip().lower() != 'true':
        raise HTTPException(status_code=503, detail='Autorizacao indisponivel.')
    from app.access.access_api_config import AccessApiConfig
    from app.push.push_registration_config import PushRegistrationConfig
    from app.push.firebase_identity_verifier import FirebaseIdentityVerifier
    from app.push.push_installation_authorizer import PushInstallationAuthorizer
    from app.push.postgresql_push_installation_owner_store import PostgreSQLPushInstallationOwnerStore
    from app.billing.google_play_subscription_claim_service import GooglePlaySubscriptionClaimService
    from app.billing.google_play_subscription_verifier import GooglePlaySubscriptionVerifier
    from app.billing.postgresql_google_play_subscription_store import PostgreSQLGooglePlaySubscriptionStore
    from app.billing.subscription_entitlement_service import SubscriptionEntitlementService
    access = AccessApiConfig.from_environment()
    push = PushRegistrationConfig.from_environment()
    scope = os.getenv('GOOGLE_PLAY_SUBSCRIPTION_SCOPE_KEY', '').strip()
    package = os.getenv('GOOGLE_PLAY_PACKAGE_NAME', '').strip()
    if (os.getenv('GOOGLE_PLAY_CLAIM_ENABLED', '').strip().lower() != 'true'
            or not access.enabled or not push.enabled or not access.database_url
            or access.database_url != push.database_url or not push.scope_key or not scope or not package):
        raise HTTPException(status_code=503, detail='Autorizacao indisponivel.')
    identity = FirebaseIdentityVerifier()
    verifier = GooglePlaySubscriptionVerifier(package_name=package, product_id='cryptoradar_pro_monthly')
    store = PostgreSQLGooglePlaySubscriptionStore(database_url=access.database_url, scope_key=scope)
    return InstallationGrantService(
        authorizer=PushInstallationAuthorizer(identity_verifier=identity,
            owner_store=PostgreSQLPushInstallationOwnerStore(database_url=push.database_url, scope_key=push.scope_key)),
        claim_service=GooglePlaySubscriptionClaimService(identity_verifier=identity, subscription_verifier=verifier,
            subscription_store=store, package_name=package),
        entitlement_service=SubscriptionEntitlementService(identity_verifier=identity, subscription_verifier=verifier,
            subscription_store=store),
        grant_store=InstallationGrantStore(database_url=access.database_url, push_scope=push.scope_key,
            subscription_scope=scope, package_name=package))


def register_installation_grant(request, authorization, service=None):
    from app.billing.google_play_subscription_claim_service import PurchaseIdentityMismatchError, PurchaseNotEntitledError
    from app.billing.postgresql_google_play_subscription_store import PurchaseTokenAlreadyClaimedError
    from app.billing.google_play_subscription_verifier import GooglePlaySubscriptionVerificationError
    try:
        return (service if service is not None else create_grant_service()).register(request, authorization)
    except HTTPException:
        raise
    except PurchaseIdentityMismatchError:
        raise HTTPException(status_code=403, detail='Compra nao vinculada a conta.') from None
    except (PurchaseNotEntitledError, PurchaseTokenAlreadyClaimedError):
        raise HTTPException(status_code=409, detail='Assinatura indisponivel.') from None
    except GooglePlaySubscriptionVerificationError:
        raise HTTPException(status_code=502, detail='Verificacao indisponivel.') from None
    except Exception:
        raise HTTPException(status_code=503, detail='Autorizacao temporariamente indisponivel.') from None
