from datetime import datetime, timedelta, timezone
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.billing.subscription_grant_acknowledgement import (
    GrantAcknowledgement, create_grant_acknowledgement, REQUIRED_FLAGS,
)
from app.billing.google_play_subscription_acknowledger import SubscriptionAcknowledgementError
from app.billing.subscription_installation_access import InstallationGrantReader
from app.billing.subscription_installation_grant import InstallationGrantService, GrantRequest


def test_grant_commits_before_ack():
    auth, claim, entitlement, store, ack = (Mock() for _ in range(5))
    auth.authorize.return_value = 'uid'
    entitlement.evaluate.return_value = SimpleNamespace(eligible=True)
    store.register.return_value = True
    trace = Mock(); trace.attach_mock(store, 'store'); trace.attach_mock(ack, 'ack')
    service = InstallationGrantService(authorizer=auth, claim_service=claim,
        entitlement_service=entitlement, grant_store=store, acknowledgement=ack)
    result = service.register(GrantRequest(installation_id='device', purchase_token='token'), 'Bearer x')
    assert [call[0] for call in trace.mock_calls] == ['store.register', 'ack']
    assert result.pro_granted is False  # Existing client response contract.
    store.register.return_value = False
    ack.reset_mock()
    with pytest.raises(HTTPException):
        service.register(GrantRequest(installation_id='device', purchase_token='token'), 'Bearer x')
    ack.assert_not_called()


def build(allowed=True, owner='uid', expired=False):
    identity, verifier, store, acknowledger, access = (Mock() for _ in range(5))
    identity.verify_bearer.return_value = 'uid'
    expiry = datetime.now(timezone.utc) + timedelta(hours=-1 if expired else 1)
    snapshot = dict(obfuscated_account_id=sha256(b'uid').hexdigest(),
        product_id='cryptoradar_pro_monthly', entitled_now=True, linked_purchase_token=None,
        state='SUBSCRIPTION_STATE_ACTIVE', expires_at=expiry)
    verifier.verify.side_effect = [SimpleNamespace(**snapshot, acknowledgement_state=state)
        for state in ('ACKNOWLEDGEMENT_STATE_PENDING', 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED')]
    access.authorizer.authorize.return_value = owner
    access.reader.has_access.return_value = allowed
    service = GrantAcknowledgement(identity=identity, verifier=verifier, store=store,
        acknowledger=acknowledger, access=access, package='example.app')
    return service, access, acknowledger, store


def invoke(service):
    service(authorization='Bearer x', installation_id='device', uid='uid', purchase_token='token')


def test_ack_requires_exact_purchase_and_owner():
    service, access, ack, store = build()
    invoke(service)
    access.reader.has_access.assert_called_once_with(installation_id='device', uid='uid', purchase_token='token')
    ack.acknowledge.assert_called_once_with('token')
    assert store.save_verified.call_args.kwargs['acknowledgement_state'] == 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED'


@pytest.mark.parametrize('changes', [{'allowed': False}, {'owner': 'other'}, {'expired': True}])
def test_ack_blocked(changes):
    service, _, ack, _ = build(**changes)
    with pytest.raises(SubscriptionAcknowledgementError):
        invoke(service)
    ack.acknowledge.assert_not_called()


def test_reader_uses_hash_not_plaintext():
    connection = Mock(); cursor = connection.cursor.return_value
    cursor.fetchone.return_value = (True,)
    reader = InstallationGrantReader(database_url='db', push_scope='push', subscription_scope='sub',
        package_name='pkg', connection_factory=lambda _: connection)
    assert reader.has_access(installation_id='device', uid='uid', purchase_token='secret-token')
    sql, params = cursor.execute.call_args.args
    assert 'g.purchase_token_hash = %s' in sql
    assert params[-1] == sha256(b'secret-token').hexdigest()
    assert 'secret-token' not in str(params)


@pytest.mark.parametrize('missing', REQUIRED_FLAGS)
def test_factory_requires_all_flags(monkeypatch, missing):
    for flag in REQUIRED_FLAGS:
        monkeypatch.setenv(flag, 'true')
    monkeypatch.delenv(missing)
    with pytest.raises(HTTPException) as error:
        create_grant_acknowledgement(identity=Mock(), verifier=Mock(), store=Mock(),
            package='pkg', database_url='db', push_scope='push', subscription_scope='sub')
    assert error.value.status_code == 503
