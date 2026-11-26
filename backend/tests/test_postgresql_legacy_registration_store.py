from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.push.postgresql_legacy_registration_store import PostgreSQLLegacyRegistrationStore
from app.push.push_device_registration_service import ProtectedInstallationRegistrationError


def subject(rows, *, rowcount=1):
    cursor = Mock(rowcount=rowcount)
    cursor.fetchone.side_effect = rows
    connection = Mock()
    connection.cursor.return_value = cursor
    store = PostgreSQLLegacyRegistrationStore(database_url='test', scope_key='scope',
                                              connection_factory=lambda _: connection)
    device = SimpleNamespace(installation_id='id', fcm_token='token',
                             firebase_installation_id='fid', platform='android', enabled=True)
    return store, device, connection, cursor


def statements(cursor):
    return [' '.join(call.args[0].split()) for call in cursor.execute.call_args_list]


def test_new_device():
    store, device, connection, cursor = subject([('id',)])
    store.save_device(device)
    assert len(statements(cursor)) == 2
    assert 'DO NOTHING' in statements(cursor)[1]
    connection.commit.assert_called_once()
    connection.close.assert_called_once()


def test_unowned_device_updates_after_lock_and_owner_check():
    store, device, connection, cursor = subject([None, ('id',), None])
    store.save_device(device)
    sql = statements(cursor)
    assert 'READ COMMITTED' in sql[0]
    assert 'FOR UPDATE' in sql[2]
    assert 'installation_owners' in sql[3]
    assert sql[4].startswith('UPDATE')
    assert cursor.execute.call_args.args[1] == ('token', 'fid', 'android', True, 'scope', 'id')
    connection.commit.assert_called_once()


@pytest.mark.parametrize('rows', [[None, ('id',), ('owner',)], [None, None]])
def test_conflict_never_updates_owned_or_missing_device(rows):
    store, device, connection, cursor = subject(rows)
    with pytest.raises(ProtectedInstallationRegistrationError):
        store.save_device(device)
    assert not any(sql.startswith('UPDATE') for sql in statements(cursor))
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()


def test_update_count_failure():
    store, device, connection, cursor = subject([None, ('id',), None], rowcount=0)
    with pytest.raises(ProtectedInstallationRegistrationError):
        store.save_device(device)
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()


def test_database_failure_rolls_back():
    store, device, connection, cursor = subject([])
    cursor.execute.side_effect = RuntimeError('database unavailable')
    with pytest.raises(RuntimeError):
        store.save_device(device)
    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
