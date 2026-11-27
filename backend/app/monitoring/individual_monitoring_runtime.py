"""Opt-in account watchlist sampling, independent of the legacy broadcast engine."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from app.monitoring.monitoring_target import MonitoringTarget
from app.monitoring.monitoring_state import MonitoringState
from app.monitoring.monitoring_observation_builder import build_monitoring_observation

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActiveAsset:
    uid: str
    coin_id: str
    symbol: str


class ActiveWatchlistReader:
    """One DB snapshot: current grants and oldest assets within the account limit."""
    def __init__(self, *, access, scope_key, connection_factory=None):
        self.reader = access.reader
        self.config = access.config
        self.scope = scope_key
        self.factory = connection_factory
        if not scope_key or any(type(n) is not int or not 1 <= n <= 10 for n in (
            self.config.free.monitored_asset_limit, self.config.pro.monitored_asset_limit
        )):
            raise ValueError('Invalid watchlist configuration.')

    def load_active(self):
        factory = self.factory
        if factory is None:
            import psycopg
            factory = lambda url: psycopg.connect(url, connect_timeout=10, options='-c statement_timeout=10000')
        connection = factory(self.reader.url)
        try:
            with connection.cursor() as cursor:
                cursor.execute('''WITH ranked AS (
                    SELECT a.firebase_auth_uid, a.coin_id, a.symbol,
                        row_number() OVER (PARTITION BY a.firebase_auth_uid ORDER BY a.created_at, a.coin_id) AS rn
                    FROM cryptoradar_individual_monitoring_assets a WHERE a.scope_key = %s
                ), entitled AS (
                    SELECT DISTINCT g.firebase_auth_uid
                    FROM cryptoradar_subscription_installation_grants g
                    JOIN cryptoradar_push_installation_owners o
                      ON o.scope_key = g.push_scope AND o.installation_id = g.installation_id
                      AND o.firebase_auth_uid = g.firebase_auth_uid
                    JOIN cryptoradar_google_play_subscriptions s
                      ON s.scope_key = g.subscription_scope AND s.purchase_token_hash = g.purchase_token_hash
                      AND s.firebase_auth_uid = g.firebase_auth_uid
                    WHERE g.push_scope = %s AND g.subscription_scope = %s AND s.package_name = %s
                      AND s.product_id = 'cryptoradar_pro_monthly'
                      AND g.valid_until > NOW() AND s.expires_at > NOW()
                      AND s.verified_at > NOW() - INTERVAL '15 minutes'
                      AND s.subscription_state IN ('SUBSCRIPTION_STATE_ACTIVE',
                          'SUBSCRIPTION_STATE_IN_GRACE_PERIOD', 'SUBSCRIPTION_STATE_CANCELED')
                      AND s.acknowledgement_state IN ('ACKNOWLEDGEMENT_STATE_PENDING', 'ACKNOWLEDGEMENT_STATE_ACKNOWLEDGED')
                ) SELECT r.firebase_auth_uid, r.coin_id, r.symbol FROM ranked r
                  LEFT JOIN entitled e ON e.firebase_auth_uid = r.firebase_auth_uid
                  WHERE r.rn <= CASE WHEN e.firebase_auth_uid IS NULL THEN %s ELSE %s END
                  ORDER BY r.firebase_auth_uid, r.rn''', (
                    self.scope, self.reader.push_scope, self.reader.subscription_scope,
                    self.reader.package, self.config.free.monitored_asset_limit,
                    self.config.pro.monitored_asset_limit))
                return tuple(ActiveAsset(*row) for row in cursor.fetchall())
        finally:
            connection.close()


class IndividualMonitoringRuntime:
    """Single worker owns samples. Market reads shared by canonical ID, never broadcast."""
    def __init__(self, *, reader, provider, batch_size=50):
        if type(batch_size) is not int or not 1 <= batch_size <= 50:
            raise ValueError('Invalid batch size.')
        self.reader = reader
        self.provider = provider
        self.batch_size = batch_size
        self._states = {}
        self._snapshot = MappingProxyType({})

    @property
    def snapshot(self):
        return self._snapshot

    def run_once(self):
        # Never expose previous account authorization as current on a failed read.
        self._snapshot = MappingProxyType({})
        assets = self.reader.load_active()
        ids = sorted({asset.coin_id for asset in assets})
        self._states = {key: state for key, state in self._states.items() if key in ids}
        fresh = set()
        for start in range(0, len(ids), self.batch_size):
            group = ids[start:start + self.batch_size]
            targets = [MonitoringTarget(symbol=key.upper(), coin_id=key) for key in group]
            try:
                payload = self.provider.fetch_market_data_batch(targets)
            except Exception:
                logger.warning('Individual monitoring market batch unavailable.')
                continue
            for target in targets:
                key = target.coin_id
                try:
                    data = payload.get(target.symbol)
                    if not isinstance(data, dict) or data.get('id') != key:
                        continue
                    # Never invent a source timestamp or treat an old sample as new.
                    stamp = data.get('last_updated')
                    if not isinstance(stamp, str):
                        continue
                    timestamp = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
                    if timestamp.tzinfo is None:
                        continue
                    observation = build_monitoring_observation(target, data)
                    state = self._states.get(key, MonitoringState(target=target))
                    if state.current_observation is not None and timestamp <= state.current_observation.observed_at:
                        continue
                    self._states[key] = state.observe(observation)
                    fresh.add(key)
                except (ValueError, TypeError, AttributeError, OverflowError):
                    continue
        # This snapshot is internal only; user-facing access must reauthorize.
        self._snapshot = MappingProxyType({(a.uid, a.coin_id): self._states[a.coin_id]
                                           for a in assets if a.coin_id in fresh})
        return len(self._snapshot)


def _enabled():
    return all(os.getenv(flag, '').strip().lower() == 'true' for flag in (
        'CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED',
        'CRYPTORADAR_INDIVIDUAL_MONITORING_RUNTIME_ENABLED'))


def create_runtime():
    from app.monitoring.individual_monitoring_api import create_individual_monitoring_service
    from app.access.access_api_config import AccessApiConfig
    from app.monitoring.coingecko_monitoring_market_data_provider import CoinGeckoMonitoringMarketDataProvider
    service = create_individual_monitoring_service()
    return IndividualMonitoringRuntime(reader=ActiveWatchlistReader(access=service.access,
        scope_key=AccessApiConfig.from_environment().scope_key),
        provider=CoinGeckoMonitoringMarketDataProvider())


async def run_loop(stop, *, factory, interval):
    if interval <= 0:
        raise ValueError('Invalid interval.')
    runtime = None
    while not stop.is_set():
        try:
            if runtime is None:
                runtime = await asyncio.to_thread(factory)
            if not stop.is_set():
                await asyncio.to_thread(runtime.run_once)
        except Exception:
            logger.warning('Individual monitoring cycle unavailable.')
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def individual_monitoring_lifespan(app, *, base_lifespan=None, enabled=None,
                                        factory=None, interval=60):
    if base_lifespan is None:
        from app.billing.subscription_lifecycle_runtime import subscription_refresh_lifespan
        base_lifespan = subscription_refresh_lifespan
    async with base_lifespan(app) as state:
        if not (_enabled() if enabled is None else enabled):
            yield state
            return
        stop = asyncio.Event()
        task = asyncio.create_task(run_loop(stop, factory=factory or create_runtime, interval=interval))
        try:
            yield state
        finally:
            stop.set()
            await task
