import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.monitoring.individual_monitoring_runtime import (
    ActiveAsset, ActiveWatchlistReader, IndividualMonitoringRuntime,
    individual_monitoring_lifespan, run_loop, _enabled,
)


class Reader:
    def __init__(self, assets):
        self.assets = assets
    def load_active(self):
        return self.assets


class Provider:
    def __init__(self):
        self.calls = []
        self.stamp = '2026-11-27T08:00:00Z'
        self.price = 10
    def fetch_market_data_batch(self, targets):
        self.calls.append([t.coin_id for t in targets])
        return {t.symbol: {'id': t.coin_id, 'current_price': self.price,
                           'last_updated': self.stamp} for t in targets}


def make():
    reader = Reader([ActiveAsset('a','coin-one','ABC'), ActiveAsset('b','coin-one','ABC'),
                     ActiveAsset('a','coin-two','ABC')])
    provider = Provider()
    return reader, provider, IndividualMonitoringRuntime(reader=reader, provider=provider)


def test_shared_market_read_and_canonical_identity():
    _, provider, runtime = make()
    assert runtime.run_once() == 3
    assert provider.calls == [['coin-one','coin-two']]
    assert runtime.snapshot['a','coin-one'] is runtime.snapshot['b','coin-one']
    assert runtime.snapshot['a','coin-one'] is not runtime.snapshot['a','coin-two']


def test_removed_or_excess_assets_disappear_without_deleting_watchlist():
    reader, provider, runtime = make()
    runtime.run_once()
    reader.assets = [ActiveAsset('a','coin-two','ABC')]
    provider.stamp = '2026-11-27T08:01:00Z'
    assert runtime.run_once() == 1
    assert set(runtime.snapshot) == {('a','coin-two')}
    assert set(runtime._states) == {'coin-two'}


def test_restart_reads_persisted_selection_again():
    reader, provider, runtime = make()
    runtime.run_once()
    restarted = IndividualMonitoringRuntime(reader=reader, provider=provider)
    assert restarted.run_once() == 3
    assert restarted.snapshot['a','coin-one'].observation_count == 1


def test_previous_observation_and_duplicate_timestamp():
    _, provider, runtime = make()
    runtime.run_once()
    assert runtime.run_once() == 0
    provider.stamp = '2026-11-27T08:01:00Z'
    provider.price = 11
    runtime.run_once()
    state = runtime.snapshot['a','coin-one']
    assert state.observation_count == 2
    assert state.price_change_since_previous_percent == 10


@pytest.mark.parametrize('bad', [None, '', 'invalid', '2026-11-27T08:00:00'])
def test_missing_or_invalid_timestamp_not_fabricated(bad):
    _, provider, runtime = make()
    provider.stamp = bad
    assert runtime.run_once() == 0


def test_failed_authorization_read_clears_snapshot():
    reader, _, runtime = make()
    runtime.run_once()
    reader.load_active = MagicMock(side_effect=RuntimeError('db'))
    with pytest.raises(RuntimeError):
        runtime.run_once()
    assert not runtime.snapshot


def test_batch_failure_isolated():
    reader, provider, _ = make()
    original = provider.fetch_market_data_batch
    def fetch(targets):
        if targets[0].coin_id == 'coin-one':
            raise RuntimeError('network')
        return original(targets)
    provider.fetch_market_data_batch = fetch
    runtime = IndividualMonitoringRuntime(reader=reader, provider=provider, batch_size=1)
    assert runtime.run_once() == 1
    assert set(runtime.snapshot) == {('a','coin-two')}


def test_sql_scopes_freshness_and_rank():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [('a','bitcoin','BTC')]
    access = SimpleNamespace(reader=SimpleNamespace(url='db',push_scope='push',
        subscription_scope='sub',package='pkg'), config=SimpleNamespace(
        free=SimpleNamespace(monitored_asset_limit=1),pro=SimpleNamespace(monitored_asset_limit=10)))
    reader = ActiveWatchlistReader(access=access, scope_key='watch', connection_factory=lambda _:conn)
    assert reader.load_active() == (ActiveAsset('a','bitcoin','BTC'),)
    sql, params = cursor.execute.call_args.args
    assert params == ('watch','push','sub','pkg',1,10)
    for clause in ['row_number()', 'a.created_at, a.coin_id', 'g.valid_until > NOW()',
                   's.expires_at > NOW()', 's.verified_at > NOW()', 'o.firebase_auth_uid = g.firebase_auth_uid',
                   's.firebase_auth_uid = g.firebase_auth_uid', 'r.rn <= CASE']:
        assert clause in sql
    conn.close.assert_called_once()


def test_double_opt_in(monkeypatch):
    monkeypatch.setenv('CRYPTORADAR_INDIVIDUAL_MONITORING_ENABLED','true')
    monkeypatch.delenv('CRYPTORADAR_INDIVIDUAL_MONITORING_RUNTIME_ENABLED',raising=False)
    assert not _enabled()
    monkeypatch.setenv('CRYPTORADAR_INDIVIDUAL_MONITORING_RUNTIME_ENABLED','true')
    assert _enabled()


def test_disabled_lifespan_preserves_base():
    calls = []
    @asynccontextmanager
    async def base(app):
        calls.append('start')
        yield 'state'
        calls.append('stop')
    async def scenario():
        async with individual_monitoring_lifespan(None, base_lifespan=base, enabled=False,
                factory=lambda: pytest.fail('worker started')) as state:
            assert state == 'state'
    asyncio.run(scenario())
    assert calls == ['start','stop']


def test_worker_retries_and_stops():
    async def scenario():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        calls = []
        class Runtime:
            def run_once(self):
                calls.append('cycle')
                if len(calls) == 1:
                    raise RuntimeError('network')
                loop.call_soon_threadsafe(stop.set)
        await asyncio.wait_for(run_loop(stop, factory=Runtime, interval=.01),2)
        assert calls == ['cycle','cycle']
    asyncio.run(scenario())
