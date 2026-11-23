from app.push.push_delivery_models import PushNotificationMessage, PushSendResult
from app.push.push_delivery_service import PushDeliveryService
from app.push.push_device import PushDevice
from app.push.push_notification_preferences import PushNotificationPreferences


class _Devices:
    def __init__(self):
        self.devices = (
            PushDevice(installation_id="a", fcm_token="token-a"),
            PushDevice(installation_id="b", fcm_token="token-b"),
        )

    def load_enabled(self):
        return self.devices


class _Sender:
    def __init__(self):
        self.sent = []

    def send(self, *, device, message):
        self.sent.append((device.installation_id, message))
        return PushSendResult(delivered=True)


class _Preferences:
    def __init__(self, values=None, fail=False):
        self.values = values or {}
        self.fail = fail

    def load(self, installation_id):
        if self.fail:
            raise RuntimeError("database unavailable")
        return self.values.get(installation_id, PushNotificationPreferences())


def _message(state, type_="early_movement"):
    return PushNotificationMessage(
        title="CryptoRadar",
        body="Teste",
        data={"type": type_, "state": state},
    )


def test_each_installation_is_filtered_independently():
    sender = _Sender()
    store = _Preferences({
        "a": PushNotificationPreferences(observation_enabled=False),
    })
    result = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=store,
    ).deliver(_message("observation"))
    assert [id_ for id_, _ in sender.sent] == ["b"]
    assert result.delivered == 1
    assert result.outcomes[0].error_code == "notification_preference_disabled"


def test_three_states_are_filtered_separately():
    sender = _Sender()
    store = _Preferences({
        "a": PushNotificationPreferences(
            observation_enabled=False,
            early_movement_enabled=True,
            confirmed_movement_enabled=False,
        ),
        "b": PushNotificationPreferences(
            observation_enabled=True,
            early_movement_enabled=False,
            confirmed_movement_enabled=True,
        ),
    })
    service = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=store,
    )
    for state, target in (
        ("observation", "b"),
        ("early_movement", "a"),
        ("confirmed_movement", "b"),
    ):
        sender.sent.clear()
        result = service.deliver(_message(state))
        assert [id_ for id_, _ in sender.sent] == [target]
        assert result.delivered == 1


def test_legacy_installations_default_to_all_enabled():
    sender = _Sender()
    result = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=_Preferences(),
    ).deliver(_message("confirmed_movement"))
    assert result.delivered == 2


def test_non_scanner_messages_are_unaffected():
    sender = _Sender()
    disabled = PushNotificationPreferences(
        observation_enabled=False,
        early_movement_enabled=False,
        confirmed_movement_enabled=False,
    )
    result = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=_Preferences({"a": disabled, "b": disabled}),
    ).deliver(_message("observation", type_="market_event"))
    assert result.delivered == 2


def test_unknown_scanner_state_keeps_previous_behavior():
    sender = _Sender()
    result = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=_Preferences(fail=True),
    ).deliver(_message("unknown"))
    assert result.delivered == 2


def test_preference_database_failure_does_not_override_opt_out():
    sender = _Sender()
    result = PushDeliveryService(
        device_store=_Devices(),
        push_sender=sender,
        notification_preferences_store=_Preferences(fail=True),
    ).deliver(_message("observation"))
    assert result.delivered == 0
    assert len(sender.sent) == 0
    assert all(x.error_code == "notification_preferences_unavailable" for x in result.outcomes)


def test_constructor_without_preferences_keeps_existing_delivery():
    sender = _Sender()
    result = PushDeliveryService(
        device_store=_Devices(), push_sender=sender
    ).deliver(_message("observation"))
    assert result.delivered == 2
