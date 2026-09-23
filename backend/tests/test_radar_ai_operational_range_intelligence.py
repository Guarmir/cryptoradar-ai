import pytest

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


def _market():
    return {
        "id": "uniswap",
        "symbol": "uni",
        "name": "Uniswap",
        "current_price": 102.5,
        "market_cap": 10_000_000_000,
        "total_volume": 1_200_000_000,
        "price_change_percentage_24h": 2.5,
    }


def _range():
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


def _recurrence():
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

    def fetch_historical_average_volume(
        self,
        *,
        asset_id: str,
    ):
        return 1_000_000_000


@pytest.mark.parametrize(
    (
        "question",
        "expected",
    ),
    [
        (
            "Qual a qualidade da faixa da UNI?",
            "range_quality",
        ),
        (
            (
                "Qual o risco de invalidação "
                "da faixa da UNI?"
            ),
            "range_invalidation",
        ),
        (
            (
                "Qual o contexto operacional "
                "da UNI?"
            ),
            "range_context",
        ),
    ],
)
def test_resolves_operational_intelligence_focus(
    question: str,
    expected: str,
) -> None:
    resolver = (
        RadarAIAssetFocusResolver()
    )

    assert (
        resolver.resolve(
            question
        )
        == expected
    )


def _answer(
    question: str,
) -> str:
    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    context = service.build_context(
        question
    )

    return (
        RadarAIAnswerComposer()
        .compose(
            context,
            question,
        )
    )


def test_answers_range_quality() -> None:
    answer = _answer(
        "Qual a qualidade da faixa da UNI?"
    )

    assert (
        "qualidade operacional"
        in answer.lower()
    )

    assert "forte" in answer.lower()

    assert "Risk Score" not in answer


def test_answers_range_invalidation() -> None:
    answer = _answer(
        (
            "Qual o risco de invalidação "
            "da faixa da UNI?"
        )
    )

    assert (
        "risco estrutural observado"
        in answer.lower()
    )

    assert "baixo" in answer.lower()


def test_answers_consolidated_context() -> None:
    answer = _answer(
        "Qual o contexto operacional da UNI?"
    )

    assert (
        "contexto operacional consolidado"
        in answer.lower()
    )

    assert "organizado" in answer.lower()

    assert (
        "região central"
        in answer.lower()
    )

    assert (
        "não representa recomendação"
        in answer.lower()
    )