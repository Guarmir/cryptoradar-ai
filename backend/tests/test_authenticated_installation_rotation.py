from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.push.authenticated_installation_api import InstallationEnrollmentFlow, create_installation_router
from app.push.authenticated_installation_enrollment import AuthenticatedInstallationEnrollment
from app.push.fcm_possession_challenge import ChallengeRejected, VerifiedDestination
from app.push.postgresql_authenticated_installation_store import PostgreSQLAuthenticatedInstallationStore


def db(*rows):
    conn = Mock()
    cur = conn.cursor.return_value
    cur.fetchone.side_effect = rows
    return PostgreSQLAuthenticatedInstallationStore(database_url='db', scope_key='scope',
        connection_factory=lambda _: conn), conn, cur


def rotate(store, fid='fid'):
    return store.rotate_owned_device(installation_id='existing', firebase_auth_uid='alice',
        fcm_token='new-token', firebase_installation_id=fid)


def test_rotation_preserves_id_and_grant():
    store, conn, cur = db(('alice', 'fid', True), None, ('existing',))
    assert rotate(store) == 'existing'
    assert 'pg_advisory_xact_lock' in cur.execute.call_args_list[0].args[0]
    assert 'UPDATE cryptoradar_push_devices' in cur.execute.call_args_list[-1].args[0]
    assert cur.execute.call_args_list[-1].args[1] == ('new-token', 'scope', 'existing')
    assert cur.execute.call_count == 4
    conn.commit.assert_called_once()


@pytest.mark.parametrize('row', [None, ('bob','fid',True), ('alice','different',True),
                                 ('alice','fid',False), ('alice',None,True)])
def test_rotation_rejects_wrong_owner_or_device(row):
    store, conn, cur = db(row)
    with pytest.raises(ValueError):
        rotate(store)
    assert cur.execute.call_count == 2
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_rotation_rejects_existing_destination():
    store, conn, cur = db(('alice','fid',True), ('another',))
    with pytest.raises(ValueError):
        rotate(store)
    assert cur.execute.call_count == 3
    conn.rollback.assert_called_once()


def test_rotation_requires_returned_id():
    store, conn, _ = db(('alice','fid',True), None, None)
    with pytest.raises(ValueError):
        rotate(store)
    conn.rollback.assert_called_once()


def detach(store):
    store.detach_owned_device(installation_id='existing', firebase_auth_uid='alice')


def test_detach_only_own_device():
    store, conn, cur = db(('existing','alice'), ('existing',))
    detach(store)
    assert 'DELETE FROM cryptoradar_push_devices' in cur.execute.call_args_list[-1].args[0]
    assert cur.execute.call_args_list[-1].args[1] == ('scope','existing')
    conn.commit.assert_called_once()


def test_detach_retry_after_lost_response():
    store, conn, cur = db(None)
    detach(store)
    assert cur.execute.call_count == 1
    conn.commit.assert_called_once()


@pytest.mark.parametrize('owner', ['bob', None])
def test_detach_rejects_unowned_device(owner):
    store, conn, cur = db(('existing',owner))
    with pytest.raises(ValueError):
        detach(store)
    assert cur.execute.call_count == 1
    conn.rollback.assert_called_once()


@pytest.fixture
def api():
    identity, store, challenge, limiter = Mock(), Mock(), Mock(), Mock()
    def verify(auth):
        if auth != 'Bearer alice':
            raise HTTPException(401, 'Unauthorized')
        return 'alice'
    identity.verify_bearer.side_effect = verify
    challenge.verify.return_value = VerifiedDestination('alice','new-token','fid')
    store.rotate_owned_device.return_value = 'existing'
    enrollment = AuthenticatedInstallationEnrollment(identity_verifier=identity, store=store)
    flow = InstallationEnrollmentFlow(identity=identity, challenge=challenge, enrollment=enrollment, limiter=limiter)
    app = FastAPI()
    app.include_router(create_installation_router(lambda: flow))
    return TestClient(app), store, challenge


BODY = {'installation_id':'existing','fcm_token':'new-token','firebase_installation_id':'fid',
        'challenge_id':'id','proof':'secret'}
HEADERS = {'Authorization':'Bearer alice'}


def test_rotate_route_requires_fresh_proof(api):
    client, store, challenge = api
    response = client.post('/push/installations/rotate', json=BODY, headers=HEADERS)
    assert response.json() == {'installation_id':'existing','status':'registered'}
    challenge.verify.assert_called_once()
    store.rotate_owned_device.assert_called_once_with(installation_id='existing',firebase_auth_uid='alice',
        fcm_token='new-token',firebase_installation_id='fid')


def test_rotate_route_rejects_failed_proof(api):
    client, store, challenge = api
    challenge.verify.side_effect = ChallengeRejected()
    assert client.post('/push/installations/rotate',json=BODY,headers=HEADERS).status_code == 409
    store.rotate_owned_device.assert_not_called()


def test_detach_requires_authentication(api):
    client, store, _ = api
    assert client.post('/push/installations/detach',json={'installation_id':'existing'}).status_code == 401
    store.detach_owned_device.assert_not_called()


def test_detach_uses_verified_uid(api):
    client, store, _ = api
    response = client.post('/push/installations/detach',json={'installation_id':'existing'},headers=HEADERS)
    assert response.json() == {'status':'detached'}
    store.detach_owned_device.assert_called_once_with(installation_id='existing',firebase_auth_uid='alice')
