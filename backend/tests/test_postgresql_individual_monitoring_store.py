from unittest.mock import MagicMock
import pytest
from app.monitoring.postgresql_individual_monitoring_store import (
    IndividualMonitoringAsset, IndividualMonitoringLimitReached,
    PostgreSQLIndividualMonitoringStore,
)


@pytest.fixture
def setup_store():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    store = PostgreSQLIndividualMonitoringStore(database_url='db', scope_key='scope',
                                                connection_factory=lambda _: conn)
    return store, conn, cursor


def test_asset_normalizes_canonical_identity():
    assert IndividualMonitoringAsset(' Bitcoin ', ' btc ') == IndividualMonitoringAsset('bitcoin', 'BTC')


@pytest.mark.parametrize('coin_id,symbol', [('', 'BTC'), ('bitcoin', ''), ('x'*201, 'BTC'), ('bitcoin', '\x00')])
def test_invalid_asset(coin_id, symbol):
    with pytest.raises(ValueError):
        IndividualMonitoringAsset(coin_id, symbol)


def test_add_locks_before_count_and_insert(setup_store):
    store, conn, cursor = setup_store
    cursor.fetchone.side_effect = [None, (9,)]
    asset = IndividualMonitoringAsset('bitcoin', 'BTC')
    assert store.add(uid='alice', asset=asset, limit=10) == asset
    calls = cursor.execute.call_args_list
    assert 'pg_advisory_xact_lock' in calls[0].args[0]
    assert calls[2].args[1] == ('scope', 'alice')
    assert calls[3].args[1] == ('scope', 'alice', 'bitcoin', 'BTC')
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.parametrize('limit', [1, 10])
def test_limit_blocks_insert(setup_store, limit):
    store, conn, cursor = setup_store
    cursor.fetchone.side_effect = [None, (limit,)]
    with pytest.raises(IndividualMonitoringLimitReached):
        store.add(uid='alice', asset=IndividualMonitoringAsset('bitcoin', 'BTC'), limit=limit)
    assert cursor.execute.call_count == 3
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()


def test_duplicate_is_idempotent_even_at_limit(setup_store):
    store, conn, cursor = setup_store
    cursor.fetchone.return_value = ('BTC',)
    assert store.add(uid='alice', asset=IndividualMonitoringAsset('bitcoin', 'OTHER'), limit=1).symbol == 'BTC'
    assert cursor.execute.call_count == 2
    conn.commit.assert_called_once()


def test_load_preserves_distinct_ids_with_same_symbol(setup_store):
    store, conn, cursor = setup_store
    cursor.fetchall.return_value = [('one', 'ABC'), ('two', 'ABC')]
    assert len(store.load_all(uid='alice')) == 2
    assert cursor.execute.call_args.args[1] == ('scope', 'alice')
    conn.close.assert_called_once()


def test_remove_scoped_and_locked(setup_store):
    store, conn, cursor = setup_store
    cursor.rowcount = 1
    assert store.remove(uid='bob', coin_id=' Bitcoin ')
    assert cursor.execute.call_args.args[1] == ('scope', 'bob', 'bitcoin')
    conn.commit.assert_called_once()


def test_failed_write_rolls_back(setup_store):
    store, conn, cursor = setup_store
    cursor.execute.side_effect = RuntimeError('database failure')
    with pytest.raises(RuntimeError):
        store.remove(uid='alice', coin_id='bitcoin')
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.parametrize('limit', [0, 11, True])
def test_invalid_limit_rejected(setup_store, limit):
    store, conn, cursor = setup_store
    with pytest.raises(ValueError):
        store.add(uid='alice', asset=IndividualMonitoringAsset('bitcoin', 'BTC'), limit=limit)
    cursor.execute.assert_not_called()
