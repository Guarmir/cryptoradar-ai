from dataclasses import dataclass
from typing import Optional


@dataclass(
    frozen=True,
)
class AssetOperationalScenarioAssessment:
    state: str
    strength: str
    directional_score: int
    supporting_factors: tuple[str, ...]
    warning_factors: tuple[str, ...]


def calculate_asset_operational_scenario(
    *,
    score: float,
    change_24h_percent: float,
    risk_score: float,
    range_quality_state: Optional[str] = None,
    range_invalidation_state: Optional[str] = None,
    market_context_state: Optional[str] = None,
    relative_strength_state: Optional[str] = None,
) -> AssetOperationalScenarioAssessment:
    _validate_percent_score(
        name="score",
        value=score,
    )

    _validate_percent_score(
        name="risk_score",
        value=risk_score,
    )

    directional_score = 0

    positive_evidence = False
    negative_evidence = False

    supporting_factors: list[str] = []
    warning_factors: list[str] = []

    score_direction = _score_direction(
        score
    )

    directional_score += score_direction

    if score_direction > 0:
        positive_evidence = True
        supporting_factors.append(
            "score_supports_upside"
        )

    elif score_direction < 0:
        negative_evidence = True
        supporting_factors.append(
            "score_supports_downside"
        )

    change_direction = _change_direction(
        change_24h_percent
    )

    directional_score += change_direction

    if change_direction > 0:
        positive_evidence = True
        supporting_factors.append(
            "price_change_supports_upside"
        )

    elif change_direction < 0:
        negative_evidence = True
        supporting_factors.append(
            "price_change_supports_downside"
        )

    market_direction = (
        _market_context_direction(
            market_context_state
        )
    )

    directional_score += market_direction

    if market_direction > 0:
        positive_evidence = True
        supporting_factors.append(
            "market_context_favorable"
        )

    elif market_direction < 0:
        negative_evidence = True
        warning_factors.append(
            "market_context_unfavorable"
        )

    relative_direction = (
        _relative_strength_direction(
            relative_strength_state
        )
    )

    directional_score += relative_direction

    if relative_direction > 0:
        positive_evidence = True
        supporting_factors.append(
            "outperforming_btc"
        )

    elif relative_direction < 0:
        negative_evidence = True
        warning_factors.append(
            "underperforming_btc"
        )

    state = _resolve_state(
        directional_score=directional_score,
        positive_evidence=positive_evidence,
        negative_evidence=negative_evidence,
    )

    strength_score = (
        _base_strength_score(
            state=state,
            directional_score=(
                directional_score
            ),
        )
    )

    strength_score += (
        _market_alignment_strength(
            state=state,
            market_context_state=(
                market_context_state
            ),
        )
    )

    strength_score += (
        _relative_alignment_strength(
            state=state,
            relative_strength_state=(
                relative_strength_state
            ),
        )
    )

    quality_adjustment = (
        _range_quality_adjustment(
            range_quality_state
        )
    )

    strength_score += quality_adjustment

    if range_quality_state == "strong":
        supporting_factors.append(
            "range_quality_strong"
        )

    elif range_quality_state in {
        "under_observation",
        "weak",
    }:
        warning_factors.append(
            "range_quality_weak"
        )

    invalidation_adjustment = (
        _range_invalidation_adjustment(
            range_invalidation_state
        )
    )

    strength_score += (
        invalidation_adjustment
    )

    if range_invalidation_state == "low":
        supporting_factors.append(
            "range_invalidation_low"
        )

    elif range_invalidation_state == "high":
        warning_factors.append(
            "range_invalidation_high"
        )

    elif (
        range_invalidation_state
        == "invalidated"
    ):
        warning_factors.append(
            "range_invalidated"
        )

    risk_adjustment = (
        _risk_adjustment(
            risk_score
        )
    )

    strength_score += risk_adjustment

    if risk_score <= 35:
        supporting_factors.append(
            "observed_risk_low"
        )

    elif risk_score >= 70:
        warning_factors.append(
            "observed_risk_high"
        )

    elif risk_score >= 55:
        warning_factors.append(
            "observed_risk_elevated"
        )

    strength = _resolve_strength(
        state=state,
        strength_score=strength_score,
    )

    return AssetOperationalScenarioAssessment(
        state=state,
        strength=strength,
        directional_score=(
            directional_score
        ),
        supporting_factors=tuple(
            supporting_factors
        ),
        warning_factors=tuple(
            warning_factors
        ),
    )


