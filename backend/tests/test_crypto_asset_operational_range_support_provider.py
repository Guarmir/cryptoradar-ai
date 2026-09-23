import pytest

from app.ai.crypto_asset_operational_range_provider import (
    CryptoAssetOperationalRangeProvider,
)


def test_calculates_historical_average_volume() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [
                        [1, 100],
                        [2, 105],
                    ],
                    "total_volumes": [
                        [1, 800_000_000],
                        [2, 1_000_000_000],
                        [3, 1_200_000_000],
                    ],
                }
            ),
        )
    )

    average = (
        provider
        .fetch_historical_average_volume(
            asset_id="uniswap",
        )
    )

    assert average == pytest.approx(
        1_000_000_000
    )


def test_returns_none_without_volume_history() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [
                        [1, 100],
                        [2, 105],
                    ],
                }
            ),
        )
    )

    assert (
        provider
        .fetch_historical_average_volume(
            asset_id="uniswap",
        )
        is None
    )