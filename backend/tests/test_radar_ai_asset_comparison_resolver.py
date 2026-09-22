import pytest

from app.ai.radar_ai_asset_comparison_resolver import (
    RadarAIAssetComparisonResolver,
)
from app.ai.radar_ai_asset_resolver import (
    RadarAIAssetResolver,
)
from app.ai.radar_ai_intent_resolver import (
    RadarAIIntentResolver,
)


@pytest.mark.parametrize(
    (
        "question",
        "expected",
    ),
    [
        (
            "Compare UNI e SOL",
            (
                "uniswap",
                "solana",
            ),
        ),
        (
            "Compare o risco de BTC e ETH",
            (
                "bitcoin",
                "ethereum",
            ),
        ),
        (
            (
                "Qual está com melhor "
                "score, UNI ou SOL?"
            ),
            (
                "uniswap",
                "solana",
            ),
        ),
    ],
)
def test_resolves_two_known_assets(
    question: str,
    expected: tuple[str, str],
) -> None:
    resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                lambda candidate: None
            ),
        )
    )

    assert resolver.resolve(
        question
    ) == expected


def test_resolves_known_and_dynamic_asset() -> None:
    received = []

    def dynamic_coin_resolver(
        candidate: str,
    ):
        received.append(
            candidate
        )

        mapping = {
            "aave": "aave",
        }

        return mapping.get(
            candidate
        )

    resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                dynamic_coin_resolver
            ),
        )
    )

    assert resolver.resolve(
        "Compare UNI e AAVE"
    ) == (
        "uniswap",
        "aave",
    )

    assert "aave" in received


def test_resolves_two_dynamic_assets() -> None:
    mapping = {
        "sui": "sui",
        "aave": "aave",
    }

    resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                lambda candidate: (
                    mapping.get(candidate)
                )
            ),
        )
    )

    assert resolver.resolve(
        "Compare SUI e AAVE"
    ) == (
        "sui",
        "aave",
    )


def test_comparison_intent_has_priority() -> None:
    mapping = {
        "aave": "aave",
    }

    comparison_resolver = (
        RadarAIAssetComparisonResolver(
            dynamic_coin_resolver=(
                lambda candidate: (
                    mapping.get(candidate)
                )
            ),
        )
    )

    asset_resolver = (
        RadarAIAssetResolver(
            dynamic_coin_resolver=(
                lambda candidate: (
                    mapping.get(candidate)
                )
            ),
        )
    )

    resolver = RadarAIIntentResolver(
        asset_resolver=asset_resolver,
        asset_comparison_resolver=(
            comparison_resolver
        ),
    )

    assert resolver.resolve(
        "Compare UNI e AAVE"
    ) == "asset_comparison"


def test_single_asset_remains_asset_analysis() -> None:
    resolver = RadarAIIntentResolver(
        asset_comparison_resolver=(
            RadarAIAssetComparisonResolver(
                dynamic_coin_resolver=(
                    lambda candidate: None
                ),
            )
        ),
        asset_resolver=(
            RadarAIAssetResolver(
                dynamic_coin_resolver=(
                    lambda candidate: None
                ),
            )
        ),
    )

    assert resolver.resolve(
        "Qual o score da UNI?"
    ) == "asset_analysis"


def test_market_question_remains_market_overview() -> None:
    resolver = RadarAIIntentResolver(
        asset_comparison_resolver=(
            RadarAIAssetComparisonResolver(
                dynamic_coin_resolver=(
                    lambda candidate: None
                ),
            )
        ),
        asset_resolver=(
            RadarAIAssetResolver(
                dynamic_coin_resolver=(
                    lambda candidate: None
                ),
            )
        ),
    )

    assert resolver.resolve(
        "Como está o mercado cripto?"
    ) == "market_overview"