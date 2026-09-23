import pytest
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


def _fake_resolve(
    self,
    question: str,
):
    return "uniswap"


def _fake_market_fetch(
    self,
    asset_id: str,
):
    assert asset_id == "uniswap"

    return {
        "id": "uniswap",
        "symbol": "uni",
        "name": "Uniswap",
        "current_price": 102.5,
        "market_cap": 10_000_000_000,
        "total_volume": 1_200_000_000,
        "price_change_percentage_24h": 2.5,
    }


def _fake_range_fetch(
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
        observed_points_count=11,
        is_operational_amplitude=True,
    )


def _fake_recurrence_fetch(
    self,
    *,
    asset_id: str,
    current_price: float,
):
    assert asset_id == "uniswap"
    assert current_price == 102.5

    return (
        AssetOperationalRangeRecurrenceAssessment(
            lower_limit_touches=3,
            upper_limit_touches=3,
            observed_points_count=11,
            total_limit_touches=6,
            completed_oscillations=3,
            has_both_limits_tested=True,
            has_minimum_recurrence=True,
            has_strong_recurrence=True,
            is_unbalanced=False,
            suggests_recurring_range=True,
            suggests_organized_oscillation=True,
            state="organized_oscillation",
        )
    )


def _fake_historical_volume_fetch(
    self,
    *,
    asset_id: str,
):
    assert asset_id == "uniswap"

    return 1_000_000_000


@pytest.mark.parametrize(
    (
        "question",
        "expected_fragments",
    ),
    [
        (
            "Qual a qualidade da faixa da UNI?",
            (
                "qualidade operacional",
                "forte",
            ),
        ),
        (
            (
                "Qual o risco de invalidação "
                "da faixa da UNI?"
            ),
            (
                "risco estrutural observado",
                "baixo",
            ),
        ),
        (
            (
                "Qual o contexto operacional "
                "da UNI?"
            ),
            (
                "contexto operacional consolidado",
                "organizado",
                "região central",
                "não representa recomendação",
            ),
        ),
    ],
)
def test_operational_range_intelligence_reaches_http(
    monkeypatch,
    question: str,
    expected_fragments: tuple[str, ...],
) -> None:
    monkeypatch.setattr(
        RadarAIAssetResolver,
        "resolve",
        _fake_resolve,
    )

    monkeypatch.setattr(
        CryptoAssetAnalysisProvider,
        "fetch",
        _fake_market_fetch,
    )

    monkeypatch.setattr(
        CryptoAssetOperationalRangeProvider,
        "fetch",
        _fake_range_fetch,
    )

    monkeypatch.setattr(
        CryptoAssetOperationalRangeProvider,
        "fetch_recurrence",
        _fake_recurrence_fetch,
    )

    monkeypatch.setattr(
        CryptoAssetOperationalRangeProvider,
        "fetch_historical_average_volume",
        _fake_historical_volume_fetch,
    )

    client = TestClient(app)

    response = client.post(
        "/ai/radar/ask",
        json={
            "question": question,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["supported"] is True

    assert (
        body["source"]
        == "cryptoradar_asset_analysis"
    )

    answer = body["answer"]

    for fragment in expected_fragments:
        assert (
            fragment
            in answer.lower()
        )

    assert "Risk Score" not in answer