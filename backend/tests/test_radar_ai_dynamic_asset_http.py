from fastapi.testclient import TestClient

import app.ai.radar_ai_api as radar_ai_api
from app.main import app
from app.services import (
    market_data_service,
)


def test_dynamic_pippin_analysis_reaches_http(
    monkeypatch,
) -> None:
    resolver_calls = []

    def resolve_coin_id(
        candidate: str,
    ):
        resolver_calls.append(
            candidate
        )

        if candidate == "pippin":
            return "pippin"

        return None

    class FakeMarketOverviewProvider:
        pass

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            assert asset_id == "pippin"

            return {
                "id": "pippin",
                "symbol": "pippin",
                "name": "Pippin",
                "current_price": 0.1234,
                "market_cap": 120_000_000,
                "total_volume": 25_000_000,
                "price_change_percentage_24h": 3.5,
            }

    monkeypatch.setattr(
        market_data_service,
        "resolve_coin_id",
        resolve_coin_id,
    )

    monkeypatch.setattr(
        radar_ai_api,
        "CoinGeckoMarketOverviewProvider",
        FakeMarketOverviewProvider,
    )

    monkeypatch.setattr(
        radar_ai_api,
        "CryptoAssetAnalysisProvider",
        FakeAssetProvider,
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": (
                "Qual o preço da PIPPIN?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["intent"] == (
        "asset_analysis"
    )

    assert body["market"] == "crypto"

    assert body["source"] == (
        "cryptoradar_asset_analysis"
    )

    assert (
        "0.12340000"
        in body["answer"]
    )

    assert "/100" not in (
        body["answer"]
    )

    assert resolver_calls.count(
        "pippin"
    ) == 1