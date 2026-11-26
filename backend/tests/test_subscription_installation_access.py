from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.billing.subscription_installation_access import (
    InstallationGrantReader, InstallationAccessService, get_installation_access,
    create_installation_access_service,
)


def build_service(granted=False):
    authorizer = Mock()
    authorizer.authorize.return_value = 'uid'
    reader = Mock()
    reader.has_access.return_value = granted
    config = SimpleNamespace(
        free=SimpleNamespace(monitored_asset_limit=1, automatic_market_alerts=False, futures_enabled=False),
        pro=SimpleNamespace(monitored_asset_limit=10, automatic_market_alerts=True, futures_enabled=True),
    )
    return InstallationAccessService(authorizer=authorizer, grant_reader=reader,
                                     entitlements_config=config), authorizer, reader


@pytest.mark.parametrize('granted,expected,limit', [(True, 'pro', 10), (False, 'free', 1), (None, 'free', 1)])
def test_resolves_only_valid_grant(granted, expected, limit):
    service, auth, reader = build_service(granted)
    result = get_installation_access(' install ', 'Bearer test', service)
    assert result.plan == expected
    assert result.monitored_asset_limit == limit
    auth.authorize.assert_called_once_with(authorization='Bearer test', installation_id='install')
    reader.has_access.assert_called_once_with(installation_id='install', uid='uid')


@pytest.mark.parametrize('code', [401, 403])
def test_no_grant_read_without_authorized_owner(code):
    service, auth, reader = build_service(True)
    auth.authorize.side_effect = HTTPException(status_code=code)
    with pytest.raises(HTTPException) as error:
        get_installation_access('install', None, service)
    assert error.value.status_code == code
    reader.has_access.assert_not_called()


def test_database_error_is_safe():
    service, _, reader = build_service(True)
    reader.has_access.side_effect = RuntimeError('secret')
    with pytest.raises(HTTPException) as error:
        get_installation_access('install', 'Bearer test', service)
    assert error.value.status_code == 503
    assert 'secret' not in error.value.detail


def test_invalid_installation_rejected():
    service, auth, _ = build_service(True)
    with pytest.raises(HTTPException) as error:
        get_installation_access(' ', 'Bearer test', service)
    assert error.value.status_code == 422
    auth.authorize.assert_not_called()


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('GOOGLE_PLAY_INSTALLATION_ACCESS_ENABLED', raising=False)
    with pytest.raises(HTTPException) as error:
        create_installation_access_service()
    assert error.value.status_code == 503


@pytest.mark.parametrize('row,expected', [((True,), True), ((False,), False), (None, False)])
def test_query_checks_ownership_scope_and_expiration(row, expected):
    connection = Mock()
    cursor = connection.cursor.return_value
    cursor.fetchone.return_value = row
    reader = InstallationGrantReader(database_url='db', push_scope='push', subscription_scope='billing',
                                     package_name='package', connection_factory=lambda _: connection)
    assert reader.has_access(installation_id='install', uid='uid') is expected
    sql, params = cursor.execute.call_args.args
    assert params == ('push', 'install', 'uid', 'billing', 'package')
    assert 'o.firebase_auth_uid = g.firebase_auth_uid' in sql
    assert 's.firebase_auth_uid = g.firebase_auth_uid' in sql
    assert 'g.valid_until > NOW()' in sql
    assert 's.expires_at > NOW()' in sql
    assert 's.verified_at > NOW()' in sql
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
