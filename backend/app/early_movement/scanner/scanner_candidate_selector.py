from typing import Iterable

from app.early_movement.liquidity import (
    EarlyMovementLiquidityEvaluator,
)
from app.early_movement.scanner.scanner_candidate import (
    EarlyMovementScannerCandidate,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


class EarlyMovementScannerCandidateSelector:
    DEFAULT_MINIMUM_LIQUIDITY_SCORE = 50.0
    DEFAULT_CANDIDATE_LIMIT = 20

    def __init__(
        self,
        *,
        liquidity_evaluator: (
            EarlyMovementLiquidityEvaluator
            | None
        ) = None,
        minimum_liquidity_score: float = (
            DEFAULT_MINIMUM_LIQUIDITY_SCORE
        ),
    ) -> None:
        if not (
            0.0
            <= minimum_liquidity_score
            <= 100.0
        ):
            raise ValueError(
                "O score mínimo de liquidez deve "
                "ficar entre 0 e 100."
            )

        self._liquidity_evaluator = (
            liquidity_evaluator
            or EarlyMovementLiquidityEvaluator()
        )

        self._minimum_liquidity_score = (
            minimum_liquidity_score
        )

    def select(
        self,
        assets: Iterable[
            EarlyMovementScannerMarketAsset
        ],
        *,
        limit: int = DEFAULT_CANDIDATE_LIMIT,
    ) -> tuple[
        EarlyMovementScannerCandidate,
        ...,
    ]:
        if limit < 1:
            raise ValueError(
                "O limite de candidatos deve ser "
                "maior que zero."
            )

        candidates: list[
            EarlyMovementScannerCandidate
        ] = []

        for asset in assets:
            liquidity = (
                self._liquidity_evaluator.evaluate(
                    {
                        "total_volume": (
                            asset.total_volume
                        ),
                        "market_cap": (
                            asset.market_cap
                        ),
                    }
                )
            )

            if not liquidity.available:
                continue

            if liquidity.score is None:
                continue

            if (
                liquidity.score
                < self._minimum_liquidity_score
            ):
                continue

            candidates.append(
                EarlyMovementScannerCandidate(
                    asset=asset,
                    liquidity=liquidity,
                )
            )

        candidates.sort(
            key=self._sort_key,
        )

        return tuple(
            candidates[:limit]
        )

    @staticmethod
    def _sort_key(
        candidate: EarlyMovementScannerCandidate,
    ) -> tuple[
        float,
        float,
        int,
        str,
    ]:
        liquidity_score = (
            candidate.liquidity.score
            or 0.0
        )

        change_24h = (
            candidate
            .asset
            .price_change_percentage_24h
        )

        movement_activity = abs(
            change_24h
            if change_24h is not None
            else 0.0
        )

        market_cap_rank = (
            candidate.asset.market_cap_rank
            if (
                candidate.asset.market_cap_rank
                is not None
            )
            else 1_000_000
        )

        return (
            -liquidity_score,
            -movement_activity,
            market_cap_rank,
            candidate.coin_id,
        )