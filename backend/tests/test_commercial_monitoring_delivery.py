from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.push.commercial_monitoring_delivery import (
    CommercialMonitoringDeviceStore, monitoring_delivery_store,
)


@pytest.mark.parametrize('uid,granted,free,pro,expected', [
    (None, False, False, False, True),
    ('uid', True, False, True, True),
    ('uid', False, False, True, False),
    ('uid', False, True, True, True),
    ('uid', True, True, False, False),
    ('uid', None, False, True, False),
])
def test_delivery_policy(uid, granted, free, pro, expected):
    device = SimpleNamespace(installation_id='device')
    devices = Mock(); devices.load_enabled.return_value = (device,)
    owners = Mock(); owners.load_owner_uid.return_value = uid
    grants = Mock(); grants.has_access.return_value = granted
    rights = SimpleNamespace(free=SimpleNamespace(automatic_market_alerts=free),
                             pro=SimpleNamespace(automatic_market_alerts=pro))
    store = CommercialMonitoringDeviceStore(device_store=devices, owner_store=owners,
                                               grant_reader=grants, entitlements_config=rights)
    assert store.load_enabled() == ((device,) if expected else ())
    if uid is None:
        grants.has_access.assert_not_called()
    else:
        grants.has_access.assert_called_once_with(installation_id='device', uid=uid)


@pytest.mark.parametrize('failure', ['owner', 'grant'])
def test_failure_does_not_authorize_and_preserves_other_recipient(failure):
    first = SimpleNamespace(installation_id='first')
    second = SimpleNamespace(installation_id='second')
    devices = Mock(); devices.load_enabled.return_value = (first, second)
    owners = Mock(); grants = Mock()
    owners.load_owner_uid.side_effect = ([RuntimeError(), None] if failure == 'owner'
                                         else ['uid', None])
    grants.has_access.side_effect = RuntimeError()
    rights = SimpleNamespace(free=SimpleNamespace(automatic_market_alerts=True),
                             pro=SimpleNamespace(automatic_market_alerts=True))
    store = CommercialMonitoringDeviceStore(device_store=devices, owner_store=owners,
                                               grant_reader=grants, entitlements_config=rights)
    assert store.load_enabled() == (second,)


def test_disabled_returns_original_store(monkeypatch):
    monkeypatch.delenv('GOOGLE_PLAY_MONITORING_ACCESS_ENABLED', raising=False)
    store = object()
    assert monitoring_delivery_store(device_store=store, database_url='db', scope_key='scope') is store
