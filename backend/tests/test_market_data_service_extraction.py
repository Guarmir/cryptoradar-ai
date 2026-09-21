import app.main as main
from app.services import (
    market_data_service,
)


def test_main_uses_extracted_market_data_service() -> None:
    assert (
        main.resolve_coin_id
        is market_data_service.resolve_coin_id
    )

    assert (
        main.get_market_data
        is market_data_service.get_market_data
    )

    assert (
        main.get_chart_data
        is market_data_service.get_chart_data
    )

    assert (
        main.safe_float
        is market_data_service.safe_float
    )