from fastapi.testclient import TestClient

import app.ai.radar_ai_api as radar_ai_api
from app.ai.market_domain import (
    MarketDomain,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)
from app.main import app


def _snapshot() -> MarketOverviewSnapshot:
    return MarketOverviewSnapshot(
        total_market_cap_usd=(
            2_500_000_000_000
        ),
        total_volume_24h_usd=(
            120_000_000_000
        ),
        market_cap_change_24h_percent=2.5,
        btc_dominance_percent=55.0,
        eth_dominance_percent=12.0,
        assets=(
            MarketOverviewAsset(
                symbol="btc",
                name="Bitcoin",
                price_usd=100_000,
                change_24h_percent=3.0,
                market_cap_usd=(
                    2_000_000_000_000
                ),
                volume_24h_usd=(
                    50_000_000_000
                ),
            ),
        ),
    )


def test_main_app_runs_radar_ai_endpoint(
    monkeypatch,
) -> None:
    class FakeProvider:
        @property
        def domain(self):
            return MarketDomain.CRYPTO

        def fetch(self):
            return _snapshot()

    monkeypatch.setattr(
        radar_ai_api,
        "CoinGeckoMarketOverviewProvider",
        FakeProvider,
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": (
                "Como está o mercado "
                "cripto agora?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Como está o mercado cripto agora?"
    )

    assert body["intent"] == (
        "market_overview"
    )

    assert body["market"] == "crypto"
    assert body["supported"] is True

    assert body["source"] == (
        "cryptoradar_market_overview"
    )

    assert body["items"]