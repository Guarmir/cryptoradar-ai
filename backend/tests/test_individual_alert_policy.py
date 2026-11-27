from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.monitoring.individual_alert_policy import IndividualAlertSettings, evaluate_alert

NOW = datetime(2026, 11, 27, tzinfo=timezone.utc)


def evaluate(change=1, interpretation='upward_movement', interval=30, enabled=True,
             age=0, gap=60, regular=None, emergency=None):
    stamp = NOW - timedelta(seconds=age)
    state = SimpleNamespace(current_observation=SimpleNamespace(observed_at=stamp),
        previous_observation=SimpleNamespace(observed_at=stamp-timedelta(seconds=gap)),
        price_change_since_previous_percent=change)
    return evaluate_alert(state=state, interpretation=interpretation,
        settings=IndividualAlertSettings(interval, enabled), now=NOW,
        last_regular=regular, last_emergency=emergency)


@pytest.mark.parametrize('interval', [0, 1, 10, 120, True, '30'])
def test_invalid_interval(interval):
    with pytest.raises(ValueError):
        IndividualAlertSettings(interval)


@pytest.mark.parametrize('change', [None, float('nan'), float('inf'), 0, .49, -.49])
def test_no_signal(change):
    assert evaluate(change=change) is None


@pytest.mark.parametrize('age,gap', [(181,60),(-1,60),(0,301),(0,0),(0,-1)])
def test_bad_timestamp(age,gap):
    assert evaluate(age=age,gap=gap) is None


@pytest.mark.parametrize('interval', [5,15,30,60])
def test_periodicity(interval):
    assert evaluate(interval=interval,regular=NOW-timedelta(minutes=interval,seconds=-1)) is None
    assert evaluate(interval=interval,regular=NOW-timedelta(minutes=interval)).kind == 'regular'


@pytest.mark.parametrize('change', [-2,2])
def test_emergency_overrides_regular(change):
    assert evaluate(change=change,interpretation='adverse_movement',regular=NOW).kind == 'emergency'


def test_emergency_cooldown():
    assert evaluate(change=-3,interpretation='adverse_movement',emergency=NOW-timedelta(seconds=299)) is None
    assert evaluate(change=-3,interpretation='adverse_movement',emergency=NOW-timedelta(seconds=300)).kind == 'emergency'


@pytest.mark.parametrize('interpretation', ['upward_movement','downward_movement','favorable_movement'])
def test_no_emergency_for_non_adverse(interpretation):
    assert evaluate(change=3,interpretation=interpretation,regular=NOW) is None


def test_emergency_disabled():
    assert evaluate(change=-3,interpretation='adverse_movement',enabled=False,regular=NOW) is None


def test_invalid_switch():
    with pytest.raises(ValueError):
        IndividualAlertSettings(emergency_enabled='true')


def test_unknown_interpretation():
    assert evaluate(interpretation='insufficient_data') is None

from unittest.mock import Mock, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.monitoring.individual_monitoring_api import IndividualMonitoringService
from app.monitoring.postgresql_individual_monitoring_store import PostgreSQLIndividualMonitoringStore
from app.services.routes.individual_monitoring_router import create_individual_monitoring_router

PATH = '/monitoring/individual/device/assets/bitcoin/alerts'

@pytest.fixture
def api():
    access = SimpleNamespace(authorizer=Mock())
    access.authorizer.authorize.return_value = 'verified'
    store = Mock()
    store.load_alert_settings.return_value = IndividualAlertSettings()
    store.save_alert_settings.return_value = True
    service = IndividualMonitoringService(access=access, store=store, coin_catalog=Mock())
    app = FastAPI()
    app.include_router(create_individual_monitoring_router(lambda: service))
    return TestClient(app), access, store


def test_read_settings(api):
    client, _, store = api
    response = client.get(PATH)
    assert response.json() == {'interval_minutes':30,'emergency_enabled':True}
    assert response.headers['cache-control'] == 'no-store'
    store.load_alert_settings.assert_called_once_with(uid='verified',coin_id='bitcoin')


def test_update_settings(api):
    client, _, store = api
    assert client.put(PATH,json={'interval_minutes':15,'emergency_enabled':False}).status_code == 200
    store.save_alert_settings.assert_called_once_with(uid='verified',coin_id='bitcoin',settings=IndividualAlertSettings(15,False))


@pytest.mark.parametrize('body', [{'interval_minutes':10,'emergency_enabled':True}, {'interval_minutes':'30','emergency_enabled':True}, {'interval_minutes':30,'emergency_enabled':'true'}, {'interval_minutes':30,'emergency_enabled':True,'uid':'other'}])
def test_invalid_request(api, body):
    client, _, store = api
    assert client.put(PATH,json=body).status_code == 422
    store.save_alert_settings.assert_not_called()


def test_reject_unowned(api):
    client, access, store = api
    access.authorizer.authorize.side_effect = HTTPException(403)
    assert client.get(PATH).status_code == 403
    assert client.put(PATH,json={'interval_minutes':30,'emergency_enabled':True}).status_code == 403
    store.load_alert_settings.assert_not_called()
    store.save_alert_settings.assert_not_called()


def test_missing_asset(api):
    client, _, store = api
    store.load_alert_settings.return_value = None
    store.save_alert_settings.return_value = False
    assert client.get(PATH).status_code == 404
    assert client.put(PATH,json={'interval_minutes':30,'emergency_enabled':True}).status_code == 404


def test_store_scoped_settings():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (15,False)
    cursor.rowcount = 1
    store = PostgreSQLIndividualMonitoringStore(database_url='db',scope_key='scope',connection_factory=lambda _:conn)
    assert store.load_alert_settings(uid='u',coin_id='BTC') == IndividualAlertSettings(15,False)
    assert cursor.execute.call_args.args[1] == ('scope','u','btc')
    assert store.save_alert_settings(uid='u',coin_id='BTC',settings=IndividualAlertSettings(60,True))
    assert cursor.execute.call_args.args[1] == (60,True,'scope','u','btc')
    conn.commit.assert_called_once()
