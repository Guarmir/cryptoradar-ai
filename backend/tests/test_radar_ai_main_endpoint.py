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

    assert body["answer"]

    assert isinstance(
        body["answer"],
        str,
    )

    assert body["items"]


def test_main_app_runs_asset_analysis_endpoint(
    monkeypatch,
) -> None:
    class FakeMarketOverviewProvider:
        pass

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            assert asset_id == "uniswap"

            return {
                "id": "uniswap",
                "symbol": "uni",
                "name": "Uniswap",
                "current_price": 12.50,
                "market_cap": 7_500_000_000,
                "total_volume": 650_000_000,
                "price_change_percentage_24h": 4.2,
            }

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
            "question": "Como está a UNI?",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["question"] == (
        "Como está a UNI?"
    )

    assert body["intent"] == (
        "asset_analysis"
    )

    assert body["market"] == "crypto"

    assert body["supported"] is True

    assert body["source"] == (
        "cryptoradar_asset_analysis"
    )

    assert body["source_version"] == "v1"

    assert body["answer"]

    assert "Uniswap" in body["answer"]

    assert body["items"]

def test_main_app_returns_focused_asset_answers(
    monkeypatch,
) -> None:
    class FakeMarketOverviewProvider:
        pass

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            assert asset_id == "uniswap"

            return {
                "id": "uniswap",
                "symbol": "uni",
                "name": "Uniswap",
                "current_price": 12.50,
                "market_cap": 7_500_000_000,
                "total_volume": 650_000_000,
                "price_change_percentage_24h": 4.2,
            }

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

    cases = (
        (
            "Qual o preço da UNI?",
            "12.50000000",
            "/100",
        ),
        (
            "Qual o score da UNI?",
            "65/100",
            "12.50000000",
        ),
        (
            "Quanto a UNI variou hoje?",
            "+4.20%",
            "65/100",
        ),
        (
            "Quais os riscos da UNI?",
            "Falta de confirmação",
            "12.50000000",
        ),
    )

    for (
        question,
        expected_fragment,
        unexpected_fragment,
    ) in cases:
        response = client.post(
            "/ai/radar/ask",
            json={
                "question": question,
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

        assert expected_fragment in (
            body["answer"]
        )

        assert unexpected_fragment not in (
            body["answer"]
        )
def test_main_app_returns_explanatory_asset_answer(
    monkeypatch,
) -> None:
    class FakeMarketOverviewProvider:
        pass

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            assert asset_id == "uniswap"

            return {
                "id": "uniswap",
                "symbol": "uni",
                "name": "Uniswap",
                "current_price": 12.50,
                "market_cap": 7_500_000_000,
                "total_volume": 650_000_000,
                "price_change_percentage_24h": 4.2,
            }

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
                "Por que a UNI está "
                "com esse sinal?"
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

    items = {
        item["key"]: item["content"]
        for item in body["items"]
    }

    answer = body["answer"]

    expected_keys = (
        "asset_score",
        "asset_signal",
        "asset_reasons",
        "asset_risks",
        "asset_invalidation",
    )

    for key in expected_keys:
        assert key in items
        assert items[key].strip()
        assert items[key] in answer

    assert (
        items["asset_price"]
        not in answer
    )

def test_main_app_returns_asset_comparison_answer(
    monkeypatch,
) -> None:
    class FakeMarketOverviewProvider:
        pass

    markets = {
        "uniswap": {
            "id": "uniswap",
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 12.50,
            "market_cap": 7_500_000_000,
            "total_volume": 650_000_000,
            "price_change_percentage_24h": 4.2,
        },
        "solana": {
            "id": "solana",
            "symbol": "sol",
            "name": "Solana",
            "current_price": 180.0,
            "market_cap": 85_000_000_000,
            "total_volume": 4_500_000_000,
            "price_change_percentage_24h": 2.1,
        },
    }

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            return markets[asset_id]

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
                "Qual está com melhor "
                "score, UNI ou SOL?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["intent"] == (
        "asset_comparison"
    )

    assert body["market"] == "crypto"

    assert body["source"] == (
        "cryptoradar_asset_comparison"
    )

    assert body["source_version"] == "v1"

    answer = body["answer"]

    assert "Uniswap (UNI)" in answer
    assert "Solana (SOL)" in answer

    assert "/100" in answer

    assert "12.50000000" not in answer
    assert "180.00000000" not in answer

def test_main_app_returns_quantitative_comparison_conclusion(
    monkeypatch,
) -> None:
    class FakeMarketOverviewProvider:
        pass

    markets = {
        "uniswap": {
            "id": "uniswap",
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 12.50,
            "market_cap": 7_500_000_000,
            "total_volume": 650_000_000,
            "price_change_percentage_24h": 4.2,
        },
        "solana": {
            "id": "solana",
            "symbol": "sol",
            "name": "Solana",
            "current_price": 180.0,
            "market_cap": 85_000_000_000,
            "total_volume": 4_500_000_000,
            "price_change_percentage_24h": 2.1,
        },
    }

    class FakeAssetProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            return markets[asset_id]

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
                "Qual tem maior volume "
                "entre UNI e SOL?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["intent"] == (
        "asset_comparison"
    )

    assert body["market"] == "crypto"

    assert body["source"] == (
        "cryptoradar_asset_comparison"
    )

    answer = body["answer"]

    assert (
        "Solana (SOL) apresenta "
        "maior volume em 24h"
        in answer
    )

    assert (
        "US$ 3,850,000,000"
        in answer
    )

    assert (
        "US$ 4,500,000,000"
        in answer
    )

    assert (
        "US$ 650,000,000"
        in answer
    )