from typing import Optional

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.early_movement.scanner import (
    EarlyMovementScanner,
)

from app.early_movement.scanner.scanner_runtime_status import (
    build_early_movement_scanner_runtime_status,
)

from app.early_movement.scanner.scanner_confirmation_serializer import (
    EarlyMovementScannerConfirmationSerializer,
)


def create_early_movement_scanner_router(
    *,
    scanner: Optional[
        EarlyMovementScanner
    ] = None,
) -> APIRouter:
    router = APIRouter(
        tags=[
            "early-movement",
        ],
    )

    scanner_instance = (
        scanner
        or EarlyMovementScanner(
            candidate_limit=10,
            result_limit=5,
        )
    )

    confirmation_serializer = (
        EarlyMovementScannerConfirmationSerializer()
    )

    @router.get(
        "/early-movement/scan",
    )
    def scan_early_movement():
        try:
            result = (
                scanner_instance.scan()
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Scanner de mercado "
                    "temporariamente indisponível."
                ),
            ) from exc

        signals = []

        analysis_failures = []

        for analysis_result in (
            result.analysis_results
        ):
            if analysis_result.error is None:
                continue

            candidate = (
                analysis_result.candidate
            )

            analysis_failures.append(
                {
                    "coin_id": (
                        candidate.coin_id
                    ),
                    "symbol": (
                        candidate.symbol
                    ),
                    "name": (
                        candidate.name
                    ),
                    "chart_available": (
                        analysis_result
                        .chart_available
                    ),
                    "error": (
                        analysis_result.error
                    ),
                }
            )

        for ranked in (
            result.ranked_results
        ):
            analysis_result = (
                ranked.result
            )

            analysis = (
                analysis_result.analysis
            )

            if analysis is None:
                continue

            candidate = (
                analysis_result.candidate
            )

            asset = (
                candidate.asset
            )

            evidence = (
                analysis.evidence
            )

            breakout_confirmation = (
                analysis
                .breakout_confirmation
            )

            signals.append(
                {
                    "rank": ranked.rank,
                    "relevance_score": (
                        ranked.relevance_score
                    ),
                    "coin_id": (
                        asset.coin_id
                    ),
                    "symbol": (
                        asset.symbol
                    ),
                    "name": (
                        asset.name
                    ),
                    "state": (
                        evidence.state.value
                    ),
                    "confirmation": (
                        confirmation_serializer.serialize(
                            evidence,
                        )
                    ),
                    "current_price": (
                        asset.current_price
                    ),
                    "change_24h": (
                        asset
                        .price_change_percentage_24h
                    ),
                    "market_cap": (
                        asset.market_cap
                    ),
                    "total_volume": (
                        asset.total_volume
                    ),
                    "market_cap_rank": (
                        asset.market_cap_rank
                    ),
                    "liquidity_score": (
                        evidence
                        .liquidity_score
                    ),
                    "price_acceleration": (
                        evidence
                        .price_acceleration
                    ),
                    "abnormal_volume_ratio": (
                        evidence
                        .abnormal_volume_ratio
                    ),
                    "volatility_expansion": (
                        evidence
                        .volatility_expansion
                    ),
                    "persistence_score": (
                        evidence
                        .persistence_score
                    ),
                    "support_break": (
                        evidence
                        .support_break
                    ),
                    "resistance_break": (
                        evidence
                        .resistance_break
                    ),
                    "retest_confirmed": (
                        evidence
                        .retest_confirmed
                    ),
                    "false_breakout_risk": (
                        evidence
                        .false_breakout_risk
                    ),
                    "breakout_direction": (
                        breakout_confirmation
                        .breakout_direction
                    ),
                    "reason": (
                        evidence.reason
                    ),
                    "invalidation_reason": (
                        evidence
                        .invalidation_reason
                    ),
                }
            )

        return {
            "status": "ok",
            "universe_size": (
                result.universe_size
            ),
            "candidate_count": (
                result.candidate_count
            ),
            "analyzed_count": (
                result.analyzed_count
            ),
            "successful_analysis_count": (
                result
                .successful_analysis_count
            ),
            "analysis_failure_count": len(
                analysis_failures,
            ),
            "analysis_failures": (
                analysis_failures
            ),
            "signal_count": len(
                signals,
            ),
            "signals": signals,
        }
    @router.get(
        "/early-movement/status",
    )
    def early_movement_status(
        request: Request,
    ):
        runtime = getattr(
            request.app.state,
            "early_movement_scanner_runtime",
            None,
        )

        return (
            build_early_movement_scanner_runtime_status(
                runtime,
            )
        )

    return router