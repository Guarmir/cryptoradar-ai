from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.billing.subscription_entitlement_service import SubscriptionEntitlementService

NOW = datetime(2026, 11, 26, tzinfo=timezone.utc)
PRODUCT = 'cryptoradar_pro_monthly'


@pytest.fixture
def setup():
    identity = Mock()
    identity.verify_bearer.return_value = 'uid'
    store = Mock()
    store.load_by_token.return_value = SimpleNamespace(firebase_auth_uid='uid', product_id=PRODUCT)
    verifier = Mock()
    verifier.verify.return_value = SimpleNamespace(
        obfuscated_account_id=sha256(b'uid').hexdigest(), product_id=PRODUCT,
        linked_purchase_token=None, entitled_now=True, state='SUBSCRIPTION_STATE_ACTIVE',
        acknowledgement_state='ACKNOWLEDGEMENT_STATE_PENDING', expires_at=NOW + timedelta(days=1))
    service = SubscriptionEntitlementService(identity_verifier=identity,
        subscription_verifier=verifier, subscription_store=store, now_provider=lambda: NOW)
    return service, identity, store, verifier


def evaluate(setup, token='token'):
    return setup[0].evaluate(authorization='Bearer test', purchase_token=token)


@pytest.mark.parametrize('state', sorted(SubscriptionEntitlementService.STATES))
def test_live_valid(setup, state):
    setup[3].verify.return_value.state = state
    assert evaluate(setup).eligible
    setup[1].verify_bearer.assert_called_once_with('Bearer test')
    setup[2].load_by_token.assert_called_once_with('token')
    setup[3].verify.assert_called_once_with('token')


@pytest.mark.parametrize('field,value', [
    ('obfuscated_account_id', None), ('obfuscated_account_id', 'wrong'),
    ('product_id', 'other'), ('linked_purchase_token', 'old'),
    ('entitled_now', False), ('state', 'SUBSCRIPTION_STATE_ON_HOLD'),
    ('acknowledgement_state', 'UNKNOWN'), ('expires_at', NOW),
    ('expires_at', NOW.replace(tzinfo=None)),
])
def test_invalid_live(setup, field, value):
    setattr(setup[3].verify.return_value, field, value)
    assert not evaluate(setup).eligible


@pytest.mark.parametrize('record', [None, SimpleNamespace(firebase_auth_uid='other', product_id=PRODUCT),
    SimpleNamespace(firebase_auth_uid='uid', product_id='other')])
def test_wrong_stored_owner_or_product(setup, record):
    setup[2].load_by_token.return_value = record
    assert not evaluate(setup).eligible
    setup[3].verify.assert_not_called()


@pytest.mark.parametrize('token', ['', ' ', 'x'*8193])
def test_invalid_token(setup, token):
    assert not evaluate(setup, token).eligible
    setup[2].load_by_token.assert_not_called()


def test_auth_failure(setup):
    setup[1].verify_bearer.side_effect = HTTPException(401)
    with pytest.raises(HTTPException):
        evaluate(setup)
    setup[2].load_by_token.assert_not_called()


@pytest.mark.parametrize('index,method', [(2,'load_by_token'), (3,'verify')])
def test_failure_closed(setup, index, method):
    getattr(setup[index], method).side_effect = RuntimeError('secret')
    result = evaluate(setup)
    assert not result.eligible
    assert result.reason == 'verification_unavailable'


def test_already_acknowledged(setup):
    setup[3].verify.return_value.acknowledgement_state = 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'
    assert evaluate(setup).eligible
