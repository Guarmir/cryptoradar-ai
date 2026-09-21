from app.services import (
    asset_analysis_service,
)
from app.services.routes import (
    asset_router,
)


def test_asset_router_uses_extracted_asset_analysis_service() -> None:
    assert (
        asset_router.calculate_ai_score
        is asset_analysis_service.calculate_ai_score
    )

    assert (
        asset_router.get_ai_signal
        is asset_analysis_service.get_ai_signal
    )

    assert (
        asset_router.get_ai_confidence
        is asset_analysis_service.get_ai_confidence
    )

    assert (
        asset_router.generate_ai_analysis
        is asset_analysis_service.generate_ai_analysis
    )

    assert (
        asset_router.calculate_score_from_market
        is asset_analysis_service.calculate_score_from_market
    )

    assert (
        asset_router.build_empty_asset_response
        is asset_analysis_service.build_empty_asset_response
    )