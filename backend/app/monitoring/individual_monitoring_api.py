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
from app.monitoring.individual_monitoring_intent import MonitoringIntent
from app.monitoring.individual_alert_policy import IndividualAlertSettings


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


    def get_intent(self, *, authorization, installation_id, coin_id):
        uid = self._identity(authorization, installation_id)
        intent = self.store.load_intent(uid=uid, coin_id=self._coin_id(coin_id))
        if intent is None:
            raise HTTPException(404, 'Ativo nao cadastrado.')
        return asdict(intent)

    def set_intent(self, *, authorization, installation_id, coin_id, intent, side):
        uid = self._identity(authorization, installation_id)
        coin_id = self._coin_id(coin_id)
        try:
            settings = MonitoringIntent(intent, side)
        except ValueError:
            raise HTTPException(422, 'Intencao ou direcao invalida.') from None
        if not self.store.save_intent(uid=uid, coin_id=coin_id, intent=settings):
            raise HTTPException(404, 'Ativo nao cadastrado.')
        return asdict(settings)


    def get_alert_settings(self, *, authorization, installation_id, coin_id):
        uid = self._identity(authorization, installation_id)
        settings = self.store.load_alert_settings(uid=uid, coin_id=self._coin_id(coin_id))
        if settings is None:
            raise HTTPException(404, 'Ativo nao cadastrado.')
        return asdict(settings)

    def set_alert_settings(self, *, authorization, installation_id, coin_id,
                           interval_minutes, emergency_enabled):
        uid = self._identity(authorization, installation_id)
        try:
            settings = IndividualAlertSettings(interval_minutes, emergency_enabled)
        except ValueError:
            raise HTTPException(422, 'Configuracao de alerta invalida.') from None
        if not self.store.save_alert_settings(uid=uid, coin_id=self._coin_id(coin_id), settings=settings):
            raise HTTPException(404, 'Ativo nao cadastrado.')
        return asdict(settings)


def create_individual_monitoring_service():
    if os.getenv('CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED', '').strip().lower() != 'true':
        raise HTTPException(503, 'Monitoramento individual indisponivel.')
    config = AccessApiConfig.from_environment()
    access = create_installation_access_service()
    return IndividualMonitoringService(access=access,
        store=PostgreSQLIndividualMonitoringStore(database_url=config.database_url,
                                                  scope_key=config.scope_key),
        coin_catalog=get_coin_list)
