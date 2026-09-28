from types import SimpleNamespace

import pytest

from app.early_movement.early_movement_evidence import (
    EarlyMovementEvidence,
)
from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.liquidity import (
    EarlyMovementLiquidityAssessment,
)
from app.early_movement.scanner import (
    EarlyMovementScannerAnalysisResult,
    EarlyMovementScannerCandidate,
    EarlyMovementScannerMarketAsset,
    EarlyMovementScannerResultRanker,
)


def _candidate(
    coin_id: str,
    *,
    liquidity_score: float = 80.0,
    rank: int = 20,
) -> EarlyMovementScannerCandidate:
    asset = EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id[:3],
        name=coin_id.title(),
        current_price=10.0,
        total_volume=300_000_000,
        market_cap=3_000_000_000,
        price_change_percentage_24h=3.0,
        market_cap_rank=rank,
    )

    liquidity = (
        EarlyMovementLiquidityAssessment(
            score=liquidity_score,
            total_volume=300_000_000,
            market_cap=3_000_000_000,
            volume_to_market_cap_ratio=0.10,
            available=True,
        )
    )

    return EarlyMovementScannerCandidate(
        asset=asset,
        liquidity=liquidity,
    )


def _result(
    coin_id: str,
    *,
    state: EarlyMovementState,
    liquidity_score: float = 80.0,
    persistence_score: float = 60.0,
    abnormal_volume_ratio: float = 1.5,
    support_break: bool = False,
    resistance_break: bool = False,
    retest_confirmed: bool = False,
    false_breakout_risk: float = 20.0,
    rank: int = 20,
) -> EarlyMovementScannerAnalysisResult:
    candidate = _candidate(
        coin_id,
        liquidity_score=liquidity_score,
        rank=rank,
    )

    evidence = EarlyMovementEvidence(
        state=state,
        liquidity_score=liquidity_score,
        persistence_score=persistence_score,
        abnormal_volume_ratio=(
            abnormal_volume_ratio
        ),
        support_break=support_break,
        resistance_break=resistance_break,
        retest_confirmed=retest_confirmed,
        false_breakout_risk=(
            false_breakout_risk
        ),
    )

    analysis = SimpleNamespace(
        evidence=evidence,
    )

    return EarlyMovementScannerAnalysisResult(
        candidate=candidate,
        analysis=analysis,
        chart_available=True,
    )


def test_ranker_prioritizes_early_movement_over_observation() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    result = ranker.rank(
        (
            _result(
                "observation",
                state=(
                    EarlyMovementState.OBSERVATION
                ),
            ),
            _result(
                "early",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
            ),
        )
    )

    assert len(result) == 2
    assert result[0].coin_id == "early"
    assert result[1].coin_id == "observation"


def test_ranker_excludes_normal_state() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    result = ranker.rank(
        (
            _result(
                "normal",
                state=(
                    EarlyMovementState.NORMAL
                ),
            ),
            _result(
                "active",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
            ),
        )
    )

    assert len(result) == 1
    assert result[0].coin_id == "active"


def test_lower_false_breakout_risk_improves_priority() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    result = ranker.rank(
        (
            _result(
                "high-risk",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
                false_breakout_risk=90.0,
            ),
            _result(
                "low-risk",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
                false_breakout_risk=10.0,
            ),
        )
    )

    assert result[0].coin_id == "low-risk"

    assert (
        result[0].relevance_score
        > result[1].relevance_score
    )


def test_retest_and_breakout_improve_priority() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    result = ranker.rank(
        (
            _result(
                "plain",
                state=(
                    EarlyMovementState.CONFIRMED_MOVEMENT
                ),
            ),
            _result(
                "confirmed",
                state=(
                    EarlyMovementState.CONFIRMED_MOVEMENT
                ),
                resistance_break=True,
                retest_confirmed=True,
            ),
        )
    )

    assert result[0].coin_id == "confirmed"

    assert (
        result[0].relevance_score
        > result[1].relevance_score
    )


def test_ranker_skips_failed_analysis_and_respects_limit() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    failed = (
        EarlyMovementScannerAnalysisResult(
            candidate=_candidate(
                "failed",
            ),
            error="analysis_failed",
        )
    )

    result = ranker.rank(
        (
            failed,
            _result(
                "one",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
            ),
            _result(
                "two",
                state=(
                    EarlyMovementState.EARLY_MOVEMENT
                ),
                persistence_score=80.0,
            ),
            _result(
                "three",
                state=(
                    EarlyMovementState.OBSERVATION
                ),
            ),
        ),
        limit=2,
    )

    assert len(result) == 2

    assert result[0].rank == 1
    assert result[1].rank == 2

    assert (
        "failed"
        not in {
            item.coin_id
            for item in result
        }
    )


def test_ranker_rejects_invalid_limit() -> None:
    ranker = (
        EarlyMovementScannerResultRanker()
    )

    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        ranker.rank(
            (),
            limit=0,
        )