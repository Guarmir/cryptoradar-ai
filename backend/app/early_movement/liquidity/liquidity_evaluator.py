import math
from typing import Any, Mapping, Optional

from app.early_movement.liquidity.liquidity_assessment import (
    EarlyMovementLiquidityAssessment,
)


class EarlyMovementLiquidityEvaluator:
    def evaluate(
        self,
        market_data: Mapping[str, Any],
    ) -> EarlyMovementLiquidityAssessment:
        total_volume = self._positive_float(
            market_data.get("total_volume"),
        )

        market_cap = self._positive_float(
            market_data.get("market_cap"),
        )

        if total_volume is None:
            return EarlyMovementLiquidityAssessment(
                market_cap=market_cap,
                factors=(
                    "Trading volume is unavailable.",
                ),
            )

        factors: list[str] = []

        score = self._volume_score(
            total_volume,
            factors,
        )

        ratio = None

        if market_cap is not None:
            ratio = total_volume / market_cap

            score += self._turnover_score(
                ratio,
                factors,
            )
        else:
            factors.append(
                "Market-cap context is unavailable."
            )

        return EarlyMovementLiquidityAssessment(
            score=self._clamp(score),
            total_volume=total_volume,
            market_cap=market_cap,
            volume_to_market_cap_ratio=ratio,
            available=True,
            factors=tuple(factors),
        )

    @staticmethod
    def _volume_score(
        total_volume: float,
        factors: list[str],
    ) -> float:
        if total_volume >= 1_000_000_000:
            factors.append(
                "Very high absolute trading volume."
            )
            return 60.0

        if total_volume >= 250_000_000:
            factors.append(
                "High absolute trading volume."
            )
            return 52.0

        if total_volume >= 100_000_000:
            factors.append(
                "Strong absolute trading volume."
            )
            return 44.0

        if total_volume >= 50_000_000:
            factors.append(
                "Moderate absolute trading volume."
            )
            return 36.0

        if total_volume >= 10_000_000:
            factors.append(
                "Usable but limited absolute trading volume."
            )
            return 25.0

        if total_volume >= 1_000_000:
            factors.append(
                "Low absolute trading volume."
            )
            return 12.0

        factors.append(
            "Very low absolute trading volume."
        )
        return 4.0

    @staticmethod
    def _turnover_score(
        ratio: float,
        factors: list[str],
    ) -> float:
        if ratio >= 0.20:
            factors.append(
                "Very strong volume-to-market-cap turnover."
            )
            return 40.0

        if ratio >= 0.10:
            factors.append(
                "Strong volume-to-market-cap turnover."
            )
            return 34.0

        if ratio >= 0.05:
            factors.append(
                "Healthy volume-to-market-cap turnover."
            )
            return 28.0

        if ratio >= 0.02:
            factors.append(
                "Moderate volume-to-market-cap turnover."
            )
            return 20.0

        if ratio >= 0.01:
            factors.append(
                "Limited volume-to-market-cap turnover."
            )
            return 12.0

        factors.append(
            "Weak volume-to-market-cap turnover."
        )
        return 6.0

    @staticmethod
    def _positive_float(
        value: Any,
    ) -> Optional[float]:
        if isinstance(value, bool):
            return None

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(parsed):
            return None

        if parsed <= 0:
            return None

        return parsed

    @staticmethod
    def _clamp(
        value: float,
    ) -> float:
        return max(
            0.0,
            min(100.0, value),
        )