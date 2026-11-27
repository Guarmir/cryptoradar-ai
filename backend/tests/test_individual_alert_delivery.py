from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock

import pytest

from app.monitoring.individual_alert_delivery import IndividualAlertDelivery, PostgreSQLIndividualAlertStore
from app.monitoring.individual_alert_policy import IndividualAlertSettings, IndividualAlertDecision
from app.monitoring.individual_monitoring_runtime import ActiveAsset
from app.push.push_device import PushDevice

NOW = datetime(2026, 11, 27, tzinfo=timezone.utc)
ASSET = ActiveAsset('account-a', 'bitcoin', 'BTC', 'position', 'long')
DEVICE = PushDevice('device-a', 'token-a')


def state(change=-3):
    return SimpleNamespace(current_observation=SimpleNamespace(observed_at=NOW),
        previous_observation=SimpleNamespace(observed_at=NOW-timedelta(seconds=60)),
        price_change_since_previous_percent=change)


@pytest.fixture
def delivery():
    store, sender = Mock(), Mock()
    store.load_settings.return_value = (IndividualAlertSettings(), NOW, None)
    store.recipients.return_value = (DEVICE,)
    store.reserve.return_value = True
    sender.send.return_value = SimpleNamespace(delivered=True)
    return IndividualAlertDelivery(store=store, sender=sender, clock=lambda: NOW), store, sender


def test_emergency_overrides_regular(delivery):
    service, store, sender = delivery
    assert service.deliver(ASSET, state(), 'adverse_movement') == 1
    decision = store.reserve.call_args.args[2]
    assert decision.kind == 'emergency'
    message = sender.send.call_args.kwargs['message']
    assert message.data == {'type': 'individual_monitoring', 'priority': 'emergency'}
    assert all(s not in repr(message) for s in ('account-a', 'bitcoin', 'BTC', 'long'))
    assert sender.send.call_args.kwargs['device'] == DEVICE


def test_regular_due(delivery):
    service, store, sender = delivery
    store.load_settings.return_value = (IndividualAlertSettings(), None, None)
    assert service.deliver(ASSET, state(-1), 'adverse_movement') == 1
    assert store.reserve.call_args.args[2].kind == 'regular'


@pytest.mark.parametrize('settings', [None, (IndividualAlertSettings(), NOW, NOW),
                                      (IndividualAlertSettings(30, False), NOW, None)])
def test_no_alert_when_removed_or_not_due(delivery, settings):
    service, store, sender = delivery
    store.load_settings.return_value = settings
    assert service.deliver(ASSET, state(), 'adverse_movement') == 0
    store.recipients.assert_not_called()
    sender.send.assert_not_called()


def test_no_recipient_no_reservation(delivery):
    service, store, sender = delivery
    store.recipients.return_value = ()
    assert service.deliver(ASSET, state(), 'adverse_movement') == 0
    store.reserve.assert_not_called()
    sender.send.assert_not_called()


def test_lost_atomic_reservation(delivery):
    service, store, sender = delivery
    store.reserve.return_value = False
    assert service.deliver(ASSET, state(), 'adverse_movement') == 0
    sender.send.assert_not_called()


def test_database_error_never_sends(delivery):
    service, store, sender = delivery
    store.reserve.side_effect = RuntimeError('db')
    with pytest.raises(RuntimeError):
        service.deliver(ASSET, state(), 'adverse_movement')
    sender.send.assert_not_called()


def test_duplicate_and_disabled_destinations(delivery):
    service, store, sender = delivery
    store.recipients.return_value = (DEVICE, PushDevice('alias','token-a'), PushDevice('off','off',enabled=False))
    assert service.deliver(ASSET, state(), 'adverse_movement') == 1
    sender.send.assert_called_once()


def test_failure_isolated_and_no_second_alias_attempt(delivery):
    service, store, sender = delivery
    store.recipients.return_value = (DEVICE, PushDevice('alias','token-a'), PushDevice('b','token-b'))
    sender.send.side_effect = [RuntimeError('send'), SimpleNamespace(delivered=True)]
    assert service.deliver(ASSET, state(), 'adverse_movement') == 1
    assert sender.send.call_count == 2


@pytest.fixture
def database():
    conn = MagicMock()
    cursor = conn.__enter__.return_value.cursor.return_value.__enter__.return_value
    access = SimpleNamespace(reader=SimpleNamespace(url='db', push_scope='push', subscription_scope='sub', package='pkg'),
        config=SimpleNamespace(pro=SimpleNamespace(automatic_market_alerts=True, monitored_asset_limit=10),
                               free=SimpleNamespace(automatic_market_alerts=False, monitored_asset_limit=1)))
    return PostgreSQLIndividualAlertStore(access=access, scope_key='watch', connection_factory=lambda _:conn), cursor, conn


def test_settings_scoped_to_intent(database):
    store, cursor, _ = database
    cursor.fetchone.return_value = (15, True, NOW, None)
    assert store.load_settings(ASSET) == (IndividualAlertSettings(15,True), NOW, None)
    sql, params = cursor.execute.call_args.args
    assert 'position_side IS NOT DISTINCT FROM' in sql
    assert params == ('watch','account-a','bitcoin','position','long')


def test_recipients_scoped_and_reauthorized(database):
    store, cursor, _ = database
    cursor.fetchall.return_value = [('device-a','token-a','android',True,None)]
    assert store.recipients(ASSET) == (DEVICE,)
    sql, params = cursor.execute.call_args.args
    for clause in ('o.firebase_auth_uid = %s', 'd.enabled', 'g.valid_until > NOW()',
                   's.expires_at > NOW()', 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED',
                   'other.fcm_token = d.fcm_token', 'NOT EXISTS', 'rn <= %s'):
        assert clause in sql
    assert params == ('watch','account-a','sub','pkg','push','account-a','bitcoin','position','long',True,10,False,1)


@pytest.mark.parametrize('kind,seconds,column', [('regular',900,'last_regular_alert_at'), ('emergency',300,'last_emergency_alert_at')])
def test_atomic_cooldown(database, kind, seconds, column):
    store, cursor, conn = database
    cursor.fetchone.return_value = ('bitcoin',)
    assert store.reserve(ASSET, IndividualAlertSettings(15), IndividualAlertDecision(kind,-3,NOW))
    sql, params = cursor.execute.call_args.args
    assert f'SET {column}' in sql and f'{column} <=' in sql and 'RETURNING coin_id' in sql
    assert params[-1] == seconds
    assert 'alert_interval_minutes = %s' in sql and 'emergency_alert_enabled = %s' in sql
    conn.__exit__.assert_called_once()
    cursor.fetchone.return_value = None
    assert not store.reserve(ASSET, IndividualAlertSettings(15), IndividualAlertDecision(kind,-3,NOW))


def test_runtime_dispatches_only_fresh_account_samples():
    from app.monitoring.individual_monitoring_runtime import IndividualMonitoringRuntime
    reader = Mock()
    reader.load_active.return_value = [ASSET, ActiveAsset("b", "bitcoin", "BTC"), ActiveAsset("a", "coin-two", "ABC")]
    provider = Mock()
    provider.fetch_market_data_batch.side_effect = lambda targets: {t.symbol: {"id": t.coin_id, "current_price": 10, "last_updated": "2026-11-27T08:00:00Z"} for t in targets}
    delivery = Mock()
    runtime = IndividualMonitoringRuntime(reader=reader, provider=provider, alert_delivery=delivery)
    assert runtime.run_once() == 3
    assert delivery.deliver.call_count == 3
    assert runtime.run_once() == 0
    assert delivery.deliver.call_count == 3
