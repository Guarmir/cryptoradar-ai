from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
)
from app.ai.asset_operational_range_recurrence_assessment import (
    AssetOperationalRangeRecurrenceAssessment,
)
from app.ai.radar_ai_answer_composer import (
    RadarAIAnswerComposer,
)
from app.ai.radar_ai_asset_context_service import (
    RadarAIAssetContextService,
)
from app.ai.radar_ai_asset_focus_resolver import (
    RadarAIAssetFocusResolver,
)


def _market() -> dict:
    return {
        "id": "uniswap",
        "symbol": "uni",
        "name": "Uniswap",
        "current_price": 102.5,
        "market_cap": 7_500_000_000,
        "total_volume": 650_000_000,
        "price_change_percentage_24h": 2.5,
    }


def _range():
    return AssetOperationalRangeAssessment(
        current_price=102.5,
        lower_limit=100.0,
        upper_limit=105.0,
        amplitude_percent=5.0,
        position_percent=50.0,
        distance_to_lower_percent=(
            2.439024
        ),
        distance_to_upper_percent=(
            2.439024
        ),
        observed_points_count=9,
        is_operational_amplitude=True,
    )


def _recurrence():
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


def test_recurrence_question_uses_operational_range_focus() -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert (
        resolver.resolve(
            "A faixa da UNI tem recorrência?"
        )
        == "operational_range"
    )


def test_radar_ai_explains_range_recurrence() -> None:
    class FakeMarketProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            return _market()

    class FakeRangeProvider:
        def fetch(
            self,
            *,
            asset_id: str,
            current_price: float,
        ):
            return _range()

        def fetch_recurrence(
            self,
            *,
            asset_id: str,
            current_price: float,
        ):
            return _recurrence()

    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    question = (
        "A faixa da UNI tem recorrência?"
    )

    context = (
        service.build_context(
            question
        )
    )

    answer = (
        RadarAIAnswerComposer()
        .compose(
            context,
            question,
        )
    )

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

    assert (
        "oscilação organizada"
        in answer
    )

    assert "Risk Score" not in answer