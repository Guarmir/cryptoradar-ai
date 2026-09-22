import pytest

from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)


@pytest.mark.parametrize(
    (
        "question",
        "asset_id",
    ),
    [
        (
            "Analise AAVE",
            "aave",
        ),
        (
            "Como está Render?",
            "render-token",
        ),
        (
            "Qual o preço da SUI?",
            "sui",
        ),
        (
            "Como está PIPPIN?",
            "pippin",
        ),
    ],
)
def test_dynamic_asset_becomes_asset_analysis(
    question: str,
    asset_id: str,
) -> None:
    def dynamic_coin_resolver(
        candidate: str,
    ):
        mapping = {
            "aave": "aave",
            "render": "render-token",
            "sui": "sui",
            "pippin": "pippin",
        }

        return mapping.get(
            candidate
        )

    asset_resolver = (
        RadarAIAssetResolver(
            dynamic_coin_resolver=(
                dynamic_coin_resolver
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
        asset_resolver.resolve(
            question
        )
        == asset_id
    )

    assert (
        intent_resolver.resolve(
            question
        )
        == "asset_analysis"
    )