def _score_direction(
    score: float,
) -> int:
    if score >= 70:
        return 2

    if score >= 60:
        return 1

    if score <= 30:
        return -2

    if score <= 40:
        return -1

    return 0


def _change_direction(
    change_24h_percent: float,
) -> int:
    if change_24h_percent >= 2.0:
        return 2

    if change_24h_percent >= 0.5:
        return 1

    if change_24h_percent <= -2.0:
        return -2

    if change_24h_percent <= -0.5:
        return -1

    return 0


def _market_context_direction(
    state: Optional[str],
) -> int:
    if state == "favorable":
        return 1

    if state == "unfavorable":
        return -1

    return 0


def _relative_strength_direction(
    state: Optional[str],
) -> int:
    if state == "outperforming":
        return 1

    if state == "underperforming":
        return -1

    return 0


def _resolve_state(
    *,
    directional_score: int,
    positive_evidence: bool,
    negative_evidence: bool,
) -> str:
    if directional_score >= 3:
        return "bullish"

    if directional_score <= -3:
        return "bearish"

    if (
        positive_evidence
        and negative_evidence
    ):
        return "conflicted"

    return "neutral"


def _base_strength_score(
    *,
    state: str,
    directional_score: int,
) -> int:
    if state in {
        "neutral",
        "conflicted",
    }:
        return 0

    absolute_score = abs(
        directional_score
    )

    if absolute_score >= 5:
        return 2

    if absolute_score >= 3:
        return 1

    return 0


def _market_alignment_strength(
    *,
    state: str,
    market_context_state: Optional[str],
) -> int:
    if (
        state == "bullish"
        and market_context_state
        == "favorable"
    ):
        return 1

    if (
        state == "bearish"
        and market_context_state
        == "unfavorable"
    ):
        return 1

    if (
        state == "bullish"
        and market_context_state
        == "unfavorable"
    ):
        return -1

    if (
        state == "bearish"
        and market_context_state
        == "favorable"
    ):
        return -1

    return 0


def _relative_alignment_strength(
    *,
    state: str,
    relative_strength_state: Optional[str],
) -> int:
    if (
        state == "bullish"
        and relative_strength_state
        == "outperforming"
    ):
        return 1

    if (
        state == "bearish"
        and relative_strength_state
        == "underperforming"
    ):
        return 1

    if (
        state == "bullish"
        and relative_strength_state
        == "underperforming"
    ):
        return -1

    if (
        state == "bearish"
        and relative_strength_state
        == "outperforming"
    ):
        return -1

    return 0


def _range_quality_adjustment(
    state: Optional[str],
) -> int:
    if state == "strong":
        return 1

    if state == "weak":
        return -2

    if state == "under_observation":
        return -1

    return 0


def _range_invalidation_adjustment(
    state: Optional[str],
) -> int:
    if state == "low":
        return 1

    if state == "high":
        return -1

    if state == "invalidated":
        return -3

    return 0


def _risk_adjustment(
    risk_score: float,
) -> int:
    if risk_score <= 35:
        return 1

    if risk_score >= 70:
        return -2

    if risk_score >= 55:
        return -1

    return 0


def _resolve_strength(
    *,
    state: str,
    strength_score: int,
) -> str:
    if state in {
        "neutral",
        "conflicted",
    }:
        return "weak"

    if strength_score >= 4:
        return "strong"

    if strength_score >= 1:
        return "moderate"

    return "weak"


def _validate_percent_score(
    *,
    name: str,
    value: float,
) -> None:
    if value < 0 or value > 100:
        raise ValueError(
            f"{name} must be between "
            "0 and 100"
        )