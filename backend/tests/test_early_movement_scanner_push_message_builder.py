
from types import SimpleNamespace

import pytest

from app.early_movement.early_movement_state import (
    EarlyMovementState,
)
from app.early_movement.scanner.scanner_push_message_builder import (
    EarlyMovementScannerPushMessageBuilder,
)


def make_result(
    state: EarlyMovementState,
    *,
    support_break: bool = False,
    resistance_break: bool = False,
):
    evidence = SimpleNamespace(
        support_break=support_break,
        resistance_break=resistance_break,
    )

    return SimpleNamespace(
        state=state,
        symbol="uni",
        name="Uniswap",
        coin_id="uniswap",
        rank=1,
        relevance_score=65.0,
        result=SimpleNamespace(
            analysis=SimpleNamespace(
                evidence=evidence,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("state", "expected_text"),
    [
        (
            EarlyMovementState.OBSERVATION,
            "Observacao antecipada",
        ),
        (
            EarlyMovementState.EARLY_MOVEMENT,
            "Movimento inicial identificado",
        ),
        (
            EarlyMovementState.CONFIRMED_MOVEMENT,
            "Movimento com confirmacoes adicionais",
        ),
    ],
)
def test_push_message_identifies_movement_state(
    state,
    expected_text,
) -> None:
    message = EarlyMovementScannerPushMessageBuilder().build(
        make_result(state)
    )

    assert expected_text in message.body
    assert message.data["state"] == state.value
    assert message.data["type"] == "early_movement"


def test_push_message_identifies_support_break() -> None:
    message = EarlyMovementScannerPushMessageBuilder().build(
        make_result(
            EarlyMovementState.OBSERVATION,
            support_break=True,
        )
    )

    assert "Rompimento de suporte" in message.body


def test_push_message_identifies_resistance_break() -> None:
    message = EarlyMovementScannerPushMessageBuilder().build(
        make_result(
            EarlyMovementState.EARLY_MOVEMENT,
            resistance_break=True,
        )
    )

    assert "Rompimento de resistencia" in message.body


def test_push_message_preserves_notification_metadata() -> None:
    message = EarlyMovementScannerPushMessageBuilder().build(
        make_result(EarlyMovementState.OBSERVATION)
    )

    assert message.title == "CryptoRadar: UNI"
    assert message.data["coin_id"] == "uniswap"
    assert message.data["symbol"] == "uni"
    assert message.data["rank"] == "1"
    assert message.data["relevance_score"] == "65.0"
