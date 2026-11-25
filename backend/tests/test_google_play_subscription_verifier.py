"""Testes offline: nenhuma chamada real ao Google ou cobranca."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.billing.google_play_subscription_verifier import (
    GooglePlaySubscriptionVerificationError,
    GooglePlaySubscriptionVerifier,
)


NOW = datetime(2026, 11, 25, tzinfo=timezone.utc)


def make_verifier(payload, *, status=200):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(status_code=status, json=lambda: payload)

    verifier = GooglePlaySubscriptionVerifier(
        package_name="com.example.cryptoradar",
        product_id="cryptoradar_pro_monthly",
        credentials_provider=lambda: SimpleNamespace(valid=True, token="test-credential"),
        http_get=fake_get,
        now_provider=lambda: NOW,
    )
    return verifier, calls


def payload(state="SUBSCRIPTION_STATE_ACTIVE", expiry="2026-12-25T00:00:00Z", product="cryptoradar_pro_monthly"):
    return {
        "subscriptionState": state,
        "acknowledgementState": "ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED",
        "lineItems": [{"productId": product, "expiryTime": expiry}],
    }


@pytest.mark.parametrize("state,expected", [
    ("SUBSCRIPTION_STATE_ACTIVE", True),
    ("SUBSCRIPTION_STATE_IN_GRACE_PERIOD", True),
    ("SUBSCRIPTION_STATE_CANCELED", True),
    ("SUBSCRIPTION_STATE_ON_HOLD", False),
    ("SUBSCRIPTION_STATE_PAUSED", False),
    ("SUBSCRIPTION_STATE_PENDING", False),
    ("SUBSCRIPTION_STATE_EXPIRED", False),
])
def test_subscription_state(state, expected):
    verifier, _ = make_verifier(payload(state=state))
    assert verifier.verify("purchase-token").entitled_now is expected


def test_expired_date_cannot_grant_access():
    verifier, _ = make_verifier(payload(expiry="2026-10-25T00:00:00Z"))
    assert verifier.verify("purchase-token").entitled_now is False


def test_wrong_product_rejected():
    verifier, _ = make_verifier(payload(product="unrelated"))
    with pytest.raises(GooglePlaySubscriptionVerificationError):
        verifier.verify("purchase-token")


def test_missing_expiry_rejected():
    verifier, _ = make_verifier({"subscriptionState": "SUBSCRIPTION_STATE_ACTIVE", "lineItems": [{"productId": "cryptoradar_pro_monthly"}]})
    with pytest.raises(GooglePlaySubscriptionVerificationError):
        verifier.verify("purchase-token")


def test_google_http_error_fails_closed():
    verifier, _ = make_verifier(payload(), status=403)
    with pytest.raises(GooglePlaySubscriptionVerificationError):
        verifier.verify("purchase-token")


def test_purchase_token_is_url_encoded_and_not_logged():
    verifier, calls = make_verifier(payload())
    verifier.verify("token/with?special")
    assert calls[0][0].endswith("token%2Fwith%3Fspecial")
    assert calls[0][1]["timeout"] == 15


def test_empty_token_rejected():
    verifier, _ = make_verifier(payload())
    with pytest.raises(ValueError):
        verifier.verify(" ")
