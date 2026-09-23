from fastapi.testclient import TestClient

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)
from app.ai.crypto_asset_analysis_provider import (
    CryptoAssetAnalysisProvider,
)
from app.ai.crypto_asset_operational_range_provider import (
    CryptoAssetOperationalRangeProvider,
)
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.main import app


def test_operational_range_reaches_http_response(
    monkeypatch,
) -> None:
    def fake_resolve(
        self,
        question: str,
    ):
        return "uniswap"

    def fake_market_fetch(
        self,
        asset_id: str,
    ):
        assert asset_id == "uniswap"

        return {
            "id": "uniswap",
            "symbol": "uni",
            "name": "Uniswap",
            "current_price": 101.0,
            "market_cap": 7_500_000_000,
            "total_volume": 650_000_000,
            "price_change_percentage_24h": 2.5,
        }

    def fake_range_fetch(
        self,
        *,
        asset_id: str,
        current_price: float,
    ):
        assert asset_id == "uniswap"
        assert current_price == 101.0

        return AssetOperationalRangeAssessment(
            current_price=101.0,
            lower_limit=100.0,
            upper_limit=105.0,
            amplitude_percent=5.0,
            position_percent=20.0,
            distance_to_lower_percent=0.990099,
            distance_to_upper_percent=3.960396,
            observed_points_count=4,
            is_operational_amplitude=True,
        )

    monkeypatch.setattr(
        RadarAIAssetResolver,
        "resolve",
        fake_resolve,
    )

    monkeypatch.setattr(
        CryptoAssetAnalysisProvider,
        "fetch",
        fake_market_fetch,
    )

    monkeypatch.setattr(
        CryptoAssetOperationalRangeProvider,
        "fetch",
        fake_range_fetch,
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": (
                "Onde a UNI está dentro da faixa?"
            ),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["source"]
        == "cryptoradar_asset_analysis"
    )

    assert body["supported"] is True

    answer = body["answer"]

    assert "faixa recente observada" in (
        answer.lower()
    )

    assert "5.00%" in answer
    assert "20.00%" in answer

    assert (
        "limite inferior"
        in answer.lower()
    )

    assert (
        "limite superior"
        in answer.lower()
    )