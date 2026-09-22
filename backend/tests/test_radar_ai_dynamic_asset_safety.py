import pytest

from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)


@pytest.mark.parametrize(
    "question",
    [
        "Como está o mercado hoje?",
        "Como está o mercado cripto agora?",
        "Como está o market hoje?",
        "Quero informações gerais.",
    ],
)
def test_general_questions_are_not_assets(
    question: str,
) -> None:
    received = []

    def dynamic_coin_resolver(
        candidate: str,
    ):
        received.append(
            candidate
        )

        return None

    asset_resolver = (
        RadarAIAssetResolver(
            dynamic_coin_resolver=(
                dynamic_coin_resolver
            ),
        )
    )

    assert (
        asset_resolver.resolve(
            question
        )
        is None
    )


def test_crypto_market_question_remains_market_overview() -> None:
    asset_resolver = (
        RadarAIAssetResolver(
            dynamic_coin_resolver=(
                lambda candidate: None
            ),
        )
    )

    intent_resolver = (
        RadarAIIntentResolver(
            asset_resolver=(
                asset_resolver
            ),
        )
    )

    assert (
        intent_resolver.resolve(
            "Como está o mercado cripto agora?"
        )
        == "market_overview"
    )