import app.main as main
from app.services import (
    market_data_service,
)
from app.services.routes import (
    asset_router,
)


def test_routes_use_extracted_market_data_service() -> None:
    assert (
        main.resolve_coin_id
        is market_data_service.resolve_coin_id
    )

    assert (
        asset_router.resolve_coin_id
        is market_data_service.resolve_coin_id
    )

    assert (
        asset_router.get_market_data
        is market_data_service.get_market_data
    )

    assert (
        asset_router.get_chart_data
        is market_data_service.get_chart_data
    )

    assert (
        asset_router.safe_float
        is market_data_service.safe_float
    )