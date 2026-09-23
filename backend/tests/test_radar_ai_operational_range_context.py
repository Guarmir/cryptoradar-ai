import pytest

from app.ai.asset_operational_range_assessment import (
    AssetOperationalRangeAssessment,
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
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)


def _market() -> dict:
    return {
        "id": "uniswap",
        "symbol": "uni",
        "name": "Uniswap",
        "current_price": 101.0,
        "market_cap": 7_500_000_000,
        "total_volume": 650_000_000,
        "price_change_percentage_24h": 2.5,
    }


def _range_assessment():
    return AssetOperationalRangeAssessment(
        current_price=101.0,
        lower_limit=100.0,
        upper_limit=105.0,
        amplitude_percent=5.0,
        position_percent=20.0,
        distance_to_lower_percent=(
            0.990099
        ),
        distance_to_upper_percent=(
            3.960396
        ),
        observed_points_count=4,
        is_operational_amplitude=True,
    )


@pytest.mark.parametrize(
    (
        "question",
        "expected",
    ),
    [
        (
            (
                "Onde a UNI está "
                "dentro da faixa?"
            ),
            "range_position",
        ),
        (
            (
                "Quanto espaço existe "
                "até a resistência da UNI?"
            ),
            "range_space",
        ),
        (
            (
                "A UNI está dentro da "
                "amplitude operacional?"
            ),
            "operational_range",
        ),
    ],
)
def test_resolves_operational_range_focus(
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


def test_dynamic_asset_supports_range_question() -> None:
    received = []

    def dynamic_resolver(
        candidate: str,
    ):
        received.append(
            candidate
        )

        if candidate == "pippin":
            return "pippin"

        return None

    resolver = RadarAIAssetResolver(
        dynamic_coin_resolver=(
            dynamic_resolver
        ),
    )

    assert (
        resolver.resolve(
            (
                "Onde PIPPIN está "
                "dentro da faixa?"
            )
        )
        == "pippin"
    )

    assert "pippin" in received


def test_context_contains_operational_range_data() -> None:
    class FakeMarketProvider:
        def fetch(
            self,
            asset_id: str,
        ):
            assert asset_id == "uniswap"

            return _market()

    class FakeRangeProvider:
        def fetch(
            self,
            *,
            asset_id: str,
            current_price: float,
        ):
            assert asset_id == "uniswap"
            assert current_price == 101.0

            return _range_assessment()

    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    context = service.build_context(
        (
            "Onde a UNI está "
            "dentro da faixa?"
        )
    )

    items = {
        item.key: item.content
        for item in context.items
    }

    assert (
        "asset_operational_range"
        in items
    )

    assert (
        "asset_operational_range_position"
        in items
    )

    assert (
        "asset_operational_range_space"
        in items
    )

    assert "5.00%" in (
        items[
            "asset_operational_range"
        ]
    )

    assert "20.00%" in (
        items[
            "asset_operational_range_position"
        ]
    )


def test_position_question_returns_focused_answer() -> None:
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
            return _range_assessment()

    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    question = (
        "Onde a UNI está "
        "dentro da faixa?"
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

    assert "5.00%" in answer
    assert "20.00%" in answer

    assert "Risk Score" not in answer


def test_space_question_returns_range_space() -> None:
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
            return _range_assessment()

    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    question = (
        "Quanto espaço existe até "
        "a resistência da UNI?"
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

    assert "0.99%" in answer
    assert "3.96%" in answer

    assert (
        "score atual"
        not in answer.lower()
    )


def test_range_unavailable_is_explained() -> None:
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
            return None

    service = (
        RadarAIAssetContextService(
            provider=FakeMarketProvider(),
            operational_range_provider=(
                FakeRangeProvider()
            ),
        )
    )

    question = (
        "Qual a faixa operacional "
        "da UNI?"
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
        "Não há histórico suficiente"
        in answer
    )