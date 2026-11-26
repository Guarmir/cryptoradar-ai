"""Internal orchestration; requires a real, durable entitlement provider before use."""
from hashlib import sha256

from app.billing.google_play_subscription_acknowledger import SubscriptionAcknowledgementError

ACKNOWLEDGED = 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
PENDING = 'ACKNOWLEDGEMENT_STATE_PENDING'


class SubscriptionAcknowledgementService:
    def __init__(self, *, identity_verifier, subscription_verifier, subscription_store,
                 acknowledger, ensure_entitlement, package_name,
                 product_id='cryptoradar_pro_monthly'):
        self._identity = identity_verifier
        self._verifier = subscription_verifier
        self._store = subscription_store
        self._ack = acknowledger
        self._ensure_entitlement = ensure_entitlement
        self._package = package_name.strip()
        self._product = product_id.strip()
        if not self._package or not self._product or not callable(ensure_entitlement):
            raise ValueError('Configuration and durable entitlement provider required.')

    def _verify(self, token, uid):
        verified = self._verifier.verify(token)
        if (verified.obfuscated_account_id != sha256(uid.encode('utf-8')).hexdigest()
                or verified.product_id != self._product or not verified.entitled_now
                or verified.linked_purchase_token
                or verified.acknowledgement_state not in (PENDING, ACKNOWLEDGED)):
            raise SubscriptionAcknowledgementError('Purchase not eligible.')
        return verified

    def _save(self, token, uid, verified):
        self._store.save_verified(purchase_token=token, firebase_auth_uid=uid,
                                  package_name=self._package, product_id=verified.product_id,
                                  subscription_state=verified.state,
                                  acknowledgement_state=verified.acknowledgement_state,
                                  expires_at=verified.expires_at)

    def acknowledge(self, *, authorization, purchase_token):
        if not isinstance(purchase_token, str) or not purchase_token.strip() or len(purchase_token.strip()) > 8192:
            raise ValueError('Invalid purchase token.')
        token = purchase_token.strip()
        uid = self._identity.verify_bearer(authorization).strip()
        if not uid:
            raise SubscriptionAcknowledgementError('Authentication required.')
        verified = self._verify(token, uid)
        self._save(token, uid, verified)
        # Must return True only after durable access has actually been granted.
        # No default implementation: this service is not wired into production.
        if self._ensure_entitlement(uid, token, verified) is not True:
            raise SubscriptionAcknowledgementError('Entitlement not fulfilled.')
        if verified.acknowledgement_state == ACKNOWLEDGED:
            return
        try:
            self._ack.acknowledge(token)
        except SubscriptionAcknowledgementError:
            # A concurrent request or a lost response may already have succeeded.
            pass
        confirmed = self._verify(token, uid)
        if confirmed.acknowledgement_state != ACKNOWLEDGED:
            raise SubscriptionAcknowledgementError('Acknowledgement not confirmed; retry required.')
        self._save(token, uid, confirmed)
