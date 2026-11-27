from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.access.access_entitlements_config import AccessEntitlementsConfig
from app.monitoring.individual_monitoring_api import (
    IndividualMonitoringService, create_individual_monitoring_service,
)
from app.monitoring.postgresql_individual_monitoring_store import (
    IndividualMonitoringAsset, IndividualMonitoringLimitReached,
)
from app.services.routes.individual_monitoring_router import create_individual_monitoring_router


@pytest.fixture
def setup():
    access = SimpleNamespace(authorizer=Mock(), reader=Mock(),
                             config=AccessEntitlementsConfig.from_environment({}))
    access.authorizer.authorize.return_value = 'uid-1'
    access.reader.has_access.return_value = False
    store = Mock()
    store.load_all.return_value = (IndividualMonitoringAsset('bitcoin', 'BTC'),)
    store.add.side_effect = lambda **kw: kw['asset']
    store.remove.return_value = True
    catalog = Mock(return_value=[{'id':'bitcoin','symbol':'btc'}])
    service = IndividualMonitoringService(access=access, store=store, coin_catalog=catalog)
    app = FastAPI()
    app.include_router(create_individual_monitoring_router(lambda: service))
    return TestClient(app), access, store, catalog


PATH = '/monitoring/individual/device/assets'
HEADERS = {'Authorization':'Bearer test'}


def test_list_account(setup):
    client, access, store, _ = setup
    response = client.get(PATH, headers=HEADERS)
    assert response.json() == {'plan':'free','limit':1,'assets':[{'coin_id':'bitcoin','symbol':'BTC'}]}
    assert response.headers['cache-control'] == 'no-store'
    access.authorizer.authorize.assert_called_once_with(authorization='Bearer test', installation_id='device')
    store.load_all.assert_called_once_with(uid='uid-1')


@pytest.mark.parametrize('granted,limit', [(False,1),(True,10)])
def test_add_uses_server_limit(setup, granted, limit):
    client, access, store, _ = setup
    access.reader.has_access.return_value = granted
    response = client.post(PATH, headers=HEADERS, json={'coin_id':' BITCOIN '})
    assert response.status_code == 200
    assert response.json() == {'coin_id':'bitcoin','symbol':'BTC'}
    store.add.assert_called_once_with(uid='uid-1', asset=IndividualMonitoringAsset('bitcoin','BTC'), limit=limit)


@pytest.mark.parametrize('method,path,body', [('get',PATH,None),('post',PATH,{'coin_id':'bitcoin'}),('delete',PATH+'/bitcoin',None)])
def test_denied_never_touches_store(setup,method,path,body):
    client, access, store, catalog = setup
    access.authorizer.authorize.side_effect = HTTPException(403)
    kwargs = {'headers':HEADERS}
    if body is not None: kwargs['json'] = body
    assert getattr(client,method)(path,**kwargs).status_code == 403
    assert not store.mock_calls
    catalog.assert_not_called()


@pytest.mark.parametrize('extra', [{'limit':10},{'uid':'other'},{'symbol':'ETH'}])
def test_reject_client_authority(setup,extra):
    client, _, store, _ = setup
    assert client.post(PATH,json={'coin_id':'bitcoin',**extra},headers=HEADERS).status_code == 422
    store.add.assert_not_called()


def test_limit_reached(setup):
    client, _, store, _ = setup
    store.add.side_effect = IndividualMonitoringLimitReached()
    assert client.post(PATH,json={'coin_id':'bitcoin'},headers=HEADERS).status_code == 409


def test_unknown_canonical_id(setup):
    client, _, store, _ = setup
    assert client.post(PATH,json={'coin_id':'btc'},headers=HEADERS).status_code == 404
    store.add.assert_not_called()


def test_remove_after_expiry(setup):
    client, access, store, _ = setup
    access.reader.has_access.side_effect = RuntimeError('unavailable')
    assert client.delete(PATH+'/bitcoin',headers=HEADERS).json() == {'removed':True}
    store.remove.assert_called_once_with(uid='uid-1',coin_id='bitcoin')
    access.reader.has_access.assert_not_called()


def test_fail_closed_on_grant_error(setup):
    client, access, store, _ = setup
    access.reader.has_access.side_effect = RuntimeError('private database info')
    response = client.post(PATH,json={'coin_id':'bitcoin'},headers=HEADERS)
    assert response.status_code == 503
    assert 'private' not in response.text
    store.add.assert_not_called()


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED',raising=False)
    with pytest.raises(HTTPException) as error:
        create_individual_monitoring_service()
    assert error.value.status_code == 503


def test_catalog_unavailable(setup):
    client, _, store, catalog = setup
    catalog.return_value = []
    assert client.post(PATH,json={'coin_id':'bitcoin'},headers=HEADERS).status_code == 503
    store.add.assert_not_called()
