from unittest.mock import Mock
import pytest
from app.push.authenticated_installation_enrollment import AuthenticatedInstallationEnrollment
from app.push.postgresql_authenticated_installation_store import PostgreSQLAuthenticatedInstallationStore


def subject(rows):
    conn = Mock()
    cur = conn.cursor.return_value
    cur.fetchall.return_value = rows
    store = PostgreSQLAuthenticatedInstallationStore(database_url='db', scope_key='scope', connection_factory=lambda _: conn)
    return store, conn, cur


def recover(store):
    return store.recover_or_create_owned_device(installation_id='new', firebase_auth_uid='uid', fcm_token='token', firebase_installation_id='fid')


def test_same_destination_recovers_without_insert():
    store, conn, cur = subject([('existing', 'uid', 'fid', True)])
    assert recover(store) == 'existing'
    assert cur.execute.call_count == 2
    assert 'pg_advisory_xact_lock' in cur.execute.call_args_list[0].args[0]
    conn.commit.assert_called_once()


def test_fresh_destination_creates_both_rows():
    store, conn, cur = subject([])
    assert recover(store) == 'new'
    assert cur.execute.call_count == 4
    conn.commit.assert_called_once()


@pytest.mark.parametrize('rows', [
    [('existing', 'other', 'fid', True)],
    [('existing', 'uid', 'other', True)],
    [('existing', 'uid', 'fid', False)],
    [('a', 'uid', 'fid', True), ('b', 'uid', 'fid', True)],
])
def test_ambiguous_or_incompatible_destination_rejected(rows):
    store, conn, cur = subject(rows)
    with pytest.raises(ValueError):
        recover(store)
    assert cur.execute.call_count == 2
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_enrollment_returns_recovered_id():
    identity, store = Mock(), Mock()
    identity.verify_bearer.return_value = 'uid'
    store.recover_or_create_owned_device.return_value = 'existing'
    service = AuthenticatedInstallationEnrollment(identity_verifier=identity, store=store, recover_existing=True)
    assert service.enroll(authorization='Bearer x', fcm_token='token', firebase_installation_id='fid').installation_id == 'existing'
    store.create_owned_device.assert_not_called()
