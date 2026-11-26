from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.billing import subscription_status_api as api
from app.billing.subscription_status_store import SubscriptionSnapshot, SubscriptionStatusStore
from app.services.routes.subscription_router import create_subscription_router


@pytest.fixture
def setup(monkeypatch):
    identity = Mock()
    identity.verify_bearer.return_value = "uid-real"
    store = Mock()
    store.load_candidate.return_value = None
    monkeypatch.setattr(api, "FirebaseIdentityVerifier", lambda: identity)
    monkeypatch.setattr(api, "create_status_store", lambda: store)
    app = FastAPI()
    app.include_router(create_subscription_router())
    return TestClient(app), identity, store


def test_account_from_bearer_only(setup):
    client, identity, store = setup
    response = client.get('/billing/google-play/status?uid=other', headers={'Authorization': 'Bearer abc'})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    identity.verify_bearer.assert_called_once_with('Bearer abc')
    store.load_candidate.assert_called_once_with('uid-real')
    assert response.json()['status'] == 'no_stored_candidate'
    assert response.json()['pro_granted'] is False


def test_snapshot_never_grants(setup):
    client, _, store = setup
    now = datetime.now(timezone.utc)
    store.load_candidate.return_value = SubscriptionSnapshot('SUBSCRIPTION_STATE_ACTIVE', now, 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED', now)
    result = client.get('/billing/google-play/status').json()
    assert result['status'] == 'stored_candidate'
    assert result['live_verified'] is False
    assert result['pro_granted'] is False
    assert result['verified_at'] is not None


def test_auth_failure_does_not_read_store(setup):
    client, identity, store = setup
    identity.verify_bearer.side_effect = HTTPException(401, 'invalid')
    assert client.get('/billing/google-play/status').status_code == 401
    store.load_candidate.assert_not_called()


def test_database_failure_hides_details(setup):
    client, _, store = setup
    store.load_candidate.side_effect = RuntimeError('secret')
    response = client.get('/billing/google-play/status')
    assert response.status_code == 503
    assert 'secret' not in response.text


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('GOOGLE_PLAY_CLAIM_ENABLED', raising=False)
    with pytest.raises(HTTPException) as error:
        api.create_status_store()
    assert error.value.status_code == 503


@pytest.mark.parametrize('has_row', [True, False])
def test_store_scopes_query_and_closes(has_row):
    connection = Mock()
    cursor = connection.cursor.return_value
    now = datetime.now(timezone.utc)
    row = ('SUBSCRIPTION_STATE_ACTIVE', now, 'ACKNOWLEDGEMENT_STATE_PENDING', now)
    cursor.fetchone.return_value = row if has_row else None
    store = SubscriptionStatusStore(database_url='db', scope_key='scope', package_name='pkg', connection_factory=lambda _: connection)
    result = store.load_candidate(' uid ')
    sql, params = cursor.execute.call_args.args
    assert params[:4] == ('scope', 'uid', 'pkg', 'cryptoradar_pro_monthly')
    for clause in ('scope_key = %s', 'firebase_auth_uid = %s', 'package_name = %s', 'product_id = %s', 'expires_at > NOW()', 'subscription_state IN'):
        assert clause in sql
    assert result == (SubscriptionSnapshot(*row) if has_row else None)
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()


def test_store_closes_on_failure():
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.execute.side_effect = RuntimeError('db')
    store = SubscriptionStatusStore(database_url='db', scope_key='scope', package_name='pkg', connection_factory=lambda _: connection)
    with pytest.raises(RuntimeError):
        store.load_candidate('uid')
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
