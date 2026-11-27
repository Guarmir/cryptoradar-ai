"""Connect acknowledgement to the exact persisted installation grant.

Activation requires explicit operational acceptance of every advertised benefit.
This flag is NOT evidence that the mobile features have been implemented.
"""
import os
from datetime import datetime, timezone

from fastapi import HTTPException

from app.billing.google_play_subscription_acknowledger import GooglePlaySubscriptionAcknowledger
from app.billing.subscription_acknowledgement_service import SubscriptionAcknowledgementService
from app.billing.subscription_installation_access import create_installation_access_service
from app.billing.subscription_lifecycle import token_cipher

REQUIRED_FLAGS = (
    'GOOGLE_PLAY_COMMERCIAL_FULFILLMENT_ENABLED',
    'GOOGLE_PLAY_INSTALLATION_ACCESS_ENABLED',
    'GOOGLE_PLAY_INSTALLATION_GRANT_ENABLED',
    'GOOGLE_PLAY_CLAIM_ENABLED',
    'GOOGLE_PLAY_REFRESH_ENABLED',
    'GOOGLE_PLAY_MONITORING_ACCESS_ENABLED',
    'CRYPTORADAR_AUTHENTICATED_ENROLLMENT_ENABLED',
    'CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED',
    'CRYPTORADAR_INDIVIDUAL_MONITORING_RUNTIME_ENABLED',
    'CRYPTORADAR_INDIVIDUAL_ALERTS_ENABLED',
)


class GrantAcknowledgement:
    def __init__(self, *, identity, verifier, store, acknowledger, access, package):
        self.identity = identity
        self.verifier = verifier
        self.store = store
        self.acknowledger = acknowledger
        self.access = access
        self.package = package

    def __call__(self, *, authorization, installation_id, uid, purchase_token):
        def ensure_entitlement(verified_uid, token, snapshot):
            if verified_uid != uid or token != purchase_token:
                return False
            expiry = snapshot.expires_at
            if (not isinstance(expiry, datetime) or expiry.utcoffset() is None
                    or expiry <= datetime.now(timezone.utc)):
                return False
            if self.access.authorizer.authorize(authorization=authorization,
                                                installation_id=installation_id) != uid:
                return False
            return self.access.reader.has_access(installation_id=installation_id,
                                                  uid=uid, purchase_token=token) is True

        service = SubscriptionAcknowledgementService(identity_verifier=self.identity,
            subscription_verifier=self.verifier, subscription_store=self.store,
            acknowledger=self.acknowledger, ensure_entitlement=ensure_entitlement,
            package_name=self.package)
        service.acknowledge(authorization=authorization, purchase_token=purchase_token)


def create_grant_acknowledgement(*, identity, verifier, store, package,
                                 database_url, push_scope, subscription_scope):
    if any(os.getenv(flag, '').strip().lower() != 'true' for flag in REQUIRED_FLAGS):
        raise HTTPException(503, 'Contratacao indisponivel.')
    token_cipher()  # Fail before issuing grants if encryption is not configured.
    access = create_installation_access_service()
    reader = access.reader
    if (reader.url, reader.push_scope, reader.subscription_scope, reader.package) != (
            database_url, push_scope, subscription_scope, package):
        raise HTTPException(503, 'Contratacao indisponivel.')
    rights = access.config.pro
    if (rights.monitored_asset_limit != 10 or not rights.automatic_market_alerts
            or not rights.futures_enabled):
        raise HTTPException(503, 'Contratacao indisponivel.')
    return GrantAcknowledgement(identity=identity, verifier=verifier, store=store,
        acknowledger=GooglePlaySubscriptionAcknowledger(package_name=package,
            product_id='cryptoradar_pro_monthly'), access=access, package=package)
