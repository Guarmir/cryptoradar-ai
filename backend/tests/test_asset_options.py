from fastapi import HTTPException
import pytest

from app.services import market_data_service
from app.services.routes.asset_router import create_asset_router


def _lookup(symbol):
    router = create_asset_router()
    endpoint = next(
        route.endpoint
        for route in router.routes
        if getattr(route, 'path', None) == '/asset-options/{symbol}'
    )
    return endpoint(symbol)


def test_asset_options_returns_all_ambiguous_symbols_without_guessing(monkeypatch):
    monkeypatch.setattr(
        market_data_service,
        'get_coin_list',
        lambda: [
            {'id': 'starknet', 'symbol': 'strk', 'name': 'Starknet'},
            {'id': 'strategy-strike-preferred-dinari-tokenized-stock', 'symbol': 'strk', 'name': 'Strategy Strike Preferred'},
            {'id': 'uniswap', 'symbol': 'uni', 'name': 'Uniswap'},
        ],
    )
    result = _lookup('STRK')
    assert [item['coin_id'] for item in result['candidates']] == [
        'starknet', 'strategy-strike-preferred-dinari-tokenized-stock'
    ]
    assert all(item['symbol'] == 'STRK' for item in result['candidates'])


def test_asset_options_accepts_full_canonical_id(monkeypatch):
    monkeypatch.setattr(
        market_data_service,
        'get_coin_list',
        lambda: [
            {'id': 'plasma', 'symbol': 'xpl', 'name': 'Plasma'},
            {'id': 'pulse-2', 'symbol': 'xpl', 'name': 'Pulse'},
        ],
    )
    result = _lookup('pulse-2')
    assert [item['coin_id'] for item in result['candidates']] == ['pulse-2']


def test_asset_options_never_guesses_or_returns_partial_matches(monkeypatch):
    monkeypatch.setattr(
        market_data_service,
        'get_coin_list',
        lambda: [{'id': 'uniswap', 'symbol': 'uni', 'name': 'Uniswap'}],
    )
    assert _lookup('nonsense')['candidates'] == []
    assert _lookup('un')['candidates'] == []


def test_asset_options_rejects_empty_query(monkeypatch):
    with pytest.raises(HTTPException) as error:
        _lookup('   ')
    assert error.value.status_code == 400
