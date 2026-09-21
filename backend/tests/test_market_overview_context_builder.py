import pytest

from app.ai.assistant_intent import (
    AssistantIntent,
)
from app.ai.market_overview_context_builder import (
    MARKET_OVERVIEW_SOURCE,
    MARKET_OVERVIEW_VERSION,
    build_market_overview_context,
)
from app.ai.market_overview_context_service import (
    MarketOverviewContextService,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewAsset,
    MarketOverviewSnapshot,
)


def _snapshot():
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
            MarketOverviewAsset(
                symbol="eth",
                name="Ethereum",
                price_usd=4_000,
                change_24h_percent=-1.0,
                market_cap_usd=(
                    480_000_000_000
                ),
                volume_24h_usd=(
                    20_000_000_000
                ),
            ),
            MarketOverviewAsset(
                symbol="sol",
                name="Solana",
                price_usd=200,
                change_24h_percent=5.0,
                market_cap_usd=(
                    100_000_000_000
                ),
                volume_24h_usd=(
                    8_000_000_000
                ),
            ),
        ),
    )


def test_builds_market_overview_context():
    context = (
        build_market_overview_context(
            _snapshot(),
        )
    )

    assert context.is_supported

    assert context.intent == (
        AssistantIntent
        .MARKET_OVERVIEW
    )

    assert (
        context.source
        == MARKET_OVERVIEW_SOURCE
    )

    assert (
        context.source_version
        == MARKET_OVERVIEW_VERSION
    )


def test_context_contains_global_market():
    context = (
        build_market_overview_context(
            _snapshot(),
        )
    )

    rendered = context.render()

    assert "Mercado global" in rendered
    assert "Dominancia BTC" in rendered
    assert "+2.50%" in rendered


def test_context_contains_market_breadth():
    context = (
        build_market_overview_context(
            _snapshot(),
        )
    )

    rendered = context.render()

    assert "2 ativos estao em alta" in (
        rendered
    )

    assert "1 estao em queda" in (
        rendered
    )


def test_context_contains_major_assets():
    context = (
        build_market_overview_context(
            _snapshot(),
        )
    )

    rendered = context.render()

    assert "BTC" in rendered
    assert "ETH" in rendered
    assert "SOL" in rendered


def test_context_contains_relevant_moves():
    context = (
        build_market_overview_context(
            _snapshot(),
        )
    )

    rendered = context.render()

    assert "SOL +5.00%" in rendered
    assert "ETH -1.00%" in rendered


def test_mover_limit_is_respected():
    context = (
        build_market_overview_context(
            _snapshot(),
            mover_limit=1,
        )
    )

    major_assets = next(
        item
        for item in context.items
        if item.key == "major_assets"
    )

    assert "BTC" in (
        major_assets.content
    )

    assert "ETH" not in (
        major_assets.content
    )


def test_invalid_mover_limit_is_rejected():
    with pytest.raises(
        ValueError
    ):
        build_market_overview_context(
            _snapshot(),
            mover_limit=0,
        )


def test_context_service_uses_provider():
    class FakeProvider:
        def fetch(
            self,
        ):
            return _snapshot()

    service = (
        MarketOverviewContextService(
            provider=FakeProvider(),
        )
    )

    context = (
        service.build_context()
    )

    assert context.is_supported
    assert (
        context.intent
        == AssistantIntent
        .MARKET_OVERVIEW
    )