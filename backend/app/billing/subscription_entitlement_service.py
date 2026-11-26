"""Live account entitlement decision; does not grant installation permissions."""
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from hmac import compare_digest
from typing import Callable


@dataclass(frozen=True)
class SubscriptionEntitlementDecision:
    eligible: bool
    reason: str


class SubscriptionEntitlementService:
    PRODUCT = 'cryptoradar_pro_monthly'
    STATES = frozenset({'SUBSCRIPTION_STATE_ACTIVE',
                        'SUBSCRIPTION_STATE_IN_GRACE_PERIOD',
                        'SUBSCRIPTION_STATE_CANCELED'})
    ACK_STATES = frozenset({'ACKNOWLEDGEMENT_STATE_PENDING',
                            'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'})

    def __init__(self, *, identity_verifier, subscription_verifier,
                 subscription_store, now_provider: Callable[[], datetime] | None = None):
        self._identity = identity_verifier
        self._verifier = subscription_verifier
        self._store = subscription_store
        self._now = now_provider or (lambda: datetime.now(timezone.utc))

    def evaluate(self, *, authorization: str | None,
                 purchase_token: str) -> SubscriptionEntitlementDecision:
        uid = self._identity.verify_bearer(authorization)
        if not isinstance(uid, str) or not uid.strip():
            return SubscriptionEntitlementDecision(False, 'authentication_required')
        uid = uid.strip()
        if not isinstance(purchase_token, str) or not purchase_token.strip() or len(purchase_token) > 8192:
            return SubscriptionEntitlementDecision(False, 'invalid_token')
        token = purchase_token.strip()
        try:
            stored = self._store.load_by_token(token)
            if stored is None or stored.firebase_auth_uid != uid or stored.product_id != self.PRODUCT:
                return SubscriptionEntitlementDecision(False, 'not_eligible')
            live = self._verifier.verify(token)
            expected = sha256(uid.encode('utf-8')).hexdigest()
            account = live.obfuscated_account_id
            now = self._now()
            if (not isinstance(account, str) or not account.isascii()
                    or not compare_digest(account, expected)
                    or live.product_id != self.PRODUCT
                    or live.linked_purchase_token
                    or live.entitled_now is not True
                    or live.state not in self.STATES
                    or live.acknowledgement_state not in self.ACK_STATES
                    or not isinstance(live.expires_at, datetime)
                    or live.expires_at.utcoffset() is None
                    or now.utcoffset() is None
                    or live.expires_at <= now):
                return SubscriptionEntitlementDecision(False, 'not_eligible')
            return SubscriptionEntitlementDecision(True, 'live_verified')
        except Exception:
            # No secrets or upstream error details returned; fail closed.
            return SubscriptionEntitlementDecision(False, 'verification_unavailable')
