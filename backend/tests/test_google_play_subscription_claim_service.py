from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.billing.google_play_subscription_claim_service import (
    GooglePlaySubscriptionClaimService,
    PurchaseIdentityMismatchError,
    PurchaseNotEntitledError,
    obfuscated_account_id,
)
from app.billing.google_play_subscription_verifier import (
    GooglePlaySubscriptionVerifier,
    VerifiedGooglePlaySubscription,
)

UID = "firebase-user-123"
TOKEN = "secret-purchase-token"
EXPIRY = datetime.now(timezone.utc) + timedelta(days=20)


def make_verified(**overrides):
    values = dict(
        product_id="cryptoradar_pro_monthly",
        state="SUBSCRIPTION_STATE_ACTIVE",
        expires_at=EXPIRY,
        acknowledgement_state="ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
        entitled_now=True,
        linked_purchase_token=None,
        obfuscated_account_id=obfuscated_account_id(UID),
    )
    values.update(overrides)
    return VerifiedGooglePlaySubscription(**values)


def make_service(verified=None, uid=UID):
    identity = Mock()
    identity.verify_bearer.return_value = uid
    verifier = Mock()
    verifier.verify.return_value = verified or make_verified()
    store = Mock()
    service = GooglePlaySubscriptionClaimService(
        identity_verifier=identity,
        subscription_verifier=verifier,
        subscription_store=store,
        package_name="br.com.cryptoradar.app",
    )
    return service, identity, verifier, store


def test_valid_purchase_saved_to_firebase_owner():
    service, identity, verifier, store = make_service()
    service.claim(authorization="Bearer good", purchase_token=TOKEN)
    identity.verify_bearer.assert_called_once_with("Bearer good")
    verifier.verify.assert_called_once_with(TOKEN)
    store.save_verified.assert_called_once_with(
        purchase_token=TOKEN,
        firebase_auth_uid=UID,
        package_name="br.com.cryptoradar.app",
        product_id="cryptoradar_pro_monthly",
        subscription_state="SUBSCRIPTION_STATE_ACTIVE",
        acknowledgement_state="ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
        expires_at=EXPIRY,
    )


@pytest.mark.parametrize("account_id", [None, "", "other-account"])
def test_rejects_purchase_missing_or_mismatched_account(account_id):
    service, _, _, store = make_service(make_verified(obfuscated_account_id=account_id))
    with pytest.raises(PurchaseIdentityMismatchError):
        service.claim(authorization="Bearer good", purchase_token=TOKEN)
    store.save_verified.assert_not_called()


def test_rejects_other_firebase_user():
    service, _, _, store = make_service(uid="intruder")
    with pytest.raises(PurchaseIdentityMismatchError):
        service.claim(authorization="Bearer good", purchase_token=TOKEN)
    store.save_verified.assert_not_called()


def test_rejects_inactive_subscription():
    service, _, _, store = make_service(make_verified(entitled_now=False))
    with pytest.raises(PurchaseNotEntitledError):
        service.claim(authorization="Bearer good", purchase_token=TOKEN)
    store.save_verified.assert_not_called()


def test_rejects_linked_purchase_until_explicit_policy():
    service, _, _, store = make_service(make_verified(linked_purchase_token="old-token"))
    with pytest.raises(PurchaseIdentityMismatchError):
        service.claim(authorization="Bearer good", purchase_token=TOKEN)
    store.save_verified.assert_not_called()


def test_rejects_missing_package_config():
    with pytest.raises(ValueError):
        GooglePlaySubscriptionClaimService(
            identity_verifier=Mock(), subscription_verifier=Mock(),
            subscription_store=Mock(), package_name="  ",
        )


def test_obfuscated_account_id_is_deterministic():
    assert len(obfuscated_account_id(UID)) == 64
    assert obfuscated_account_id(" " + UID + " ") == obfuscated_account_id(UID)
    assert obfuscated_account_id("another") != obfuscated_account_id(UID)


def test_obfuscated_account_id_rejects_missing():
    with pytest.raises(ValueError):
        obfuscated_account_id(" ")


def test_verifier_parses_google_account_identifier():
    verifier = GooglePlaySubscriptionVerifier(
        package_name="br.com.cryptoradar.app", product_id="cryptoradar_pro_monthly",
    )
    result = verifier._parse({
        "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
        "lineItems": [{"productId": "cryptoradar_pro_monthly", "expiryTime": EXPIRY.isoformat()}],
        "externalAccountIdentifiers": {"obfuscatedExternalAccountId": "opaque-account"},
    })
    assert result.obfuscated_account_id == "opaque-account"


def test_verifier_missing_external_ids_keeps_none():
    verifier = GooglePlaySubscriptionVerifier(
        package_name="br.com.cryptoradar.app", product_id="cryptoradar_pro_monthly",
    )
    result = verifier._parse({
        "subscriptionState": "SUBSCRIPTION_STATE_ACTIVE",
        "lineItems": [{"productId": "cryptoradar_pro_monthly", "expiryTime": EXPIRY.isoformat()}],
    })
    assert result.obfuscated_account_id is None
