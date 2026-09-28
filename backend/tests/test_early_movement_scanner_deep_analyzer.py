import pytest

from app.early_movement.liquidity import (
    EarlyMovementLiquidityAssessment,
)
from app.early_movement.scanner import (
    EarlyMovementScannerCandidate,
    EarlyMovementScannerDeepAnalyzer,
    EarlyMovementScannerMarketAsset,
)


def _candidate(
    coin_id: str,
    *,
    liquidity_score: float = 86.0,
) -> EarlyMovementScannerCandidate:
    asset = EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol=coin_id[:3],
        name=coin_id.title(),
        current_price=10.0,
        total_volume=500_000_000,
        market_cap=5_000_000_000,
        price_change_percentage_24h=3.0,
        market_cap_rank=20,
    )

    liquidity = (
        EarlyMovementLiquidityAssessment(
            score=liquidity_score,
            total_volume=500_000_000,
            market_cap=5_000_000_000,
            volume_to_market_cap_ratio=0.10,
            available=True,
        )
    )

    return EarlyMovementScannerCandidate(
        asset=asset,
        liquidity=liquidity,
    )


class FakeAnalyzer:
    def __init__(
        self,
    ) -> None:
        self.calls = []
        self.result = object()

    def analyze(
        self,
        chart_data,
        *,
        liquidity_score=None,
    ):
        self.calls.append(
            (
                chart_data,
                liquidity_score,
            )
        )

        return self.result


def test_deep_analyzer_uses_canonical_coin_id_and_liquidity() -> None:
    captured = []

    chart_data = {
        "prices": [
            [1, 10.0],
            [2, 10.5],
        ],
        "total_volumes": [
            [1, 100.0],
            [2, 150.0],
        ],
    }

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        captured.append(
            (
                coin_id,
                days,
            )
        )

        return chart_data

    fake_analyzer = FakeAnalyzer()

    deep_analyzer = (
        EarlyMovementScannerDeepAnalyzer(
            analyzer=fake_analyzer,
            chart_loader=fake_loader,
        )
    )

    result = deep_analyzer.analyze_candidates(
        (
            _candidate(
                "uniswap",
                liquidity_score=86.0,
            ),
        )
    )

    assert len(result) == 1

    assert captured == [
        (
            "uniswap",
            7,
        )
    ]

    assert fake_analyzer.calls == [
        (
            chart_data,
            86.0,
        )
    ]

    assert result[0].coin_id == "uniswap"
    assert result[0].chart_available is True
    assert result[0].analysis is fake_analyzer.result
    assert result[0].error is None


def test_deep_analyzer_handles_empty_chart_safely() -> None:
    fake_analyzer = FakeAnalyzer()

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        return {
            "prices": [],
        }

    deep_analyzer = (
        EarlyMovementScannerDeepAnalyzer(
            analyzer=fake_analyzer,
            chart_loader=fake_loader,
        )
    )

    result = deep_analyzer.analyze_candidates(
        (
            _candidate(
                "bitcoin",
            ),
        )
    )

    assert len(result) == 1
    assert result[0].analysis is None
    assert result[0].chart_available is False

    assert (
        result[0].error
        == "chart_data_unavailable"
    )

    assert fake_analyzer.calls == []


def test_deep_analyzer_isolates_failure_between_assets() -> None:
    fake_analyzer = FakeAnalyzer()

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        if coin_id == "broken":
            raise RuntimeError(
                "temporary failure"
            )

        return {
            "prices": [
                [1, 10.0],
                [2, 11.0],
            ],
            "total_volumes": [
                [1, 100.0],
                [2, 200.0],
            ],
        }

    deep_analyzer = (
        EarlyMovementScannerDeepAnalyzer(
            analyzer=fake_analyzer,
            chart_loader=fake_loader,
        )
    )

    result = deep_analyzer.analyze_candidates(
        (
            _candidate(
                "broken",
            ),
            _candidate(
                "ethereum",
            ),
        )
    )

    assert len(result) == 2

    assert result[0].coin_id == "broken"
    assert result[0].analysis is None

    assert (
        result[0].error
        == "chart_load_failed"
    )

    assert result[1].coin_id == "ethereum"
    assert result[1].analysis is fake_analyzer.result
    assert result[1].chart_available is True
    assert result[1].error is None


def test_deep_analyzer_accepts_custom_chart_period() -> None:
    captured = []

    def fake_loader(
        coin_id: str,
        days: int,
    ):
        captured.append(
            days,
        )

        return {
            "prices": [
                [1, 10.0],
            ],
        }

    deep_analyzer = (
        EarlyMovementScannerDeepAnalyzer(
            analyzer=FakeAnalyzer(),
            chart_loader=fake_loader,
            chart_days=3,
        )
    )

    deep_analyzer.analyze_candidates(
        (
            _candidate(
                "solana",
            ),
        )
    )

    assert captured == [
        3,
    ]


def test_deep_analyzer_rejects_invalid_chart_period() -> None:
    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        EarlyMovementScannerDeepAnalyzer(
            chart_days=0,
        )