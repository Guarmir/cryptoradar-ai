from app.ai.coingecko_market_overview_provider import (
    CoinGeckoMarketOverviewProvider,
)
from app.ai.market_domain import (
    MarketDomain,
)
from app.ai.market_overview_provider import (
    MarketOverviewProvider,
)


def test_market_domains_are_available():
    assert MarketDomain.CRYPTO.value == (
        "crypto"
    )

    assert MarketDomain.STOCKS.value == (
        "stocks"
    )

    assert MarketDomain.FOREX.value == (
        "forex"
    )

    assert (
        MarketDomain.COMMODITIES.value
        == "commodities"
    )


def test_coingecko_is_market_provider():
    provider = (
        CoinGeckoMarketOverviewProvider()
    )

    assert isinstance(
        provider,
        MarketOverviewProvider,
    )


def test_coingecko_domain_is_crypto():
    provider = (
        CoinGeckoMarketOverviewProvider()
    )

    assert (
        provider.domain
        == MarketDomain.CRYPTO
    )


def test_market_domain_is_string_compatible():
    assert (
        MarketDomain.CRYPTO
        == "crypto"
    )