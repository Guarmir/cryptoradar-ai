"""Authenticated account watchlist management; no worker activation."""
import os
from dataclasses import asdict

from fastapi import HTTPException

from app.access.access_api_config import AccessApiConfig
from app.billing.subscription_installation_access import create_installation_access_service
from app.monitoring.postgresql_individual_monitoring_store import (
    IndividualMonitoringAsset, IndividualMonitoringLimitReached,
    PostgreSQLIndividualMonitoringStore,
)
from app.services.market_data_service import get_coin_list


class IndividualMonitoringService:
    def __init__(self, *, access, store, coin_catalog):
        self.access = access
        self.store = store
        self.coin_catalog = coin_catalog

    def _identity(self, authorization, installation_id):
        installation_id = installation_id.strip()
        if not installation_id or len(installation_id) > 200:
            raise HTTPException(422, 'Instalacao invalida.')
        return self.access.authorizer.authorize(
            authorization=authorization, installation_id=installation_id)

    def _rights(self, uid, installation_id):
        granted = self.access.reader.has_access(uid=uid, installation_id=installation_id.strip())
        rights = self.access.config.pro if granted is True else self.access.config.free
        if type(rights.monitored_asset_limit) is not int or not 1 <= rights.monitored_asset_limit <= 10:
            raise HTTPException(503, 'Configuracao de monitoramento indisponivel.')
        return rights

    @staticmethod
    def _coin_id(value):
        value = value.strip().lower()
        if not value or len(value) > 200 or '\x00' in value:
            raise HTTPException(422, 'Ativo invalido.')
        return value

    def list_assets(self, *, authorization, installation_id):
        uid = self._identity(authorization, installation_id)
        rights = self._rights(uid, installation_id)
        assets = self.store.load_all(uid=uid)
        return {'plan': rights.plan, 'limit': rights.monitored_asset_limit,
                'assets': [asdict(asset) for asset in assets]}

    def add_asset(self, *, authorization, installation_id, coin_id):
        uid = self._identity(authorization, installation_id)
        coin_id = self._coin_id(coin_id)
        catalog = self.coin_catalog()
        if not isinstance(catalog, list) or not catalog:
            raise HTTPException(503, 'Catalogo indisponivel.')
        matches = [coin for coin in catalog if isinstance(coin, dict)
                   and coin.get('id') == coin_id and isinstance(coin.get('symbol'), str)]
        if len(matches) != 1:
            raise HTTPException(404, 'Ativo nao encontrado.')
        try:
            asset = IndividualMonitoringAsset(coin_id, matches[0]['symbol'])
        except ValueError:
            raise HTTPException(503, 'Catalogo indisponivel.') from None
        rights = self._rights(uid, installation_id)
        try:
            saved = self.store.add(uid=uid, asset=asset, limit=rights.monitored_asset_limit)
        except IndividualMonitoringLimitReached:
            raise HTTPException(409, 'Limite de ativos atingido.') from None
        return asdict(saved)

    def remove_asset(self, *, authorization, installation_id, coin_id):
        uid = self._identity(authorization, installation_id)
        return {'removed': self.store.remove(uid=uid, coin_id=self._coin_id(coin_id))}


def create_individual_monitoring_service():
    if os.getenv('CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED', '').strip().lower() != 'true':
        raise HTTPException(503, 'Monitoramento individual indisponivel.')
    config = AccessApiConfig.from_environment()
    access = create_installation_access_service()
    return IndividualMonitoringService(access=access,
        store=PostgreSQLIndividualMonitoringStore(database_url=config.database_url,
                                                  scope_key=config.scope_key),
        coin_catalog=get_coin_list)
