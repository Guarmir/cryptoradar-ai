
import pytest

from app.early_movement.extreme_movement.extreme_movement_market_provider import (
    ExtremeMovementMarketProvider,
)
from app.early_movement.scanner.coingecko_scanner_market_provider import (
    EarlyMovementScannerDataError,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def make_asset(coin_id, rank):
    return {
        "id": coin_id,
        "symbol": coin_id,
        "name": coin_id.upper(),
        "current_price": 1.0,
        "total_volume": 1000000,
        "market_cap": 5000000,
        "price_change_percentage_24h": 15.0,
        "market_cap_rank": rank,
    }


def test_fetches_complementary_pages():
    pages = []

    def fake_get(url, *, params, headers, timeout):
        pages.append(params["page"])
        return FakeResponse(
            [make_asset(f"coin-{params['page']}", 300)]
        )

    provider = ExtremeMovementMarketProvider(
        request_get=fake_get,
    )

    assets = provider.fetch()

    assert pages == [2, 3]
    assert len(assets) == 2
    assert {asset.coin_id for asset in assets} == {
        "coin-2",
        "coin-3",
    }


def test_removes_duplicate_coin_ids():
    def fake_get(url, *, params, headers, timeout):
        return FakeResponse([make_asset("same-coin", 300)])

    provider = ExtremeMovementMarketProvider(
        request_get=fake_get,
    )

    assets = provider.fetch()

    assert len(assets) == 1
    assert assets[0].coin_id == "same-coin"


def test_ignores_invalid_assets():
    def fake_get(url, *, params, headers, timeout):
        return FakeResponse(
            [
                {"id": "invalid", "current_price": 0},
                make_asset("valid-coin", 350),
            ]
        )

    provider = ExtremeMovementMarketProvider(
        request_get=fake_get,
        page_count=1,
    )

    assets = provider.fetch()

    assert len(assets) == 1
    assert assets[0].coin_id == "valid-coin"


def test_rejects_invalid_response():
    def fake_get(url, *, params, headers, timeout):
        return FakeResponse({"error": "invalid"})

    provider = ExtremeMovementMarketProvider(
        request_get=fake_get,
        page_count=1,
    )

    with pytest.raises(
        EarlyMovementScannerDataError,
        match="Resposta complementar",
    ):
        provider.fetch()


def test_rejects_rate_limit():
    def fake_get(url, *, params, headers, timeout):
        return FakeResponse([], status_code=429)

    provider = ExtremeMovementMarketProvider(
        request_get=fake_get,
        page_count=1,
    )

    with pytest.raises(
        EarlyMovementScannerDataError,
        match="Limite temporário",
    ):
        provider.fetch()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_page": 1},
        {"page_count": 0},
        {"page_count": 5},
        {"timeout": 0},
    ],
)
def test_rejects_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        ExtremeMovementMarketProvider(**kwargs)
