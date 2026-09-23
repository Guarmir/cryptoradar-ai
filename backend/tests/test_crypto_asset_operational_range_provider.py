from app.ai.crypto_asset_operational_range_provider import (
    CryptoAssetOperationalRangeProvider,
)


def test_provider_builds_range_from_chart_data() -> None:
    received = {}

    def fetch_chart_data(
        asset_id: str,
        days: int,
    ):
        received["asset_id"] = asset_id
        received["days"] = days

        return {
            "prices": [
                [1, 100.0],
                [2, 103.0],
                [3, 105.0],
                [4, 102.0],
            ],
        }

    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                fetch_chart_data
            ),
        )
    )

    assessment = provider.fetch(
        asset_id="uniswap",
        current_price=101.0,
    )

    assert received == {
        "asset_id": "uniswap",
        "days": 1,
    }

    assert assessment is not None

    assert assessment.lower_limit == 100.0
    assert assessment.upper_limit == 105.0

    assert (
        assessment.is_operational_amplitude
        is True
    )


def test_provider_accepts_dictionary_points() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [
                        {
                            "timestamp": 1,
                            "price": 100.0,
                        },
                        {
                            "timestamp": 2,
                            "price": 105.0,
                        },
                    ],
                }
            ),
        )
    )

    assessment = provider.fetch(
        asset_id="uniswap",
        current_price=101.0,
    )

    assert assessment is not None

    assert assessment.lower_limit == 100.0
    assert assessment.upper_limit == 105.0


def test_provider_returns_none_without_chart_history() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [],
                }
            ),
        )
    )

    assert (
        provider.fetch(
            asset_id="uniswap",
            current_price=101.0,
        )
        is None
    )


def test_provider_rejects_empty_asset_id() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [],
                }
            ),
        )
    )

    try:
        provider.fetch(
            asset_id="   ",
            current_price=101.0,
        )

    except ValueError as error:
        assert (
            str(error)
            == "asset_id must not be empty"
        )

    else:
        raise AssertionError(
            "ValueError was not raised"
        )