from app.ai.crypto_asset_operational_range_provider import (
    CryptoAssetOperationalRangeProvider,
)


def test_provider_builds_recurrence_from_chart() -> None:
    provider = (
        CryptoAssetOperationalRangeProvider(
            fetch_chart_data=(
                lambda asset_id, days: {
                    "prices": [
                        [1, 100.0],
                        [2, 100.5],
                        [3, 102.5],
                        [4, 104.5],
                        [5, 105.0],
                        [6, 102.5],
                        [7, 100.4],
                        [8, 102.5],
                        [9, 104.2],
                    ],
                }
            ),
        )
    )

    recurrence = (
        provider.fetch_recurrence(
            asset_id="uniswap",
            current_price=102.5,
        )
    )

    assert recurrence is not None

    assert (
        recurrence.lower_limit_touches
        == 2
    )

    assert (
        recurrence.upper_limit_touches
        == 2
    )

    assert (
        recurrence.completed_oscillations
        == 2
    )

    assert (
        recurrence.state
        == "recurring_range"
    )