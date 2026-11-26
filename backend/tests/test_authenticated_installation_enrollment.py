from unittest.mock import Mock
from uuid import UUID

import pytest

from app.push.authenticated_installation_enrollment import AuthenticatedInstallationEnrollment
from app.push.postgresql_authenticated_installation_store import PostgreSQLAuthenticatedInstallationStore


def subject():
    identity = Mock()
    identity.verify_bearer.return_value = 'uid-1'
    store = Mock()
    return AuthenticatedInstallationEnrollment(identity_verifier=identity, store=store), identity, store


def test_fresh_id_and_verified_uid():
    service, identity, store = subject()
    result = service.enroll(authorization='Bearer test', fcm_token='token', firebase_installation_id='fid')
    assert UUID(result.installation_id).version == 4
    assert result.firebase_auth_uid == 'uid-1'
    identity.verify_bearer.assert_called_once_with('Bearer test')
    store.create_owned_device.assert_called_once_with(installation_id=result.installation_id,
        firebase_auth_uid='uid-1', fcm_token='token', firebase_installation_id='fid')


def test_fresh_ids_differ():
    service, _, _ = subject()
    assert service.enroll(authorization='a', fcm_token='t').installation_id != service.enroll(authorization='a', fcm_token='t').installation_id


def test_cannot_supply_existing_id():
    service, _, store = subject()
    with pytest.raises(TypeError):
        service.enroll(authorization='a', fcm_token='t', installation_id='existing')
    store.create_owned_device.assert_not_called()


def test_auth_failure_blocks_storage():
    service, identity, store = subject()
    identity.verify_bearer.side_effect = PermissionError()
    with pytest.raises(PermissionError):
        service.enroll(authorization=None, fcm_token='t')
    store.create_owned_device.assert_not_called()


@pytest.mark.parametrize('token', ['', ' ', None, 'x'*4097])
def test_invalid_token(token):
    service, _, store = subject()
    with pytest.raises(ValueError):
        service.enroll(authorization='a', fcm_token=token)
    store.create_owned_device.assert_not_called()


@pytest.mark.parametrize('fid', ['', ' ', 'x'*201])
def test_invalid_fid(fid):
    service, _, store = subject()
    with pytest.raises(ValueError):
        service.enroll(authorization='a', fcm_token='t', firebase_installation_id=fid)
    store.create_owned_device.assert_not_called()


def test_storage_failure_not_reported_as_success():
    service, _, store = subject()
    store.create_owned_device.side_effect = RuntimeError()
    with pytest.raises(RuntimeError):
        service.enroll(authorization='a', fcm_token='t')


def db_subject():
    connection = Mock()
    cursor = connection.cursor.return_value
    store = PostgreSQLAuthenticatedInstallationStore(database_url='db', scope_key='scope', connection_factory=lambda _: connection)
    return store, connection, cursor


def create(store):
    store.create_owned_device(installation_id='new', firebase_auth_uid='uid', fcm_token='token', firebase_installation_id=None)


def test_atomic_inserts_without_upsert():
    store, connection, cursor = db_subject()
    create(store)
    first, second = cursor.execute.call_args_list
    assert 'cryptoradar_push_devices' in first.args[0]
    assert first.args[1] == ('scope', 'new', 'token', None)
    assert 'cryptoradar_push_installation_owners' in second.args[0]
    assert second.args[1] == ('scope', 'new', 'uid')
    assert all('ON CONFLICT' not in call.args[0] for call in (first, second))
    connection.commit.assert_called_once()
    connection.rollback.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


@pytest.mark.parametrize('effects', [[RuntimeError()], [None, RuntimeError()]])
def test_insert_failure_rolls_back(effects):
    store, connection, cursor = db_subject()
    cursor.execute.side_effect = effects
    with pytest.raises(RuntimeError):
        create(store)
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
