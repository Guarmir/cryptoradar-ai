from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.billing.subscription_installation_grant import (
    GrantRequest, InstallationGrantService, InstallationGrantStore, create_grant_service,
)


def setup_service():
    auth = Mock()
    auth.authorize.return_value = 'uid'
    claim = Mock()
    entitlement = Mock()
    entitlement.evaluate.return_value = SimpleNamespace(eligible=True)
    store = Mock()
    store.register.return_value = True
    return InstallationGrantService(authorizer=auth, claim_service=claim,
        entitlement_service=entitlement, grant_store=store), auth, claim, entitlement, store


def request():
    return GrantRequest(installation_id=' device ', purchase_token=' token ')


def test_valid_grant_is_persisted_but_not_pro():
    service, auth, claim, entitlement, store = setup_service()
    result = service.register(request(), 'Bearer test')
    auth.authorize.assert_called_once_with(authorization='Bearer test', installation_id='device')
    claim.claim.assert_called_once_with(authorization='Bearer test', purchase_token='token')
    entitlement.evaluate.assert_called_once_with(authorization='Bearer test', purchase_token='token')
    store.register.assert_called_once_with(uid='uid', installation_id='device', purchase_token='token')
    assert result.pro_granted is False


def test_wrong_owner_stops_all_other_operations():
    service, auth, claim, entitlement, store = setup_service()
    auth.authorize.side_effect = HTTPException(403)
    with pytest.raises(HTTPException) as error:
        service.register(request(), 'Bearer test')
    assert error.value.status_code == 403
    claim.claim.assert_not_called()
    entitlement.evaluate.assert_not_called()
    store.register.assert_not_called()


def test_failed_claim_stops_grant():
    service, _, claim, entitlement, store = setup_service()
    claim.claim.side_effect = RuntimeError()
    with pytest.raises(RuntimeError):
        service.register(request(), 'Bearer test')
    entitlement.evaluate.assert_not_called()
    store.register.assert_not_called()


def test_ineligible_stops_grant():
    service, _, _, entitlement, store = setup_service()
    entitlement.evaluate.return_value = SimpleNamespace(eligible=False)
    with pytest.raises(HTTPException) as error:
        service.register(request(), 'Bearer test')
    assert error.value.status_code == 409
    store.register.assert_not_called()


def test_changed_owner_or_snapshot_blocks_persistence():
    service, _, _, _, store = setup_service()
    store.register.return_value = False
    with pytest.raises(HTTPException) as error:
        service.register(request(), 'Bearer test')
    assert error.value.status_code == 409


@pytest.mark.parametrize('field', ['installation_id', 'purchase_token'])
def test_whitespace_rejected_before_auth(field):
    service, auth, _, _, _ = setup_service()
    data = {'installation_id': 'device', 'purchase_token': 'token'}
    data[field] = ' '
    with pytest.raises(HTTPException) as error:
        service.register(GrantRequest(**data), None)
    assert error.value.status_code == 422
    auth.authorize.assert_not_called()


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('GOOGLE_PLAY_INSTALLATION_GRANT_ENABLED', raising=False)
    with pytest.raises(HTTPException) as error:
        create_grant_service()
    assert error.value.status_code == 503


@pytest.mark.parametrize('row', [None, ('expiry',)])
def test_store_hashes_token_and_bounds_grant(row):
    from hashlib import sha256
    conn = Mock()
    cursor = conn.cursor.return_value
    cursor.fetchone.return_value = row
    store = InstallationGrantStore(database_url='db', push_scope='push', subscription_scope='billing',
        package_name='package', connection_factory=lambda _: conn)
    assert store.register(uid='uid', installation_id='device', purchase_token='secret') is (row is not None)
    sql, params = cursor.execute.call_args.args
    assert 'LEAST(s.expires_at' in sql and '15 minutes' in sql
    assert 'o.firebase_auth_uid = %s' in sql
    assert 'grants.firebase_auth_uid = EXCLUDED.firebase_auth_uid' in sql
    assert 'secret' not in params and sha256(b'secret').hexdigest() in params
    if row is None:
        conn.commit.assert_not_called()
        conn.rollback.assert_called_once()
    else:
        conn.commit.assert_called_once()
    conn.close.assert_called_once()
