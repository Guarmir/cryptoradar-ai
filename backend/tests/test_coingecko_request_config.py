from app.services.coingecko_request_config import (
    CoinGeckoRequestConfig,
)


def test_headers_without_api_key_preserve_defaults() -> None:
    config = CoinGeckoRequestConfig(
        api_key=None,
    )

    assert config.headers == {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
    }


def test_headers_include_demo_api_key() -> None:
    config = CoinGeckoRequestConfig(
        api_key="demo-secret",
    )

    assert config.headers == {
        "Accept": "application/json",
        "User-Agent": "CryptoRadar/2.0",
        "x-cg-demo-api-key": "demo-secret",
    }


def test_config_reads_demo_key_from_environment() -> None:
    config = (
        CoinGeckoRequestConfig
        .from_environment(
            {
                "COINGECKO_DEMO_API_KEY": (
                    "environment-secret"
                ),
            }
        )
    )

    assert (
        config.api_key
        == "environment-secret"
    )

    assert (
        config.headers[
            "x-cg-demo-api-key"
        ]
        == "environment-secret"
    )


def test_config_ignores_blank_api_key() -> None:
    config = (
        CoinGeckoRequestConfig
        .from_environment(
            {
                "COINGECKO_DEMO_API_KEY": "   ",
            }
        )
    )

    assert config.api_key is None

    assert (
        "x-cg-demo-api-key"
        not in config.headers
    )