from fastapi.testclient import TestClient

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    AssetOperationalRangeRecurrenceAssessment,
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


def test_operational_range_recurrence_reaches_http_response(
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
            "current_price": 102.5,
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
        assert current_price == 102.5

        return AssetOperationalRangeAssessment(
            current_price=102.5,
            lower_limit=100.0,
            upper_limit=105.0,
            amplitude_percent=5.0,
            position_percent=50.0,
            distance_to_lower_percent=2.439024,
            distance_to_upper_percent=2.439024,
            observed_points_count=9,
            is_operational_amplitude=True,
        )

    def fake_recurrence_fetch(
        self,
        *,
        asset_id: str,
        current_price: float,
    ):
        assert asset_id == "uniswap"
        assert current_price == 102.5

        return (
            AssetOperationalRangeRecurrenceAssessment(
                lower_limit_touches=2,
                upper_limit_touches=2,
                observed_points_count=9,
                total_limit_touches=4,
                completed_oscillations=2,
                has_both_limits_tested=True,
                has_minimum_recurrence=True,
                has_strong_recurrence=False,
                is_unbalanced=False,
                suggests_recurring_range=True,
                suggests_organized_oscillation=False,
                state="recurring_range",
            )
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

    monkeypatch.setattr(
        CryptoAssetOperationalRangeProvider,
        "fetch_recurrence",
        fake_recurrence_fetch,
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": (
                "A faixa da UNI tem recorrência?"
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

    assert (
        "2 toques no limite inferior"
        in answer
    )

    assert (
        "2 toques no limite superior"
        in answer
    )

    assert (
        "2 oscilações completas"
        in answer
    )

    assert (
        "recorrência mínima"
        in answer
    )