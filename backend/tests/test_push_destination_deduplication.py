from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from app.push.push_device import PushDevice
from app.push.push_delivery_service import PushDeliveryService
from app.push.push_delivery_models import PushNotificationMessage, PushSendResult
from app.push.push_notification_preferences import PushNotificationPreferences
from app.push.commercial_monitoring_delivery import CommercialMonitoringDeviceStore


def device(id_, enabled=True, token='same'):
    return PushDevice(installation_id=id_, fcm_token=token, enabled=enabled)


@pytest.mark.parametrize('granted,enabled,expected', [(True,True,True),(False,True,False),(True,False,False)])
def test_owned_destination_never_falls_back_to_legacy(granted,enabled,expected):
    legacy, owned = device('legacy'), device('owned',enabled)
    store = Mock(); store.load_all.return_value = (legacy,owned)
    owners = Mock(); owners.load_owner_uid.side_effect = lambda id_: 'uid' if id_ == 'owned' else None
    grants = Mock(); grants.has_access.return_value = granted
    rights = SimpleNamespace(free=SimpleNamespace(automatic_market_alerts=False),pro=SimpleNamespace(automatic_market_alerts=True))
    result = CommercialMonitoringDeviceStore(device_store=store,owner_store=owners,grant_reader=grants,entitlements_config=rights).load_enabled()
    assert result == ((owned,) if expected else ())


@pytest.mark.parametrize('failure', [False,True])
def test_ambiguous_or_unknown_ownership_blocks_destination(failure):
    store=Mock(); store.load_all.return_value=(device('a'),device('b'))
    owners=Mock(); owners.load_owner_uid.side_effect = [None,RuntimeError()] if failure else ['a','b']
    grants=Mock()
    assert CommercialMonitoringDeviceStore(device_store=store,owner_store=owners,grant_reader=grants,entitlements_config=Mock()).load_enabled()==()
    grants.has_access.assert_not_called()


@pytest.mark.parametrize('send_fails',[False,True])
def test_only_one_attempt_per_destination(send_fails):
    store=Mock(); store.load_enabled.return_value=(device('a'),device('b'))
    sender=Mock(); sender.send.return_value=PushSendResult(delivered=True)
    if send_fails: sender.send.side_effect=RuntimeError()
    result=PushDeliveryService(device_store=store,push_sender=sender).deliver(PushNotificationMessage(title='x',body='y'))
    assert sender.send.call_count==1
    assert result.outcomes[1].error_code=='duplicate_destination'


@pytest.mark.parametrize('failure',[False,True])
def test_later_alias_optout_or_error_blocks_earlier_alias(failure):
    store=Mock(); store.load_enabled.return_value=(device('a'),device('b'),device('c',token='other'))
    prefs=Mock(); prefs.load.side_effect=[PushNotificationPreferences(),RuntimeError() if failure else PushNotificationPreferences(observation_enabled=False),PushNotificationPreferences()]
    sender=Mock(); sender.send.return_value=PushSendResult(delivered=True)
    result=PushDeliveryService(device_store=store,push_sender=sender,notification_preferences_store=prefs).deliver(PushNotificationMessage(title='x',body='y',data={'type':'early_movement','state':'observation'}))
    assert sender.send.call_count==1
    assert sender.send.call_args.kwargs['device'].installation_id=='c'
    assert result.delivered==1
