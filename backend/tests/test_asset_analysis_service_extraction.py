import app.main as main
from app.services import (
    asset_analysis_service,
)


def test_main_uses_extracted_asset_analysis_service() -> None:
    assert (
        main.calculate_ai_score
        is asset_analysis_service.calculate_ai_score
    )

    assert (
        main.get_ai_signal
        is asset_analysis_service.get_ai_signal
    )

    assert (
        main.get_ai_confidence
        is asset_analysis_service.get_ai_confidence
    )

    assert (
        main.generate_ai_analysis
        is asset_analysis_service.generate_ai_analysis
    )

    assert (
        main.calculate_score_from_market
        is asset_analysis_service.calculate_score_from_market
    )

    assert (
        main.build_empty_asset_response
        is asset_analysis_service.build_empty_asset_response
    )