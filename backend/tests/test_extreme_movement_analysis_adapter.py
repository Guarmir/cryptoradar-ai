from types import SimpleNamespace

from app.early_movement.early_movement_metrics import (
    EarlyMovementMetrics,
)
from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisAdapter,
)
from app.early_movement.scanner.scanner_analysis_result import (
    EarlyMovementScannerAnalysisResult,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


def make_result(
    coin_id: str,
    *,
    analysis_available: bool = True,
    recent_return: float = 8.0,
    acceleration: float = 4.0,
):
    asset = EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id.upper(),
        name=coin_id,
        current_price=1.0,
        total_volume=1_000_000.0,
        market_cap=10_000_000.0,
        price_change_percentage_24h=20.0,
    )

    candidate = EarlyMovementScannerCandidate(
        asset=asset,
        liquidity=SimpleNamespace(score=80.0),
    )

    analysis = None

    if analysis_available:
        analysis = SimpleNamespace(
            metrics=EarlyMovementMetrics(
                recent_price_return=recent_return,
                price_acceleration=acceleration,
                abnormal_volume_ratio=2.0,
                volatility_expansion=2.0,
                persistence_score=70.0,
            )
        )

    return EarlyMovementScannerAnalysisResult(
        candidate=candidate,
        analysis=analysis,
        chart_available=analysis_available,
    )


def test_adapts_existing_analysis():
    adapter = ExtremeMovementAnalysisAdapter()

    entries = adapter.adapt([
        make_result("irys"),
    ])

    assert len(entries) == 1
    assert entries[0].coin_id == "irys"
    assert entries[0].assessment.state == (
        "extreme_acceleration"
    )


def test_skips_unavailable_analysis():
    adapter = ExtremeMovementAnalysisAdapter()

    entries = adapter.adapt([
        make_result(
            "unavailable",
            analysis_available=False,
        ),
    ])

    assert entries == ()


def test_preserves_multiple_assets():
    adapter = ExtremeMovementAnalysisAdapter()

    entries = adapter.adapt([
        make_result("coin-a"),
        make_result(
            "coin-b",
            recent_return=-8.0,
            acceleration=-4.0,
        ),
    ])

    assert len(entries) == 2
    assert entries[0].coin_id == "coin-a"
    assert entries[1].coin_id == "coin-b"
    assert entries[1].assessment.direction == "down"


def test_detects_possible_reversal():
    adapter = ExtremeMovementAnalysisAdapter()

    entries = adapter.adapt([
        make_result(
            "irys",
            recent_return=8.0,
            acceleration=-5.0,
        ),
    ])

    assert entries[0].assessment.state == (
        "possible_reversal"
    )


def test_handles_empty_results():
    adapter = ExtremeMovementAnalysisAdapter()

    assert adapter.adapt([]) == ()