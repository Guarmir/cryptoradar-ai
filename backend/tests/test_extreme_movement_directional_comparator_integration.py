from datetime import datetime, timedelta, timezone

from app.early_movement.extreme_movement.extreme_movement_candidate_comparator import (
    ExtremeMovementCandidateComparator,
)
from app.early_movement.scanner.scanner_market_asset import (
    EarlyMovementScannerMarketAsset,
)


def _asset(price: float, *, coin_id: str = "test-coin", change_24h: float = 4.0):
    return EarlyMovementScannerMarketAsset(
        coin_id=coin_id,
        symbol="TST",
        name="Test Coin",
        current_price=price,
        total_volume=200_000.0,
        price_change_percentage_24h=change_24h,
    )


def test_acompanha_direcao_sem_alterar_selecao_original():
    comparator = ExtremeMovementCandidateComparator()
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    prices = [100.0, 101.0, 102.0, 101.0, 100.0]
    expected_states = [
        "insufficient_data",
        "detected",
        "sustained",
        "opposite_detected",
        "opposite_sustained",
    ]
    for i, (price, expected) in enumerate(zip(prices, expected_states)):
        result = comparator.compare(
            [_asset(price)],
            observed_at=start + timedelta(minutes=i * 5),
        )
        assert result.current_coin_ids == ("test-coin",)
        assert result.experimental_coin_ids == ()
        assert result.experimental_priorities == ()
        assert len(result.directional_continuities) == 1
        reading = result.directional_continuities[0]
        assert reading.state == expected
        assert reading.coin_id == "test-coin"
    assert reading.direction == "down"
    assert reading.previous_direction == "up"


def test_continuidade_sem_passar_filtro_de_selecao():
    comparator = ExtremeMovementCandidateComparator()
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    first = comparator.compare(
        [_asset(100.0, change_24h=1.0)], observed_at=start
    )
    second = comparator.compare(
        [_asset(101.0, change_24h=1.0)],
        observed_at=start + timedelta(minutes=5),
    )
    assert first.current_coin_ids == ()
    assert second.current_coin_ids == ()
    assert second.directional_continuities[0].state == "detected"


def test_historicos_de_moedas_diferentes_ficam_isolados():
    comparator = ExtremeMovementCandidateComparator()
    start = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    comparator.compare(
        [_asset(100.0), _asset(200.0, coin_id="other-coin")],
        observed_at=start,
    )
    result = comparator.compare(
        [_asset(101.0), _asset(198.0, coin_id="other-coin")],
        observed_at=start + timedelta(minutes=5),
    )
    by_id = {item.coin_id: item for item in result.directional_continuities}
    assert by_id["test-coin"].direction == "up"
    assert by_id["other-coin"].direction == "down"


def test_limite_de_selecao_nao_limita_diagnostico_direcional():
    comparator = ExtremeMovementCandidateComparator()
    result = comparator.compare(
        [_asset(100.0), _asset(200.0, coin_id="other-coin")],
        limit=1,
        observed_at=datetime(2026, 11, 14, tzinfo=timezone.utc),
    )
    assert len(result.current_coin_ids) == 1
    assert len(result.directional_continuities) == 2
