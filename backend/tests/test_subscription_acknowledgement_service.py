from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.billing.google_play_subscription_acknowledger import (
    GooglePlaySubscriptionAcknowledger, SubscriptionAcknowledgementError,
)
from app.billing.subscription_acknowledgement_service import (
    SubscriptionAcknowledgementService, ACKNOWLEDGED, PENDING,
)


def snapshot(state=PENDING, **changes):
    data = dict(obfuscated_account_id=sha256(b'uid').hexdigest(),
                product_id='cryptoradar_pro_monthly', entitled_now=True,
                linked_purchase_token=None, acknowledgement_state=state,
                state='SUBSCRIPTION_STATE_ACTIVE', expires_at=None)
    data.update(changes)
    return SimpleNamespace(**data)


def setup():
    identity = Mock(); identity.verify_bearer.return_value = 'uid'
    verifier = Mock(); verifier.verify.side_effect = [snapshot(), snapshot(ACKNOWLEDGED)]
    store = Mock(); ack = Mock(); grant = Mock(return_value=True)
    service = SubscriptionAcknowledgementService(identity_verifier=identity,
        subscription_verifier=verifier, subscription_store=store, acknowledger=ack,
        ensure_entitlement=grant, package_name='example.app')
    return service, identity, verifier, store, ack, grant


def run(service):
    service.acknowledge(authorization='Bearer test', purchase_token='token')


def test_success_order():
    s, _, _, store, ack, grant = setup()
    calls = Mock(); calls.attach_mock(store, 'store'); calls.attach_mock(grant, 'grant'); calls.attach_mock(ack, 'ack')
    run(s)
    assert [c[0] for c in calls.mock_calls] == ['store.save_verified', 'grant', 'ack.acknowledge', 'store.save_verified']
    assert store.save_verified.call_args.kwargs['acknowledgement_state'] == ACKNOWLEDGED


@pytest.mark.parametrize('changes', [dict(obfuscated_account_id='wrong'), dict(entitled_now=False), dict(linked_purchase_token='old'), dict(product_id='other'), dict(acknowledgement_state='unknown')])
def test_rejects_invalid(changes):
    s, _, verifier, store, ack, grant = setup(); verifier.verify.side_effect = [snapshot(**changes)]
    with pytest.raises(SubscriptionAcknowledgementError): run(s)
    store.save_verified.assert_not_called(); ack.acknowledge.assert_not_called(); grant.assert_not_called()


def test_no_entitlement_no_ack():
    s, _, _, _, ack, grant = setup(); grant.return_value = False
    with pytest.raises(SubscriptionAcknowledgementError): run(s)
    ack.acknowledge.assert_not_called()


def test_storage_failure_no_ack():
    s, _, _, store, ack, grant = setup(); store.save_verified.side_effect = RuntimeError()
    with pytest.raises(RuntimeError): run(s)
    ack.acknowledge.assert_not_called(); grant.assert_not_called()


def test_already_acknowledged():
    s, _, verifier, _, ack, _ = setup(); verifier.verify.side_effect = [snapshot(ACKNOWLEDGED)]
    run(s); ack.acknowledge.assert_not_called()


def test_lost_response_confirmed():
    s, _, _, _, ack, _ = setup(); ack.acknowledge.side_effect = SubscriptionAcknowledgementError()
    run(s)


def test_unconfirmed_retry():
    s, _, verifier, store, _, _ = setup(); verifier.verify.side_effect = [snapshot(), snapshot()]
    with pytest.raises(SubscriptionAcknowledgementError): run(s)
    assert store.save_verified.call_count == 1


def test_auth_failure():
    s, identity, verifier, _, ack, _ = setup(); identity.verify_bearer.side_effect = RuntimeError()
    with pytest.raises(RuntimeError): run(s)
    verifier.verify.assert_not_called(); ack.acknowledge.assert_not_called()


def test_transport():
    post = Mock(return_value=SimpleNamespace(status_code=200))
    a = GooglePlaySubscriptionAcknowledger(package_name='example.app', product_id='pro',
        credentials_provider=lambda: SimpleNamespace(valid=True, token='credential'), http_post=post)
    a.acknowledge('a/b')
    assert post.call_args.args[0].endswith('/pro/tokens/a%2Fb:acknowledge')
    assert post.call_args.kwargs['allow_redirects'] is False
    assert post.call_args.kwargs['json'] == {}


@pytest.mark.parametrize('status', [302, 400, 401, 409, 500])
def test_transport_rejects_http(status):
    a = GooglePlaySubscriptionAcknowledger(package_name='example.app', product_id='pro',
        credentials_provider=lambda: SimpleNamespace(valid=True, token='credential'),
        http_post=Mock(return_value=SimpleNamespace(status_code=status)))
    with pytest.raises(SubscriptionAcknowledgementError): a.acknowledge('token')
