from types import SimpleNamespace
from unittest.mock import Mock, MagicMock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.monitoring.individual_monitoring_intent import MonitoringIntent, interpret_observation
from app.monitoring.individual_monitoring_api import IndividualMonitoringService
from app.monitoring.individual_monitoring_runtime import ActiveAsset, IndividualMonitoringRuntime
from app.monitoring.postgresql_individual_monitoring_store import PostgreSQLIndividualMonitoringStore
from app.services.routes.individual_monitoring_router import create_individual_monitoring_router


@pytest.mark.parametrize('intent,side', [('opportunity','long'),('position',None),('position','other'),('other',None)])
def test_invalid_intent(intent, side):
    with pytest.raises(ValueError):
        MonitoringIntent(intent, side)


@pytest.mark.parametrize('change,intent,side,expected', [
    (None,'opportunity',None,'insufficient_data'),
    (float('nan'),'position','long','insufficient_data'),
    (0,'position','short','unchanged'),
    (2,'opportunity',None,'upward_movement'),
    (-2,'opportunity',None,'downward_movement'),
    (2,'position','long','favorable_movement'),
    (-2,'position','long','adverse_movement'),
    (2,'position','short','adverse_movement'),
    (-2,'position','short','favorable_movement'),
])
def test_interpret(change,intent,side,expected):
    assert interpret_observation(SimpleNamespace(price_change_since_previous_percent=change), MonitoringIntent(intent,side)) == expected


@pytest.fixture
def api():
    access = SimpleNamespace(authorizer=Mock())
    access.authorizer.authorize.return_value = 'verified-uid'
    store = Mock()
    store.load_intent.return_value = MonitoringIntent()
    store.save_intent.return_value = True
    service = IndividualMonitoringService(access=access,store=store,coin_catalog=Mock())
    app = FastAPI()
    app.include_router(create_individual_monitoring_router(lambda: service))
    return TestClient(app), access, store


PATH = '/monitoring/individual/device/assets/bitcoin/intent'
HEAD = {'Authorization':'Bearer test'}


def test_get_scoped(api):
    client,_,store = api
    response = client.get(PATH,headers=HEAD)
    assert response.json() == {'intent':'opportunity','side':None}
    assert response.headers['cache-control'] == 'no-store'
    store.load_intent.assert_called_once_with(uid='verified-uid',coin_id='bitcoin')


def test_update_scoped(api):
    client,_,store = api
    assert client.put(PATH,headers=HEAD,json={'intent':'position','side':'short'}).json() == {'intent':'position','side':'short'}
    store.save_intent.assert_called_once_with(uid='verified-uid',coin_id='bitcoin',intent=MonitoringIntent('position','short'))


def test_reject_other_account(api):
    client,access,store = api
    access.authorizer.authorize.side_effect = HTTPException(403)
    assert client.put(PATH,headers=HEAD,json={'intent':'position','side':'long'}).status_code == 403
    store.save_intent.assert_not_called()


def test_reject_extra_authority(api):
    client,_,store = api
    assert client.put(PATH,headers=HEAD,json={'intent':'opportunity','uid':'other'}).status_code == 422
    store.save_intent.assert_not_called()


def test_invalid_combination(api):
    client,_,store = api
    assert client.put(PATH,headers=HEAD,json={'intent':'position'}).status_code == 422
    store.save_intent.assert_not_called()


def test_missing_asset(api):
    client,_,store = api
    store.save_intent.return_value = False
    store.load_intent.return_value = None
    assert client.put(PATH,headers=HEAD,json={'intent':'opportunity'}).status_code == 404
    assert client.get(PATH,headers=HEAD).status_code == 404


def test_store_scoped_update_and_read():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.rowcount = 1
    cursor.fetchone.return_value = ('position','long')
    store = PostgreSQLIndividualMonitoringStore(database_url='db',scope_key='scope',connection_factory=lambda _:conn)
    assert store.save_intent(uid='u',coin_id='BTC',intent=MonitoringIntent('position','long'))
    assert cursor.execute.call_args.args[1] == ('position','long','scope','u','btc')
    conn.commit.assert_called_once()
    assert store.load_intent(uid='u',coin_id='btc') == MonitoringIntent('position','long')
    assert cursor.execute.call_args.args[1] == ('scope','u','btc')


def test_store_rolls_back():
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.execute.side_effect = RuntimeError('db')
    store = PostgreSQLIndividualMonitoringStore(database_url='db',scope_key='scope',connection_factory=lambda _:conn)
    with pytest.raises(RuntimeError):
        store.save_intent(uid='u',coin_id='btc',intent=MonitoringIntent())
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


def test_shared_prices_opposite_interpretations_and_clear():
    reader = Mock()
    reader.load_active.return_value = [ActiveAsset('a','bitcoin','BTC','position','long'), ActiveAsset('b','bitcoin','BTC','position','short')]
    provider = Mock()
    provider.fetch_market_data_batch.side_effect = [
        {'BITCOIN':{'id':'bitcoin','current_price':10,'last_updated':'2026-11-27T08:00:00Z'}},
        {'BITCOIN':{'id':'bitcoin','current_price':11,'last_updated':'2026-11-27T08:01:00Z'}}]
    runtime = IndividualMonitoringRuntime(reader=reader,provider=provider)
    runtime.run_once()
    assert set(runtime.interpretations.values()) == {'insufficient_data'}
    runtime.run_once()
    assert runtime.interpretations == {('a','bitcoin'):'favorable_movement',('b','bitcoin'):'adverse_movement'}
    assert len(provider.fetch_market_data_batch.call_args.args[0]) == 1
    reader.load_active.side_effect = RuntimeError('db')
    with pytest.raises(RuntimeError):
        runtime.run_once()
    assert not runtime.interpretations
